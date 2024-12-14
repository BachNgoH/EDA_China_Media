from urllib.parse import unquote
import json
from datetime import datetime

with open('bk_url_list.json', 'r', encoding='utf-8') as f:
    urls = json.load(f)

for url in urls:
    # Find the href parameter
    href_start = url['url'].find("href=") + 5  # Add 5 to skip "href="
    href_end = url['url'].find("&", href_start)  # Find the next & after href

    # Extract the encoded href
    encoded_href = url['url'][href_start:href_end]
    
    # Decode the URL-encoded string
    decoded_href = unquote(encoded_href)
    url['url'] = decoded_href

# filter the urls from September 2023 to October 2024
urls = [url for url in urls if datetime.strptime(url['date'], '%Y-%m-%d') >= datetime(2023, 9, 1) and datetime.strptime(url['date'], '%Y-%m-%d') <= datetime(2024, 10, 31)]

with open('bk_url_list_clean.json', 'w', encoding='utf-8') as f:
    json.dump(urls, f, ensure_ascii=False, indent=4)
    
