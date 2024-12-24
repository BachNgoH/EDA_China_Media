import pandas as pd
import json

# Read the JSON file
with open('processed_articles_flp_classified.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Extract relevant fields from each article
articles_data = []
for article in data:
    article_info = {
        'url': article.get('url', ''),
        'date': article.get('date', ''),
        'content': article.get('content', ''),
        'is_related': article.get('is_related', False)
    }
    articles_data.append(article_info)

# Create DataFrame
df = pd.DataFrame(articles_data)

# Export to Excel
df.to_excel('articles_flp.xlsx', index=False, engine='openpyxl')