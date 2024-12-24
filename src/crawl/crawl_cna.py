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
BASE_URL = "https://www.channelnewsasia.com/"
WAIT_TIME = 2

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
    
    # Add these new options to improve stability
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-features=NetworkService')
    options.add_argument('--disable-dev-shm-usage')
    options.page_load_strategy = 'eager'  # Don't wait for all resources to load
    
    # Create driver with longer timeout settings
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)  # Seconds
    driver.set_script_timeout(30)     # Seconds
    
    # Construct full URL
    full_url = f"{base_url}{url}" if base_url else url
    
    driver.get(full_url)
    return driver

async def search(query: str):
    try:
        data = []
        start = 1
        reached_old_news = False
        
        while not reached_old_news:
            # Format the search URL with start parameter
            search_url = f"search?q={query}&page={start}"
            
            # Get the page content using Selenium with the driver
            driver = selenium_open_browser(search_url, base_url=BASE_URL)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, WAIT_TIME)
            
            # Wait for articles to load using the new class selector
            article_items = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "li.ais-Hits-item")
            ))
            print(f"Found {len(article_items)} articles")
            if not article_items:
                break
                
            # Extract data from current page
            for article in article_items:
                try:
                    # Find the title and link within the article using updated selectors
                    title_element = article.find_element(By.CSS_SELECTOR, "h6.hit-name a")
                    title = title_element.text.strip()
                    link = title_element.get_attribute("href")
                    
                    # Find the date with updated selector
                    date_element = article.find_element(By.CSS_SELECTOR, "div.hit-date")
                    date_str = date_element.text.strip()
                    print(f"Date: {date_str}")
                    
                    
                    # Check if the article is 2 or more years old
                    if "2 years ago" in date_str.strip():
                        print(f"Reached old news: {date_str}")
                        reached_old_news = True
                        return {
                            "status": 200,
                            "data": data
                        }
                        
                    
                    print(f"Found article: {title} - {link} - {date_str}")
                    
                    data.append(SearchResult(
                        link=link,
                        title=title,
                        date=""
                    ))
                except Exception as e:
                    logging.error(f"Error extracting article data: {e}")
                    continue
            
            driver.quit()
            
            if reached_old_news:
                return {
                    "status": 200,
                    "data": data
                }
                
            start += 1
            
            # Add a small delay to avoid overwhelming the server
            await asyncio.sleep(1)
        
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
        "Community of Shared Future China",
        "Belt and Road Initiative",
        "Community of Common Destiny",
        "Community of Shared Destiny",
        "Community of Shared Future",
        "Community of Shared Future for Mankind",
        "China's influence",
        "China Soft Power",
        "China's global strategy",
        "China's global policy",
        "China's global influence",
        "ASEAN Perception",
        "China Dream"
    }
    
    url_list = []
    for search_query in search_queries:
        search_results = asyncio.run(search(search_query))
        if search_results["status"] != 200:
            print(f"Error in search: {search_results['message']}")
            continue
        for search_res in search_results["data"]:
            # check if the url is already in the url_list
            if search_res.link not in [item["url"] for item in url_list]:
                url_list.append({
                    "url": search_res.link, 
                })
    
    # save the url_list to a json file
    with open("url_list_cna.json", "w") as f:
        json.dump(url_list, f)