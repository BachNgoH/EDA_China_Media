from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
import json
import asyncio
from typing import List
import dotenv
import os

dotenv.load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """
You are a helpful assistant that classifies the news content if it is related to the 
China's comminty of shared future initiative:

The Community of Shared Future for Mankind is a concept proposed by the Communist Party of China. It emphasizes the importance of international cooperation and mutual benefit, as well as the need for countries to work together to address global challenges.

This is the news content:
{context}

======================

Please classify the news content if it is related to the Community of Shared Future for Mankind.
If it is related classify its sentiment towards the Community of Shared Future for Mankind.
These are the keywords related to the Community of Shared Future for Mankind:
{keywords}

Response in JSON format:
{{
    "is_related": true/false
}}
"""

ADVANCED_ANALYSIS_PROMPT_TEMPLATE = """
You are a helpful assistant that classifies the news content if it is related to the 
China's comminty of shared future initiative:

The Community of Shared Future for Mankind is a concept proposed by the Communist Party of China. It emphasizes the importance of international cooperation and mutual benefit, as well as the need for countries to work together to address global challenges.

This is the news content:
{context}

======================

Please analyze the news content and provide a detailed analysis of the news content.
These are the keywords related to the Community of Shared Future for Mankind:
{keywords}
Count the number of times the keywords appear in the content.

Response in JSON format:
{{
    "title": "the title of the news",
    "is_title_contain_shared_future": true/false # if the title contains the keywords related to the Community of Shared Future for Mankind
    "sentiment": "positive"/"negative"/"neutral"/"concerned"
    "main_keywords": [("keyword1", 3), ("keyword2", 4), ("keyword3", 2)] # the keywords and the number of times they appear in the content
}}
"""

KEYWORDS = ["Community of common destiny", "Community of shared future", "Community of shared destiny", "Community of common destiny of mankind", "Belt and Road Initiative", "Asian Infrastructure Investment Bank", "Global Development Initiative", "Global Security Initiative", "Global Governance Initiative", "Global Civilization Initiative", "Global Development Initiative", "Global Security Initiative", "Global Governance Initiative", "Global Civilization Initiative", "Global Security Initiative", "China's influence", "China's soft power", "ASIAN perception", "China dream"]

async def classify_content(content: str) -> dict:
    llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    prompt = PromptTemplate(PROMPT_TEMPLATE)
    response = llm.complete(prompt.format(context=content, keywords=KEYWORDS), response_format={"type": "json_object"})
    return json.loads(response.text)

async def advanced_analysis(content: str) -> dict:
    llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    prompt = PromptTemplate(ADVANCED_ANALYSIS_PROMPT_TEMPLATE)
    response = llm.complete(prompt.format(context=content, keywords=KEYWORDS), response_format={"type": "json_object"})
    return json.loads(response.text)

async def process_batch(items: List[dict]) -> List[dict]:
    # First, classify all items
    classification_tasks = [classify_content(f"URL: {item['url']}\nContent: {item['content']}") for item in items]
    classification_results = await asyncio.gather(*classification_tasks)
    
    # Update items with classification results and create analysis tasks for related items
    analysis_tasks = []
    for item, result in zip(items, classification_results):
        item['is_related'] = result['is_related']
        if result['is_related']:
            analysis_tasks.append((item, advanced_analysis(item['content'])))
    
    # Process advanced analysis for related items
    for item, analysis_task in analysis_tasks:
        analysis_result = await analysis_task
        item.update({
            'title': analysis_result['title'],
            'is_title_contain_shared_future': analysis_result['is_title_contain_shared_future'],
            'sentiment': analysis_result['sentiment'],
            'main_keywords': analysis_result['main_keywords']
        })
    
    return items

async def main(input_file):
    with open(input_file, 'r') as f:
        content = json.load(f)
    
    # Process content in batches of 5
    batch_size = 5
    processed_content = []
    
    for i in range(0, len(content), batch_size):
        batch = content[i:i + batch_size]
        processed_batch = await process_batch(batch)
        processed_content.extend(processed_batch)
        print(f"Processed batch {i//batch_size + 1}/{(len(content) + batch_size - 1)//batch_size}")

    with open(f'{input_file.split(".")[0]}_classified.json', 'w') as f:
        json.dump(processed_content, f, indent=4)

    print(f"Processed {len(processed_content)} articles")

if __name__ == "__main__":
    asyncio.run(main('processed_articles_st.json'))
    asyncio.run(main('processed_articles_flp_.json'))
    asyncio.run(main('processed_articles_jkt_.json'))
    asyncio.run(main('processed_articles_bk.json'))