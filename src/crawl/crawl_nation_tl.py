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
BASE_URL = "https://www.nationthailand.com/search"
WAIT_TIME = 10

class SearchResult(BaseModel):
    link: str
    title: str
    date: str
    blurb: str
    image_url: str | None = None  # Made optional in case some articles don't have images

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

async def search(query: str):
    try:
        data = []
        driver = selenium_open_browser(f"?q={query}", base_url=BASE_URL)
        wait = WebDriverWait(driver, WAIT_TIME)
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        continue_scrolling = True
        
        while continue_scrolling:
            # Wait for articles to load using the updated class selector
            article_items = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.card-h")
            ))
            
            # Extract data from current page
            for article in article_items:
                try:
                    # Get the main link
                    card_link = article.find_element(By.CSS_SELECTOR, "a.card-body")
                    link = card_link.get_attribute("href")
                    
                    # Find the title
                    title_element = article.find_element(By.CSS_SELECTOR, ".text-category-header a.title")
                    title = title_element.text.strip()
                    
                    # Find the date
                    date_element = article.find_element(By.CSS_SELECTOR, ".published-date small")
                    date_str = date_element.text.strip()
                    date = datetime.strptime(date_str, "%A, %B %d, %Y").strftime("%Y-%m-%d")
                    
                    # Get the blurb
                    blurb_element = article.find_element(By.CSS_SELECTOR, "small.blurb")
                    blurb = blurb_element.text.strip()
                    
                    # Try to get the image URL (if it exists)
                    try:
                        image_element = article.find_element(By.CSS_SELECTOR, ".card-image img")
                        image_url = image_element.get_attribute("src")
                    except:
                        image_url = None
                    
                    # Check if we've reached articles before August 2023
                    if datetime.strptime(date, "%Y-%m-%d") < datetime.strptime("2023-08-01", "%Y-%m-%d"):
                        continue_scrolling = False
                        break
                    
                    print(f"Found article: {title} - {date}")
                    
                    data.append(SearchResult(
                        link=link,
                        title=title,
                        date=date,
                        blurb=blurb,
                        image_url=image_url
                    ))
                except Exception as e:
                    logging.error(f"Error extracting article data: {e}")
                    continue
            
            if continue_scrolling:
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for new content to load
                
                # Check if we've reached the bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    continue_scrolling = False
                last_height = new_height
        
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
        search_results = asyncio.run(search(search_query))
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