search_summary = """
User query:
{query}

Following are the list of search results fetched by search engine:
{paras}

Your task is to understand user's query first and check if the answer for that query is available in any of the above search results .Select those search results paragraphs then generate a summarized answer with respect to user's query.  
  
Also you must follow below instructions before coming up with the answer:    
1. the final summarized answer MUST always come from the provided search results.    
2. If you can't come up with the summarized answer from the provided search results or user's query seems to be not relevant to the  provided search results, then you MUST reply with "NOT FOUND" as summarized answer.
3. To ensure the credibility of summarized answer, Be sure you MUST always include a correct citations number whenever necessary in brackets as [1], [2]...etc. based on provided search results after each phrase or sentence to indicate which part of provided search results supports summarized answer.
4. Please you MUST never ever try to fabricate, mislead, make up the summarized answer.
\n{format_instructions}
Output JSON:
"""

search_qa = """
Following are the list of search results fetched by search engine:
{paras}

Your task is to generate pair of questions and summarized answers(must come from provided search results).
    
Also you must follow below instructions before coming up with the question and summarized answers:  
1. Generated question and summarized answers MUST always come from the provided search results.  
2. Please you MUST never ever try to fabricate, mislead, make up the summarized answer.
3. Generate as many as possible combinations of distinct question and summarized answers.
4. To ensure the credibility of summarized answers for each question, Be sure you MUST always include a correct citations number whenever necessary in brackets as [1], [2]...etc. based on provided search results after each phrase or sentence to indicate which part of provided search results supports summarized answer.
\n{format_instructions}
Output JSON:
"""