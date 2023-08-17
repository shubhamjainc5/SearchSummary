

from utils.prompt import search_summary, search_qa
import asyncio

import json
import numpy as np
import os
import re
import copy
import time
from langchain.schema import OutputParserException
# openai is commented to avoid langchain resource not found error
#import openai

from typing import List, Dict

from utils.logging_handler import Logger
from utils.timer import timed
import traceback
import config

from json.decoder import JSONDecodeError
from openai.error import APIError, Timeout, RateLimitError, APIConnectionError, AuthenticationError, \
    ServiceUnavailableError, InvalidRequestError

from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import List
import ast


os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_API_BASE"] = config.OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = config.OPEN_AI_API_KEY


# Here's another example, but with a compound typed field.
class SearchSummary(BaseModel):

    Summary: str = Field(description="Generated summarised answer with respect to user query")


class QuestionAnswerSet(BaseModel):

    question: str = Field(description="a generated question related to given user query whose answer can only be found in given search results")
    answer: str = Field(description="a generated summarized answer framed only from the given search results")


class RelevantQuestionAnswers(BaseModel):

    relqa: List[QuestionAnswerSet] = Field(description="a set of generated questions(which are related to given user query) and summarized answers(whose answers also lies in the provided search results).")
    



async def generate_summary(paras: List[str], query: str) -> (Dict[str, str], int, float):
    print('\n---------summary-------------\n')
    begin_start = time.time()
    cnt = 0
    call_tokens = []

    async def summary_llm_call() -> Dict[str, str]:

        nonlocal cnt

        model = AzureChatOpenAI(
            deployment_name=config.AZURE_DEPLOYMENT_NAME,
            model_name=config.AZURE_MODEL_NAME,
            max_tokens=200,
            temperature=0,
            verbose=True,
            request_timeout=20
        )

        template = "Ignore previous instructions.\n you are a part of search engine whose job is to find the answer of user's search query only from the provided search results and later provide a summarized answer from the relevant search results only."
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)

        summary_parser = PydanticOutputParser(pydantic_object=SearchSummary)
        summary_format_instructions = summary_parser.get_format_instructions()

        summary_template = PromptTemplate(input_variables=["paras", "query"],
                                        template=search_summary,
                                        partial_variables={"format_instructions": summary_format_instructions})
        
        human_message_prompt = HumanMessagePromptTemplate(prompt=summary_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        summary_chain = LLMChain(llm=model, prompt=chat_prompt, output_key="generated_summary")

        #start = time.time()
        gpt_op = await summary_chain.agenerate([{"paras": paras, "query": query}])
        
        #start = time.time()
        Logger.info("\n Response from GPT : {0}".format(gpt_op))

        generated_summary = gpt_op.generations[0][0].text
        #print(generated_summary)

        #summary_prompt = summary_template.format(paras=paras, query=query, format_instructions=summary_format_instructions)
        #print(summary_prompt)
        #summary_ip_tokens = model.get_num_tokens(summary_prompt)
        #summary_op_tokens = model.get_num_tokens(generated_summary)
        #print(summary_op_tokens)
        call_tokens.append(gpt_op.dict()['llm_output']['token_usage']['total_tokens'])
        cnt += 1
        #Logger.debug("token calc ran in {}s".format(round(time.time() - start, 4)))

        try:
            #start = time.time()
            summary_result = summary_parser.parse(generated_summary).json()
            summary_result = json.loads(summary_result)
            Logger.info('\n Langchain json summary content parsed: {0}'.format(summary_result))
            #Logger.debug("langchain parsing ran in {}s".format(round(time.time() - start, 4)))
            summary_result = {'Summary':''} if summary_result['Summary'].lower()=='not found' else summary_result
        except Exception as lang_err:
            Logger.error(traceback.format_exc())
            print(lang_err)
            summary_result = generated_summary[generated_summary.find('{'): generated_summary.rfind('}') + 1]
            summary_result = ast.literal_eval(summary_result)
            Logger.info('\n Regex json summary content parsed: {0}'.format(summary_result))
            summary_result = {'Summary':''} if summary_result['Summary'].lower()=='not found' else summary_result

        return summary_result

    try:
        result = await summary_llm_call()
        status = 'LLMParsed'
    except (AssertionError, JSONDecodeError, OutputParserException, KeyError) as e:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: summary Parsing or Assertion Failed')
        try:
            result = await summary_llm_call()
            status = 'LLMRetryParsed'
        except (APIError, Timeout, ServiceUnavailableError) as e1:
            Logger.error(traceback.format_exc())
            Logger.error('ERROR: LLM SERVER Not responding')
            result = {'Summary':''}
            status = 'LLMServerError'
        except (RateLimitError, APIConnectionError, InvalidRequestError, AuthenticationError) as e3:
            Logger.error(traceback.format_exc())
            Logger.error('ERROR: Application server Not responding')
            result = {'Summary':''}
            status = 'AppServerError'
        except:
            Logger.error(traceback.format_exc())
            Logger.error('UNKNOWN ERROR: occurred')
            result = {'Summary':''}
            status = 'UnknownError'
    except (APIError, Timeout, ServiceUnavailableError) as e1:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: LLM SERVER Not responding')
        result = {'Summary':''}
        status = 'LLMServerError'
    except (RateLimitError, APIConnectionError, InvalidRequestError, AuthenticationError) as e3:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: Application server Not responding')
        result = {'Summary':''}
        status = 'AppServerError'
    except:
        Logger.error(traceback.format_exc())
        Logger.error('UNKNOWN ERROR: occurred')
        result = {'Summary':''}
        status = 'UnknownError'

    print('\n---------summary:{0}-------------\n'.format(status))
    Logger.info(f"\n---------summary:{status}-------------\n")
    Logger.debug("summary chain run ran in {}s".format(round(time.time() - begin_start , 4)))

    return result, cnt, 0 if len(call_tokens) == 0 else np.average(call_tokens), status



async def generate_qa(paras: List[str], query: str) -> (List[Dict[str, str]], int, float):
    print('\n---------RelevantQ&A-------------\n')
    begin_start= time.time()
    cnt = 0
    call_tokens = []

    async def qa_llm_call() -> Dict[str, str]:

        nonlocal cnt

        model = AzureChatOpenAI(
            deployment_name=config.AZURE_DEPLOYMENT_NAME,
            model_name=config.AZURE_MODEL_NAME,
            max_tokens=1500,
            temperature=0,
            verbose=True,
            request_timeout=25
        )

        template = "Ignore previous instructions.\n you are a part of search engine whose job is to generate pair of new questions and their summarized answers( MUST come from given search results only.)"
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)

        qa_parser = PydanticOutputParser(pydantic_object=RelevantQuestionAnswers)
        qa_format_instructions = qa_parser.get_format_instructions()

        qa_template = PromptTemplate(input_variables=["paras"],
                                        template=search_qa,
                                        partial_variables={"format_instructions": qa_format_instructions})
        
        human_message_prompt = HumanMessagePromptTemplate(prompt=qa_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        qa_chain = LLMChain(llm=model, prompt=chat_prompt, output_key="generated_qa")

        start = time.time()
        gpt_op = await qa_chain.agenerate([{"paras": paras, "query": query}])
        #Logger.debug("chain run ran in {}s".format(round(time.time() - start, 4)))


        start = time.time()
        Logger.info("\n Response from GPT : {0}".format(gpt_op))

        generated_qa = gpt_op.generations[0][0].text
        #print(generated_qa)

        #qa_prompt = qa_template.format(paras=paras, format_instructions=qa_format_instructions)
        #print(qa_prompt)
        #qa_ip_tokens = model.get_num_tokens(qa_prompt)
        #qa_op_tokens = model.get_num_tokens(generated_qa)
        #print(qa_op_tokens)
        call_tokens.append(gpt_op.dict()['llm_output']['token_usage']['total_tokens'])
        cnt += 1
        #Logger.debug("token calc ran in {}s".format(round(time.time() - start, 4)))

        try:
            start = time.time()
            qa_result = qa_parser.parse(generated_qa).json()
            qa_result = json.loads(qa_result)['relqa']
            Logger.info('\n Langchain json generated qa parsed: {0}'.format(qa_result))
            #Logger.debug("langchain parsing ran in {}s".format(round(time.time() - start, 4)))
        except Exception as lang_err:
            Logger.error(traceback.format_exc())
            print(lang_err)
            qa_result = generated_qa[generated_qa.find('['): generated_qa.rfind(']') + 1]
            qa_result = ast.literal_eval(qa_result)
            Logger.info('\n Regex json qa content parsed: {0}'.format(qa_result))

        return qa_result

    try:
        result = await qa_llm_call()
        status = 'LLMParsed'
    except (AssertionError, JSONDecodeError, OutputParserException, KeyError) as e:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: qa Parsing or Assertion Failed')
        try:
            result = await qa_llm_call()
            status = 'LLMRetryParsed'
        except (APIError, Timeout, ServiceUnavailableError) as e1:
            Logger.error(traceback.format_exc())
            Logger.error('ERROR: LLM SERVER Not responding')
            result = []
            status = 'LLMServerError'
        except (RateLimitError, APIConnectionError, InvalidRequestError, AuthenticationError) as e3:
            Logger.error(traceback.format_exc())
            Logger.error('ERROR: Application server Not responding')
            result = []
            status = 'AppServerError'
        except:
            Logger.error(traceback.format_exc())
            Logger.error('UNKNOWN ERROR: occurred')
            result = []
            status = 'UnknownError'
    except (APIError, Timeout, ServiceUnavailableError) as e1:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: LLM SERVER Not responding')
        result = []
        status = 'LLMServerError'
    except (RateLimitError, APIConnectionError, InvalidRequestError, AuthenticationError) as e3:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: Application server Not responding')
        result = []
        status = 'AppServerError'
    except:
        Logger.error(traceback.format_exc())
        Logger.error('UNKNOWN ERROR: occurred')
        result = []
        status = 'UnknownError'

    print('\n---------qa:{0}-------------\n'.format(status))
    Logger.info(f"\n---------qa:{status}-------------\n")
    Logger.debug("QA chain run ran in {}s".format(round(time.time() - begin_start , 4)))

    return result, cnt, 0 if len(call_tokens) == 0 else np.average(call_tokens), status


