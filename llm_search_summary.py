

from prompt import search_summary, search_qa

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

from logging_handler import Logger
from timer import timed
import traceback
import config

from json.decoder import JSONDecodeError
from openai.error import APIError, Timeout, RateLimitError, APIConnectionError, AuthenticationError, \
    ServiceUnavailableError, InvalidRequestError

from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.chains import SequentialChain, TransformChain
from langchain.memory import SimpleMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser, RetryWithErrorOutputParser
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

    relqa: List[QuestionAnswerSet] = Field(description="a set of generated question and their corresponding summarized answers.")


@timed
def generate_summary(paras: List[str], query: str) -> (Dict[str, str], int, float):
    print('\n---------summary-------------\n')

    cnt = 0
    call_tokens = []

    def summary_llm_call() -> Dict[str, str]:

        start = time.time()

        nonlocal cnt

        model = AzureChatOpenAI(
            deployment_name=config.AZURE_DEPLOYMENT_NAME,
            model_name=config.AZURE_MODEL_NAME,
            max_tokens=200,
            temperature=0,
            verbose=True,
            request_timeout=60
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

        Logger.debug("chain intialization ran in {}s".format(round(time.time() - start, 4)))

        start = time.time()
        gpt_op = summary_chain({"paras": paras, "query": query})
        Logger.debug("chain run ran in {}s".format(round(time.time() - start, 4)))


        start = time.time()
        Logger.info("\n Response from GPT : {0}".format(gpt_op))

        generated_summary = gpt_op['generated_summary']
        #print(generated_summary)

        summary_prompt = summary_template.format(paras=paras, query=query, format_instructions=summary_format_instructions)
        print(summary_prompt)
        summary_ip_tokens = model.get_num_tokens(summary_prompt)
        summary_op_tokens = model.get_num_tokens(generated_summary)
        print(summary_op_tokens)
        call_tokens.append(summary_ip_tokens + summary_op_tokens)
        cnt += 1
        Logger.debug("token calc ran in {}s".format(round(time.time() - start, 4)))

        try:
            start = time.time()
            summary_result = summary_parser.parse(generated_summary).json()
            summary_result = json.loads(summary_result)
            Logger.info('\n Langchain json summary content parsed: {0}'.format(summary_result))
            Logger.debug("langchain parsing ran in {}s".format(round(time.time() - start, 4)))
        except Exception as lang_err:
            Logger.error(traceback.format_exc())
            print(lang_err)
            summary_result = generated_summary[generated_summary.find('{'): generated_summary.rfind('}') + 1]
            summary_result = ast.literal_eval(summary_result)
            Logger.info('\n Regex json summary content parsed: {0}'.format(summary_result))

        return summary_result

    try:
        result = summary_llm_call()
        status = 'LLMParsed'
    except (AssertionError, JSONDecodeError, OutputParserException, KeyError) as e:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: summary Parsing or Assertion Failed')
        try:
            result = summary_llm_call()
            status = 'LLMRetryParsed'
        except (APIError, Timeout, ServiceUnavailableError) as e1:
            Logger.error(traceback.format_exc())
            Logger.error('ERROR: LLM SERVER Not responding')
            result = {}
            status = 'LLMServerError'
        except (RateLimitError, APIConnectionError, InvalidRequestError, AuthenticationError) as e3:
            Logger.error(traceback.format_exc())
            Logger.error('ERROR: Application server Not responding')
            result = {}
            status = 'AppServerError'
        except:
            Logger.error(traceback.format_exc())
            Logger.error('UNKNOWN ERROR: occurred')
            result = {}
            status = 'UnknownError'
    except (APIError, Timeout, ServiceUnavailableError) as e1:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: LLM SERVER Not responding')
        result = {}
        status = 'LLMServerError'
    except (RateLimitError, APIConnectionError, InvalidRequestError, AuthenticationError) as e3:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: Application server Not responding')
        result = {}
        status = 'AppServerError'
    except:
        Logger.error(traceback.format_exc())
        Logger.error('UNKNOWN ERROR: occurred')
        result = {}
        status = 'UnknownError'

    print('\n---------summary:{0}-------------\n'.format(status))
    Logger.info(f"\n---------summary:{status}-------------\n")

    return result, cnt, 0 if len(call_tokens) == 0 else np.average(call_tokens), status


@timed
def generate_qa(paras: List[str], query: str) -> (List[Dict[str, str]], int, float):
    print('\n---------RelevantQ&A-------------\n')

    cnt = 0
    call_tokens = []

    def qa_llm_call() -> Dict[str, str]:

        start = time.time()

        nonlocal cnt

        model = AzureChatOpenAI(
            deployment_name=config.AZURE_DEPLOYMENT_NAME,
            model_name=config.AZURE_MODEL_NAME,
            max_tokens=300,
            temperature=0.7,
            verbose=True,
            request_timeout=60
        )

        template = "Ignore previous instructions.\n you are a part of search engine whose job is to first find whether answer to the given user's query exist in the provided search results, if yes then you should generate pair of new questions(MUST be related to given user's query) and their summarized answers( MUST come from given search results only.)"
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)

        qa_parser = PydanticOutputParser(pydantic_object=RelevantQuestionAnswers)
        qa_format_instructions = qa_parser.get_format_instructions()

        qa_template = PromptTemplate(input_variables=["paras", "query"],
                                        template=search_qa,
                                        partial_variables={"format_instructions": qa_format_instructions})
        
        human_message_prompt = HumanMessagePromptTemplate(prompt=qa_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        qa_chain = LLMChain(llm=model, prompt=chat_prompt, output_key="generated_qa")

        Logger.debug("chain intialization ran in {}s".format(round(time.time() - start, 4)))

        start = time.time()
        gpt_op = qa_chain({"paras": paras, "query": query})
        Logger.debug("chain run ran in {}s".format(round(time.time() - start, 4)))


        start = time.time()
        Logger.info("\n Response from GPT : {0}".format(gpt_op))

        generated_qa = gpt_op['generated_qa']
        #print(generated_qa)

        qa_prompt = qa_template.format(paras=paras, query=query, format_instructions=qa_format_instructions)
        print(qa_prompt)
        qa_ip_tokens = model.get_num_tokens(qa_prompt)
        qa_op_tokens = model.get_num_tokens(generated_qa)
        print(qa_op_tokens)
        call_tokens.append(qa_ip_tokens + qa_op_tokens)
        cnt += 1
        Logger.debug("token calc ran in {}s".format(round(time.time() - start, 4)))

        try:
            start = time.time()
            qa_result = qa_parser.parse(generated_qa).json()
            qa_result = json.loads(qa_result)['relqa']
            Logger.info('\n Langchain json generated qa parsed: {0}'.format(qa_result))
            Logger.debug("langchain parsing ran in {}s".format(round(time.time() - start, 4)))
        except Exception as lang_err:
            Logger.error(traceback.format_exc())
            print(lang_err)
            qa_result = generated_qa[generated_qa.find('['): generated_qa.rfind(']') + 1]
            qa_result = ast.literal_eval(qa_result)
            Logger.info('\n Regex json qa content parsed: {0}'.format(qa_result))

        return qa_result

    try:
        result = qa_llm_call()
        status = 'LLMParsed'
    except (AssertionError, JSONDecodeError, OutputParserException, KeyError) as e:
        Logger.error(traceback.format_exc())
        Logger.error('ERROR: qa Parsing or Assertion Failed')
        try:
            result = qa_llm_call()
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

    return result, cnt, 0 if len(call_tokens) == 0 else np.average(call_tokens), status

if __name__ == "__main__":

    paras = ["An acid is often used to remove hard-water deposits, discoloration on metal surfaces and rust stains. White vinegar and lemon juice are mild acids that can be used in place of commercial products. Lemon juice should not be used on silver. Prolonged exposure to an acid may irritate the respiratory tract, so it is important to provide adequate ventilation when using the products.",

            "People spend an average of 90 percent of their time indoors. Studies conducted by the Environmental Protection Agency(EPA) show levels of several common organic pollutants to be 2 to 5 times higher inside homes than outside. Many of these pollutants come from the volatile organic compounds (VOCs) released from household cleaning products. Indoor pollutants can be reduced by limiting the number of chemicals used indoors. By following three basic guidelines you can improve your indoor environment, save money and help conserve natural resources",

            "Simplify cleaning and reduce VOCs by using fewer cleaning products. Choose or make products that you can use for several purposes. If you use fewer cleaners then you have are storing fewer chemicals in your home. Most cleaning products contain one or more of these basic cleaning ingredients: abrasive, alkali, acid, bleach, disinfectant and surfactants."]

    #query = "Why does earth rotate around sun?"
    #query = "how to remove hard-water stains?"
    #query = "how to remove dirt from my furniture?"
    #query = "fbsjfb sjfjs sjnosn jdjdj"
    #query = "What are VOCs?"
    query="who is Obama?"

    summary, api_cnt, api_tokens, status = generate_summary(paras, query)

    Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for summary generation")

    print(summary)

    gen_qa, api_cnt, api_tokens, status = generate_qa(paras, query)

    Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for qa generation")

    print(gen_qa)

