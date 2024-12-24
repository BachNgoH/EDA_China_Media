from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
import json
import asyncio
from typing import List
import dotenv
import os
from argparse import ArgumentParser
from datetime import datetime

dotenv.load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ARTICLE_TYPE_PROMPT = """
Please analyze this news content and classify its article type based on these criteria:
1. Interview (Phỏng vấn): Question-answer format, dialogue between reporter and interviewee
2. Short News (Tin Ngắn): 60-100 words, complete but concise information
3. Medium News (Tin Vừa): 80-200 words, more detailed than short news
4. In-depth News (Tin Sâu): Up to 400 words, detailed analysis with multiple perspectives
5. Chronicle News (Tin Tường Thuật): ~200 words, chronological reporting of events
6. Commentary (Bình luận): 200-3000 words, expressing personal viewpoints with clear stance

Content:
{content}

Response in JSON format:
{{
    "article_type": "Interview"/"Short News"/"Medium News"/"In-depth News"/"Chronicle News"/"Commentary",
    "article_type_reason": "Brief explanation of why this article type was chosen"
}}
"""

async def get_article_type(content: str) -> dict:
    llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    prompt = PromptTemplate(ARTICLE_TYPE_PROMPT)
    response = llm.complete(prompt.format(content=content), response_format={"type": "json_object"})
    return json.loads(response.text)

async def process_batch(items: List[dict]) -> List[dict]:
    tasks = [get_article_type(item['content']) for item in items]
    results = await asyncio.gather(*tasks)
    
    for item, result in zip(items, results):
        item['article_type'] = result['article_type']
        item['article_type_reason'] = result['article_type_reason']
    
    return items

async def main(input_file):
    # Load existing classified content
    with open(input_file, 'r') as f:
        content = json.load(f)
    
    # Process in batches of 5
    batch_size = 5
    updated_content = [article for article in content if 'article_type' in article.keys()]
    
    content = [article for article in content if article['is_related'] == True]
    # filter articles before 2023-09-01
    content = [article for article in content if datetime.strptime(article['date'], '%Y-%m-%d') >= datetime(2023, 9, 1)]
    content = [article for article in content if 'article_type' not in article.keys()]
    
    print(f"Found {len(content)} articles to update")

    for i in range(0, len(content), batch_size):
        batch = content[i:i + batch_size]
        processed_batch = await process_batch(batch)
        updated_content.extend(processed_batch)
        print(f"Processed batch {i//batch_size + 1}/{(len(content) + batch_size - 1)//batch_size}")

    # Save updated content
    output_file = f'{input_file.split(".")[0]}_with_types.json'
    with open(output_file, 'w') as f:
        json.dump(updated_content, f, indent=4)

    print(f"Updated {len(updated_content)} articles")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input_file", type=str, required=True,
                      help="Path to the JSON file containing classified articles")
    args = parser.parse_args()
    asyncio.run(main(args.input_file)) 