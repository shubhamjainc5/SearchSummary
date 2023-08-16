from fastapi import FastAPI
from utils.logging_handler import Logger
from utils.llm_search_summary import generate_summary, generate_qa
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import time


app = FastAPI()

origins = ["*"]  # specify orgins to handle CORS issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/llm_api/get_summary")
async def get_summary():

    paras = ["An acid is often used to remove hard-water deposits, discoloration on metal surfaces and rust stains. White vinegar and lemon juice are mild acids that can be used in place of commercial products. Lemon juice should not be used on silver. Prolonged exposure to an acid may irritate the respiratory tract, so it is important to provide adequate ventilation when using the products.",

        "People spend an average of 90 percent of their time indoors. Studies conducted by the Environmental Protection Agency(EPA) show levels of several common organic pollutants to be 2 to 5 times higher inside homes than outside. Many of these pollutants come from the volatile organic compounds (VOCs) released from household cleaning products. Indoor pollutants can be reduced by limiting the number of chemicals used indoors. By following three basic guidelines you can improve your indoor environment, save money and help conserve natural resources",

        "Simplify cleaning and reduce VOCs by using fewer cleaning products. Choose or make products that you can use for several purposes. If you use fewer cleaners then you have are storing fewer chemicals in your home. Most cleaning products contain one or more of these basic cleaning ingredients: abrasive, alkali, acid, bleach, disinfectant and surfactants."]

    #query = "Why does earth rotate around sun?"
    #query = "how to remove hard-water stains?"
    #query = "how to remove dirt from my furniture?"
    #query = "fbsjfb sjfjs sjnosn jdjdj"
    #query = "What are VOCs?"
    query="who is Obama?"

    Logger.info(f"Running on {os.getpid()}")

    summary, api_cnt, api_tokens, status = await generate_summary(paras, query)

    Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for summary generation")

    print(summary)

    return summary


@app.post("/llm_api/get_relqa")
async def get_relqa():

    paras = ["An acid is often used to remove hard-water deposits, discoloration on metal surfaces and rust stains. White vinegar and lemon juice are mild acids that can be used in place of commercial products. Lemon juice should not be used on silver. Prolonged exposure to an acid may irritate the respiratory tract, so it is important to provide adequate ventilation when using the products.",

        "People spend an average of 90 percent of their time indoors. Studies conducted by the Environmental Protection Agency(EPA) show levels of several common organic pollutants to be 2 to 5 times higher inside homes than outside. Many of these pollutants come from the volatile organic compounds (VOCs) released from household cleaning products. Indoor pollutants can be reduced by limiting the number of chemicals used indoors. By following three basic guidelines you can improve your indoor environment, save money and help conserve natural resources",

        "Simplify cleaning and reduce VOCs by using fewer cleaning products. Choose or make products that you can use for several purposes. If you use fewer cleaners then you have are storing fewer chemicals in your home. Most cleaning products contain one or more of these basic cleaning ingredients: abrasive, alkali, acid, bleach, disinfectant and surfactants."]

    #query = "Why does earth rotate around sun?"
    #query = "how to remove hard-water stains?"
    #query = "how to remove dirt from my furniture?"
    #query = "fbsjfb sjfjs sjnosn jdjdj"
    #query = "What are VOCs?"
    query="who is Obama?"

    Logger.info(f"Running on {os.getpid()}")

    # start = time.time()
    # time.sleep(5)
    # gen_qa=[]
    # Logger.info("complete chain ran in {}s".format(round(time.time() - start, 4)))

    gen_qa, api_cnt, api_tokens, status = await generate_qa(paras, query)

    Logger.info(f"{api_cnt} API Calls were made with an average of {api_tokens} tokens per call for qa generation")

    print(gen_qa)

    return gen_qa

@app.get('/api/')
async def root():
    return {'message': 'This is the backend endpoint of summary & QA retriver of search results by LLM service.'}


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