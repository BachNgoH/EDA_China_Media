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
BASE_URL = "https://www.straitstimes.com/search"
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
    
    driver = webdriver.Chrome(options=options)
    
    # Construct full URL
    full_url = f"{base_url}{url}" if base_url else url
    
    driver.get(full_url)
    return driver

async def search(query: str):
    try:
        # Format the search URL
        search_url = f"?searchkey={query}"
        
        # Get the page content using Selenium with the driver
        driver = selenium_open_browser(search_url, base_url=BASE_URL)
        
        # Wait for the "Within a Year" link and click it
        wait = WebDriverWait(driver, WAIT_TIME)
        year_filter = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'within three years')]")))
        year_filter.click()
        
        # Wait for the page to load after filter
        time.sleep(3)
        
        data = []
        while True:
            # Wait for articles to load
            article_links = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a[onmousedown*='queryly.util.trackClick']")
            ))
            
            # Extract data from current page
            for article in article_links:
                try:
                    # Get the href attribute for the link
                    link = article.get_attribute("href")
                    # Find the title div within the article
                    title = article.find_element(By.CLASS_NAME, "queryly_item_title").text.strip()
                    date = article.find_element(By.CLASS_NAME, "queryly_item_description").text.strip().split("...")[0]
                    print(f"Found article: {title} - {link} - {date}")
                    
                    data.append(SearchResult(
                        link=link,
                        title=title,
                        date=date
                    ))
                except Exception as e:
                    logging.error(f"Error extracting article data: {e}")
                    continue

            try:
                # Find the next button using a more specific XPath
                next_button = driver.find_element(
                    By.XPATH, 
                    "//a[.//h2[contains(text(), 'Next Page')]]"
                )
                if not next_button.is_displayed():
                    break
                # Use JavaScript to click the button since it uses onclick
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)  # Increased wait time for page load
            except Exception as e:
                logging.info(f"No more pages to load: {e}")
                break
        
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

    search_queries = [
        "Belt and Road Initiative",
        "Community of Common Destiny",
        "Community of Shared Future",
        "Community of Common Destiny of Mankind",
        "Asia Infrastructure Investment Bank",
        "Global Security Initiative",
        "Global Development Initiative",
        "Global Civilization Initiative",
        "China's Influence",
        "China Soft Power",
        "China's Global Strategy",
        "China's Global Policy",
        "China's Global Influence",
        "China's Dream",
        "ASEAN Perception"
    ]   
    url_list = []
    for search_query in search_queries:
        search_results = asyncio.run(search(search_query))
        if search_results["status"] != 200:
            continue
        for search_res in search_results["data"]:
            url_list.append({
                "url": search_res.link, 
                "date": datetime.strptime(search_res.date.strip(), '%b %d, %Y').strftime('%Y-%m-%d')
            })
    
    # save the url_list to a json file
    with open("url_list_st.json", "w") as f:
        json.dump(url_list, f) 