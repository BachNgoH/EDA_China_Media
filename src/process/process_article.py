import json
import re
from datetime import datetime
from pathlib import Path

def extract_date_from_url(url):
    # Extract date pattern YYYY/MM/DD from URL
    date_pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
    match = re.search(date_pattern, url)
    if match:
        try:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
        except ValueError:
            return None
    return None

def load_article_content(index):
    try:
        article_path = Path(f'articles/article_{index + 1}.md')
        if article_path.exists():
            with open(article_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error reading article_{index}.md: {e}")
    return None

def process_urls():
    # Load original JSON
    with open('st_url_list.json', 'r') as f:
        urls = json.load(f)
    
    # Process each item
    processed_data = []
    for i, item in enumerate(urls):
        url = item['url']
        date = extract_date_from_url(url)
        content = load_article_content(i)
        
        processed_item = {
            'url': url,
            'date': date,
            'content': content
        }
        processed_data.append(processed_item)
    
    # Save to new JSON
    with open('processed_articles_st.json', 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    process_urls()