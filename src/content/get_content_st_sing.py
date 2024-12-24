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
    # Remove all links while keeping their text
    links = element.find_elements(By.TAG_NAME, "a")
    for link in links:
        try:
            link.get_attribute('innerHTML')  # Keep the text content
        except:
            continue
    print("Links removed")

    # Remove all images
    images = element.find_elements(By.TAG_NAME, "img")
    for img in images:
        try:
            img.parent.remove()
        except:
            continue
    print("Images removed")
    
    # Get the text content
    content = element.get_attribute('innerHTML')
    
    # Clean up HTML
    content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<[^>]+>', '\n', content)
    
    # Remove extra whitespace and empty lines
    content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())
    
    return content

def get_unprocessed_urls(processed_articles, new_urls):
    # Extract processed URLs into a set for faster lookup
    processed_urls = {article['url'] for article in processed_articles}
    
    # Filter out already processed URLs
    return [item for item in new_urls if item['url'] not in processed_urls]

def scrape_article(driver, url, date):
    try:
        driver.get(url)
        time.sleep(2)
        
        wait = WebDriverWait(driver, 10)
        article = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "article-content")))
        
        # Clean and get the content
        content = clean_content(article)
        
        return {
            "url": url,
            "content": content,
            "date": date
        }
    
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

def main():
    # Load existing processed articles    
    # Load new URLs to process
    with open('url_list_st.json', 'r') as f:
        new_urls = json.load(f)

    # Remove the date before September 2023
    new_urls = [item for item in new_urls if datetime.strptime(item['date'], '%Y-%m-%d') >= datetime(2023, 9, 1)]
    
    processed_articles = []
    driver = setup_driver()
    
    # Process each unprocessed URL
    for i, item in enumerate(new_urls):
        url = item['url']
        print(f"Processing {i+1}/{len(new_urls)}: {url}")
        article_data = scrape_article(driver, url, item['date'])
        if article_data:
            processed_articles.append(article_data)
            
            # Save progress after each successful scrape
            with open('processed_articles_st.json', 'w', encoding='utf-8') as f:
                json.dump(processed_articles, f, ensure_ascii=False, indent=2)
            
            print(f"Saved article data. Total processed: {len(processed_articles)}")
        
        time.sleep(2)  # Be nice to the server
    
    driver.quit()
    print("Processing complete!")

if __name__ == "__main__":
    main()