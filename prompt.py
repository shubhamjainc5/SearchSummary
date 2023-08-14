search_summary = """
User query:
{query}

Following are the list of search results fetched by search engine:
{paras}

Your task is to understand user's query first and check if the answer for that query is available in any of the above search results .Select those search results paragraphs then generate a summarized answer with respect to user's query.  
  
Also you must follow below instructions before coming up with the answer:    
1. the final summarized answer MUST always come from the provided search results.    
2. If you can't come up with the summarized answer from the provided search results or user's query seems to be not relevant to the  provided search results, then you MUST reply with "NOT FOUND" as summarized answer. Please you MUST never ever try to fabricate, mislead, make up the summarized answer.
\n{format_instructions}
Output JSON:
"""

search_qa = """
User query:
{query}

Following are the list of search results fetched by search engine:
{paras}

Your task is to understand user's query first and find if the answer for that query is available in any of the above search results .  
Only when the answer to the user's search query is available , you should generate pair of question and summarized answers which are related to given user query and whose answers also lies in the provided search results.  
    
Also you must follow below instructions before coming up with the question and summarized answers:  
1. Generated summarized answers MUST always come from the provided search results.  
2. Generated question MUST be related to giver user's query but should not be exactly same.  
3. If you can't understand user's query or user's query seems irrelevant to the provided search results, then you should not generate anything and simply returns empty array in output json.  

\n{format_instructions}
Output JSON:
"""