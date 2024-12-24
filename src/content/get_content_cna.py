from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import markdown
import re
import os
import logging
from datetime import datetime

def setup_driver():
    """
    Opens a Chrome browser using Selenium WebDriver with specified options.
    
    Args:
        url (str): The URL path or full URL to open
        base_url (str, optional): Base URL to prepend to the url parameter
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    # Add headless mode
    options.add_argument('--headless')
    
    # Optimize performance
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-features=NetworkService')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images loading
    options.page_load_strategy = 'eager'
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)  # Reduced timeout
    driver.set_script_timeout(20)     # Reduced timeout
    
    return driver


def clean_content(element):
    # Get the text content directly without handling links/images separately
    content = element.get_attribute('innerHTML')
    
    # Clean up HTML more efficiently
    content = re.sub(r'<(script|style)[^>]*>.*?</\1>|<[^>]+>', '\n', content, flags=re.DOTALL)
    
    # Remove extra whitespace and empty lines
    return '\n'.join(line.strip() for line in content.split('\n') if line.strip())

def get_unprocessed_urls(processed_articles, new_urls):
    # Extract processed URLs into a set for faster lookup
    processed_urls = {article['url'] for article in processed_articles}
    
    # Filter out already processed URLs
    return [item for item in new_urls if item['url'] not in processed_urls]

def scrape_article(driver, url):
    try:
        driver.get(url)
        # Reduced sleep time
        time.sleep(1)
        
        wait = WebDriverWait(driver, 5)  # Reduced wait time
        article = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "content")))
        
        date = article.find_element(By.CLASS_NAME, "article-publish").text.strip()
        date = date.split("(")[0].strip()
        date = datetime.strptime(date, "%d %b %Y %I:%M%p").strftime("%Y-%m-%d")
        
        content = clean_content(article)
        return {
            "url": url,
            "date": date,
            "content": content,
        }
    
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}", exc_info=True)
        return None

def main():
    # Get unprocessed URLs
    with open('url_list_cna.json', 'r') as f:
        urls_to_process = json.load(f)
        
    driver = setup_driver()
    processed_articles = []

    # Process each unprocessed URL
    for i, item in enumerate(urls_to_process):
        url = item['url']
        print(f"Processing {i+1}/{len(urls_to_process)}: {url}")
        
        article_data = scrape_article(driver, url)
        if article_data:
            processed_articles.append(article_data)
            
            # Save progress after each successful scrape
            with open('processed_articles_cna.json', 'w', encoding='utf-8') as f:
                json.dump(processed_articles, f, ensure_ascii=False, indent=2)
            
            print(f"Saved article data. Total processed: {len(processed_articles)}")
        
        time.sleep(2)  # Be nice to the server
    
    driver.quit()
    print("Processing complete!")

if __name__ == "__main__":
    main()