from fastapi import FastAPI
from utils.llm_search_summary import generate_summary, generate_qa
from utils.doc_ranker import rerank_documents
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import time
from pydantic import BaseModel
from typing import Dict, List
import json
import traceback
from collections import OrderedDict
import re
import uvicorn
import requests
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import config

logging.basicConfig(filename='logs/app.log',
                    filemode='a',
    format='%(asctime)s,%(process)d %(name)s %(levelname)s %(message)s', level=logging.DEBUG)

Logger = logging.getLogger(__name__)
Logger.propagate = False
Logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s,%(process)d %(name)s %(levelname)s %(message)s')
handler = TimedRotatingFileHandler('logs/app.log',
                                    when="W0",
                                    interval=1,
                                    backupCount=4)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
Logger.addHandler(handler)

app = FastAPI()

origins = ["*"]  # specify orgins to handle CORS issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Summary(BaseModel):
    requestId: int
    user_query: str
    search_results: Dict

class RelQA(BaseModel):
    requestId: int
    user_query: str
    search_results: Dict

class Rerank(BaseModel):
    query: str
    top_k: int


@app.post("/rerank")
async def rerank_document(input: Rerank):

    try:
        
        query = input.query
        top_k = input.top_k
        Logger.info(f"Recieved request for summary for '{query}' user query")

        start_time = time.time()
        rs = requests.post(config.ELASTIC_HOST_URL,json= {"query":query,"top_k":top_k},
                    headers={"Content-Type": "application/json"})
        status_code = rs.status_code
        Logger.info(f"Elastic search sent response with {status_code} status code")
        if status_code==200:
            
            response_text = json.loads(rs.text)
            Logger.info("Elastic search document retriveal took {:.4f} seconds".format(time.time() - start_time))
            if len(response_text)>0:
                start_time = time.time()
                rerank_text, result_status = await rerank_documents(response_text,query)
                Logger.info("Overall reranking took {:.4f} seconds".format(time.time() - start_time))
            else:
                rerank_text= []
                result_status = 'Blank Elastic result'
        else:
            rerank_text= []
            result_status = 'Elastic Failed'
    except Exception as e:
        Logger.error(traceback.format_exc())
        rerank_text= []
        result_status = 'UnknownError'

    return json.dumps({'content':rerank_text, 'status':result_status})


@app.post("/llm_api/get_summary")
async def get_summary(input: Summary):

    try:
        requestId = input.requestId
        query = input.user_query
        Logger.info(f"Recieved '{requestId}' request for summary for '{query}' user query")

        paras = [ p['content']  for p in input.search_results['content']]
        Logger.info(f"Search results for '{requestId}' request:  {paras}")

        # Logger.info(f"Running on {os.getpid()}")

        raw_summary, api_cnt, api_tokens, status = await generate_summary(paras, query)

        Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for summary generation")

        print(raw_summary)


        if raw_summary['Summary']!='':
            summary={}
            citations = [c.strip('[').strip(']') for c in re.findall(r'\[\d+\]' ,raw_summary['Summary'])]
            citations = list(OrderedDict.fromkeys([int(c) for c in citations if c.isdigit()]))
            summary['Summary'] = raw_summary
            ct = {}
            if len(citations)>0:
                for c in citations:
                    if c<len(paras)+1:
                        ct[c] = input.search_results['content'][c-1]['meta']['Ind_number']
            summary['citations']=ct
        else:
            summary = {'Summary':'', 'citations':{}}
        
    except Exception as e:
        Logger.error(traceback.format_exc())
        summary = {'Summary':'', 'citations':{}}

    return summary


@app.post("/llm_api/get_relqa")
async def get_relqa(input: RelQA):

    try:

        requestId = input.requestId
        query = input.user_query
        Logger.info(f"Recieved '{requestId}' request for summary for '{query}' user query")

        paras = [ p['content']  for p in input.search_results['content']]
        Logger.info(f"Search results for '{requestId}' request:  {paras}")

        # Logger.info(f"Running on {os.getpid()}")

        raw_qa, api_cnt, api_tokens, status = await generate_qa(paras, query)

        Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for qa generation")
        print(raw_qa)

        if len(raw_qa)>0:
            gen_qa=[]
            for qa in raw_qa:
                qa_dict={}
                citations = [c.strip('[').strip(']') for c in re.findall(r'\[\d+\]' ,qa['answer'])]
                citations = list(OrderedDict.fromkeys([int(c) for c in citations if c.isdigit()]))
                qa_dict['question'] = qa['question']
                qa_dict['answer'] = qa['answer']
                ct = {}
                if len(citations)>0:
                    for c in citations:
                        if c<len(paras)+1:
                            ct[c]=input.search_results['content'][c-1]['meta']['Ind_number']
                qa_dict['citations']=ct
                gen_qa.append(qa_dict)
        else:
            gen_qa = []

    except Exception as e:
        Logger.error(traceback.format_exc())
        gen_qa = []

    return gen_qa

@app.get('/api/')
async def root():
    return {'message': 'This is the backend endpoint of summary & QA retriver of search results by LLM service.'}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=9050)

# if __name__ == "__main__":

#     paras = ["An acid is often used to remove hard-water deposits, discoloration on metal surfaces and rust stains. White vinegar and lemon juice are mild acids that can be used in place of commercial products. Lemon juice should not be used on silver. Prolonged exposure to an acid may irritate the respiratory tract, so it is important to provide adequate ventilation when using the products.",

#             "People spend an average of 90 percent of their time indoors. Studies conducted by the Environmental Protection Agency(EPA) show levels of several common organic pollutants to be 2 to 5 times higher inside homes than outside. Many of these pollutants come from the volatile organic compounds (VOCs) released from household cleaning products. Indoor pollutants can be reduced by limiting the number of chemicals used indoors. By following three basic guidelines you can improve your indoor environment, save money and help conserve natural resources",

#             "Simplify cleaning and reduce VOCs by using fewer cleaning products. Choose or make products that you can use for several purposes. If you use fewer cleaners then you have are storing fewer chemicals in your home. Most cleaning products contain one or more of these basic cleaning ingredients: abrasive, alkali, acid, bleach, disinfectant and surfactants."]

#     #query = "Why does earth rotate around sun?"
#     #query = "how to remove hard-water stains?"
#     #query = "how to remove dirt from my furniture?"
#     #query = "fbsjfb sjfjs sjnosn jdjdj"
#     #query = "What are VOCs?"
#     query="who is Obama?"

#     summary, api_cnt, api_tokens, status = asyncio.run(generate_summary(paras, query))

#     Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for summary generation")

#     print(summary)

#     gen_qa, api_cnt, api_tokens, status = asyncio.run(generate_qa(paras, query))

#     Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for qa generation")

#     print(gen_qa)