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
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(options=chrome_options)
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

def load_processed_articles():
    try:
        with open('processed_articles_jkt.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_unprocessed_urls(processed_articles, new_urls):
    # Extract processed URLs into a set for faster lookup
    processed_urls = {article['url'] for article in processed_articles}
    
    # Filter out already processed URLs
    return [item for item in new_urls if item['url'] not in processed_urls]

def scrape_article(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        
        wait = WebDriverWait(driver, 10)
        article = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tjp-single")))
        
        # Get the date if available
        try:
            date_element = driver.find_element(By.CLASS_NAME, "post-date")
            date = date_element.text
        except:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Clean and get the content
        content = clean_content(article)
        
        return {
            "url": url,
            "date": date,
            "content": content,
        }
    
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

def main():
    # Load existing processed articles
    processed_articles = load_processed_articles()
    
    # Load new URLs to process
    with open('url_list_jkt.json', 'r') as f:
        new_urls = json.load(f)
    
    # Get unprocessed URLs
    urls_to_process = get_unprocessed_urls(processed_articles, new_urls)
    print(f"Found {len(urls_to_process)} new articles to process")
    
    driver = setup_driver()
    
    # Process each unprocessed URL
    for i, item in enumerate(urls_to_process):
        url = item['url']
        print(f"Processing {i+1}/{len(urls_to_process)}: {url}")
        
        article_data = scrape_article(driver, url)
        if article_data:
            processed_articles.append(article_data)
            
            # Save progress after each successful scrape
            with open('processed_articles_jkt_.json', 'w', encoding='utf-8') as f:
                json.dump(processed_articles, f, ensure_ascii=False, indent=2)
            
            print(f"Saved article data. Total processed: {len(processed_articles)}")
        
        time.sleep(2)  # Be nice to the server
    
    driver.quit()
    print("Processing complete!")

if __name__ == "__main__":
    main()