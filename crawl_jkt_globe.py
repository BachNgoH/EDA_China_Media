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
BASE_URL = "https://jakartaglobe.id/"
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
    print(f"Full URL: {full_url}")
    driver.get(full_url)
    return driver

async def search(query: str):
    try:
        data = []
        page = 1
        reached_old_news = False
        
        while not reached_old_news:
            # Format the search URL with page parameter
            search_url = f"search/{query}/{page}"
            print(f"Search URL: {search_url}")
            
            # Get the page content using Selenium with the driver
            driver = selenium_open_browser(search_url, base_url=BASE_URL)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, WAIT_TIME)
            
            try:
                # Wait for articles to load
                article_items = wait.until(EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "row.mb-4.position-relative")
                ))
                
                # Check if we have any articles
                if not article_items:
                    break
                    
                print(f"Found {len(article_items)} articles on page {page}")
                
                # Extract data from current page
                for article in article_items:
                    try:
                        # Find the title and link within the article
                        title_element = article.find_element(By.CSS_SELECTOR, "h4.mb-3.text-truncate-2-lines")
                        title = title_element.text.strip()
                        link_element = article.find_element(By.CSS_SELECTOR, "a.stretched-link")
                        link = link_element.get_attribute("href")
                        
                        # Get date
                        date_element = article.find_element(By.CSS_SELECTOR, "span.text-muted.small")
                        date_str = date_element.text.strip()
                        
                        # Parse the date string
                        try:
                            article_date = datetime.strptime(date_str, "%b %d, %Y | %I:%M %p")
                            
                            # Check if we've reached August 2023
                            if article_date.year == 2023 and article_date.month <= 8:
                                print(f"Reached August 2023: {date_str}")
                                reached_old_news = True
                                return {
                                    "status": 200,
                                    "data": data
                                }
                            
                            formatted_date = article_date.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError as e:
                            logging.error(f"Error parsing date {date_str}: {e}")
                            formatted_date = date_str
                        
                        print(f"Found article: {title} - {link} - {formatted_date}")
                        
                        data.append(SearchResult(
                            link=link,
                            title=title,
                            date=formatted_date
                        ))
                        
                    except Exception as e:
                        logging.error(f"Error extracting article data: {e}")
                        continue
                
            finally:
                driver.quit()
                
            page += 1
            
            # Add a small delay between pages
            await asyncio.sleep(2)
        
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
        "Community-of-Shared-Future-China",
        "Belt-and-Road-Initiative",
        "Community-of-Common-Destiny",
        "Community-of-Shared-Destiny",
        "Community-of-Shared-Future",
        "Community-of-Shared-Future-for-Mankind",
        "China's-influence",
        "China-Soft-Power",
        "China's-global-strategy",
        "China's-global-policy",
        "China's-global-influence",
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
                    "title": search_res.title,
                    "date": search_res.date
                })
    
    # save the url_list to a json file
    with open("url_list_jkt_globe.json", "w") as f:
        json.dump(url_list, f)