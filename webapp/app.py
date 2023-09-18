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
# Logger.propagate = False
Logger.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s,%(process)d %(name)s %(levelname)s %(message)s')
# handler = TimedRotatingFileHandler('logs/app.log',
#                                     when="W0",
#                                     interval=1,
#                                     backupCount=4)
# handler.setLevel(logging.INFO)
# handler.setFormatter(formatter)
# Logger.addHandler(handler)

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
    channel_id: str
    channel_index:str

class RelQA(BaseModel):
    requestId: int
    user_query: str
    search_results: Dict
    channel_id: str
    channel_index:str

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

    return {'content':rerank_text, 'status':result_status}


@app.post("/llm_api/get_summary")
async def get_summary(input: Summary):

    begin_start= time.time()

    try:
        requestId = input.requestId
        query = input.user_query
        Logger.info(f"Recieved '{requestId}' request for summary for '{query}' user query")

        top_k = 3

        input_documents = input.search_results['content'][:top_k]

        paras = [ {"Doc_number":i+1, "text":input_documents[i]['meta']['text_pdf']}  for i in range(len(input_documents))]
        Logger.info(f"Search results for '{requestId}' request:  {paras}")

        raw_summary, api_cnt, api_tokens, status = await generate_summary(paras, query)

        input_doc_numbers = { str(j+1):(input_documents[j]['meta']['file_name'],input_documents[j]['meta']['page_num'])  for j in range(len(input_documents))}

        Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for summary generation")

        print(raw_summary)

        # raw_summary = {'Summary': 'To connect to a Bluetooth-enabled device using your Lenovo laptop, you can follow these steps: 1. Click the action center icon in the Windows notification area. Enable the Bluetooth feature. [1][Doc_number:2] 2. Click the bluetooth options to add a bluetooth device, and then follow the on-screen instructions. [1] Alternatively, you can press Fn+F5 to enable the Bluetooth feature on your laptop. Then, right-click the data that you want to send and select Send To ➙ Bluetooth Devices. Choose a Bluetooth device from the list and follow the instructions on the screen. [2] If you are using Windows XP, you can double-click the My Bluetooth Places icon on the desktop. Then, go to Bluetooth Tasks and double-click View devices in range. Select the device you want to connect to and choose the service you want to use. [3]'}

        if raw_summary['Summary']!='':
            summary={}
            summary['Summary'] = raw_summary['Summary']

            citations_matches = list(re.finditer(r'\[\d+\]', raw_summary['Summary']))
            ct_list = []
            if len(citations_matches)>0:
                for match in citations_matches: 
                    ct = {}
                    ct['start'] = match.start()+1
                    cit = raw_summary['Summary'][ct['start']]
                    ct['end'] = match.start()+2
                    ct ['file_name'] = input_doc_numbers[cit][0]
                    ct ['page_num'] = input_doc_numbers[cit][1]
                    ct ['Ind_number'] = int(raw_summary['Summary'][ct['start']])
                    if cit in list(input_doc_numbers.keys()):
                        ct_list.append(ct)
                
            summary['citations']=ct_list
        else:
            summary = {'Summary':'', 'citations':[]}
        
        Logger.info(f"response for executive summary call is {summary}")

    except Exception as e:
        Logger.error(traceback.format_exc())
        summary = {'Summary':'', 'citations':[]}
        Logger.info(f"response for executive summary call is {summary}")

    Logger.info("summary API took {}s".format(round(time.time() - begin_start , 4)))
    return summary


