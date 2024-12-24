from pydantic import BaseModel
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import asyncio
import logging
import json
import time
from selenium import webdriver
from datetime import datetime

# Constants
BASE_URL = "https://search.bangkokpost.com/"
WAIT_TIME = 10

class SearchResult(BaseModel):
    link: str
    title: str
    date: str

def selenium_open_browser(url: str, base_url: str = None) -> webdriver.Chrome:
    """
    Opens a Chrome browser using Selenium WebDriver with specified options.
    
    Args:
        url (str): The URL path or full URL to open
        base_url (str, optional): Base URL to prepend to the url parameter
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    
    # Construct full URL
    full_url = f"{base_url}{url}" if base_url else url
    
    driver.get(full_url)
    return driver

async def search(query: str, page_limit: int = 90):
    try:
        data = []
        # Iterate through pages using start parameter (0 to page_limit in steps of 10)
        for start in range(0, page_limit, 10):
            # Format the search URL with start parameter
            search_url = f"search/result?start={start}&q={query}&category=all&refinementFilter=&sort=newest&rows=10&publishedDate="
            
            # Get the page content using Selenium with the driver
            driver = selenium_open_browser(search_url, base_url=BASE_URL)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, WAIT_TIME)
            
            # Wait for articles to load using the new class selector
            article_items = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.search-listnews--row")
            ))
            
            # Extract data from current page
            for article in article_items:
                try:
                    # Find the title and link within the article
                    title_element = article.find_element(By.CSS_SELECTOR, ".mk-listnew--title h3 a")
                    title = title_element.text.strip()
                    link = title_element.get_attribute("href")
                    
                    # Find the date in the publication info
                    date_element = article.find_element(By.CSS_SELECTOR, ".mk-listnew--title p span")
                    date_str = date_element.text.replace("Published on ", "").strip()
                    # Convert date from MM/DD/YYYY to YYYY-MM-DD
                    date = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                    
                    print(f"Found article: {title} - {link} - {date}")
                    
                    data.append(SearchResult(
                        link=link,
                        title=title,
                        date=date
                    ))
                except Exception as e:
                    logging.error(f"Error extracting article data: {e}")
                    continue
            
            driver.quit()
        
        return {
            "status": 200,
            "data": data
        }
        
    except Exception as e:
        logging.error(f"Error in search: {e}", exc_info=True)
        if 'driver' in locals():
            driver.quit()
        return {
            "status": 404,
            "message": str(e)
        }

if __name__ == "__main__":

    search_queries = {
        "Community of Shared Future China": 60,
        "Belt and Road Initiative": 90,
        "Community of Common Destiny": 90,
        "Community of Shared Destiny": 90,
        "Community of Shared Future": 90,
        "Community of Shared Future for Mankind": 90,
        "China's influence": 90,
        "China Soft Power": 90,
        "China's global strategy": 90,
        "China's global policy": 90,
        "China's global influence": 90,
        "ASEAN Perception": 90,
        "China Dream": 90
    }
    
    url_list = []
    for search_query, page_limit in search_queries.items():
        search_results = asyncio.run(search(search_query, page_limit))
        if search_results["status"] != 200:
            print(f"Error in search: {search_results['message']}")
            continue
        for search_res in search_results["data"]:
            # check if the url is already in the url_list
            if search_res.link not in [item["url"] for item in url_list]:
                url_list.append({
                    "url": search_res.link, 
                    "date": search_res.date
                })
    
    # save the url_list to a json file
    with open("bk_url_list.json", "w") as f:
        json.dump(url_list, f) 