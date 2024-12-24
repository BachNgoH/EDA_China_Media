from fastapi import HTTPException
from typing import List, Optional
from pydantic import BaseModel
import markdown
from utils import selenium_open_browser
import asyncio
import logging
import json

# Constants (move these to a separate const.py file)
BASE_URL = "https://www.inquirer.net/"
ENCRYPTED_IMG = "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcShpqiBCpiQKcz9fhdV8GSJ3SjXwcMvujfIUVgZIZEfdki7_ctlIpreP4mh"
ERROR_MESSAGE = "Error message here"

class SearchResult(BaseModel):
    link: str
    title: str
    image: Optional[str]
    headline: str
    premium_badge: str

async def search(query: str, sortby: str = "relevance", page: Optional[str] = None, max_pages: int = 9):
    try:
        # Format the search URL
        search_url = f"search?q={query}#gsc.tab=0&gsc.q={query}&gsc.sort={sortby}&gsc.page={page or 1}"
        
        # Get the page content using Selenium
        soup, _ = selenium_open_browser(search_url, base_url=BASE_URL)
        
        data = []
        # Find all search results
        results = soup.select(".gsc-expansionArea .gsc-webResult")

        for result in results:
            title = result.select_one(".gsc-thumbnail-inside a.gs-title").text.strip()
            headline_dom = result.select_one(".gsc-table-result .gs-bidi-start-align")
            link = result.select_one(".gsc-thumbnail-inside a.gs-title")['href']
                        
            # Convert HTML to markdown
            headline = markdown.markdown(str(headline_dom)).strip()
            try:
                image = result.select_one(".gs-image-box img.gs-image")['src']
            except:
                image = None
            premium_badge = "premium" if image == ENCRYPTED_IMG else "not premium"
            
            data.append(SearchResult(
                link=link,
                title=title,
                image=image,
                headline=headline,
                premium_badge=premium_badge
            ))
        
        # Check page limit
        current_page = int(page) if page else 1
        if current_page < max_pages:
            next_page_data = await search(query, sortby, str(current_page + 1), max_pages)
            data.extend(next_page_data["data"])
        
        return {
            "status": 200,
            "important": markdown.markdown("headline"),
            "data": data,
            "pagination": {
                "currentPage": current_page,
                "totalPage": max_pages
            }
        }
        
    except Exception as e:
        logging.error(f"Error in search: {e}", exc_info=True)
        return {
            "status": 404,
            "message": str(e)
        }

if __name__ == "__main__":
    # queries = [('Belt and Road Initiative', 10), ('Community of Shared Future', 10), ('Community of Common Destiny', 4)]
    queries = [('Community of shared destiny', 10), ('Community of common destiny of mankind', 10), ('Asia Infrastructure Investment Bank', 5), ('Global Security Initiative', 5), ('Global Development Initiative', 5), ('Global Civilization Initiative', 5), ('China\'s influence', 5), ('China Soft Power', 5), ('China\'s global strategy', 5), ('China\'s global policy', 5), ('China\'s global influence', 5), ('China\'s global strategy', 5), ('China\'s global policy', 5), ('China\'s global influence', 5), ('China\'s global strategy', 5), ('China\'s global policy', 10), ('China\'s global influence', 10)]
    url_list = []
    for query in queries:
        search_results = asyncio.run(search(query[0], sortby='date', max_pages=query[1]))
        if search_results["status"] == 200: 
            for search_res in search_results["data"]:
                if search_res.link not in url_list:
                    url_list.append({"url": search_res.link})
    
    # save the url_list to a json file
    with open("flp_url_list.json", "w") as f:
        json.dump(url_list, f)