@app.post("/llm_api/get_relqa")
async def get_relqa(input: RelQA):

    begin_start= time.time()

    try:

        requestId = input.requestId
        query = input.user_query
        Logger.info(f"Recieved '{requestId}' request for QA for '{query}' user query")

        top_k = 3

        input_documents = input.search_results['content'][:top_k]

        paras = [ {"Doc_number":i+1, "text":input_documents[i]['meta']['text_pdf']}  for i in range(len(input_documents))]
        Logger.info(f"Search results for '{requestId}' request:  {paras}")

        raw_qa, api_cnt, api_tokens, status = await generate_qa(paras, query)

        input_doc_numbers = { str(j+1):(input_documents[j]['meta']['file_name'],input_documents[j]['meta']['page_num'])  for j in range(len(input_documents))}

        Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for qa generation")
        print(raw_qa)

        # raw_qa = [{'question': 'How do I enable the Bluetooth feature in Windows?', 'answer': 'To enable the Bluetooth feature in Windows, you can click the action center icon in the Windows[2] notification area and enable the Bluetooth feature. [1]'}, {'question': 'How can I send data via Bluetooth?', 'answer': 'To send data via Bluetooth, you can press Fn+F5 to enable the Bluetooth feature and then right-click the data that you want to send. Select Send To Bluetooth Devices and choose a Bluetooth device to send the data to. [2]'}, {'question': 'How do I access devices with Bluetooth enabled?', 'answer': 'To access devices with Bluetooth enabled, you can double-click the My Bluetooth Places icon on the desktop. For Windows XP, go to Bluetooth Tasks and double-click View devices in range. A list of devices with Bluetooth enabled will appear. Click on the device you want to access and select the service you want to use. [3]'}]

        if len(raw_qa)>0:
            gen_qa=[]
            for qa in raw_qa:
                qa_dict={}
                qa_dict['question'] = re.sub(r'\[[^]]*\]','',qa['question'])
                qa_dict['answer'] = qa['answer']
                citations_matches = list(re.finditer(r'\[\d+\]', qa['answer']))
                ct_list = []
                if len(citations_matches)>0:
                    for match in citations_matches:
                        ct = {}
                        ct['start'] = match.start()+1
                        cit = qa['answer'][ct['start']]
                        ct['end'] = match.start()+2
                        ct ['file_name'] = input_doc_numbers[cit][0]
                        ct ['page_num'] = input_doc_numbers[cit][1]
                        ct ['Ind_number'] = int(qa['answer'][ct['start']])
                        if cit in list(input_doc_numbers.keys()):
                            ct_list.append(ct)
                qa_dict['citations']=ct_list
                gen_qa.append(qa_dict)
        else:
            gen_qa = []
        Logger.info(f"response for related QA  call is {gen_qa}")

    except Exception as e:
        Logger.error(traceback.format_exc())
        gen_qa = []
        Logger.info(f"response for related QA call is {gen_qa}")

    Logger.info("Q&A API took {}s".format(round(time.time() - begin_start , 4)))
    return gen_qa

@app.get('/api/')
async def root():
    return {'message': 'This is the backend endpoint of summary & QA retriver of search results by LLM service.'}


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=9050)

# if __name__ == "__main__":

#     paras = [{'Doc_number': 157, 'text': 'In another scenario, if you carry your computer around without the included ac power adapter, you may use \na capable USB Type-C charger to provide power through the USB Type-C connector. In both scenarios, the \noutput power of a USB Type-C charger or the USB Type-C connector on a dock or display should be at least \n20 V and 2.25 A in order to provide power to your computer. The following table lists the charging capability \nof a USB Type-C connector on a charger or an external device based on its maximum output power.'}, {'Doc_number': 155, 'text': 'Power input through a USB Type-C connector'}, {'Doc_number': 165, 'text': 'Note: If the computer is already connected to an electrical outlet using the included power adapter, the \ncomputer will not receive power through the USB Type-C connector.'}]

#     query="can I charge my thinkbook through usb type C connector?"

#     summary, api_cnt, api_tokens, status = asyncio.run(generate_summary(paras, query))

#     Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for summary generation")

#     print(summary)

    # gen_qa, api_cnt, api_tokens, status = asyncio.run(generate_qa(paras, query))

    # Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for qa generation")

    # print(gen_qa)