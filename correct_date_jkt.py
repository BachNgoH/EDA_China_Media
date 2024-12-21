from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
from datetime import datetime

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def convert_date_format(date_str):
    try:
        # Parse the date string "Mon, December 7, 2020" format
        date_obj = datetime.strptime(date_str, "%a, %B %d, %Y")
        # Convert to "YYYY-MM-DD" format
        return date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error converting date {date_str}: {str(e)}")
        return date_str

def get_article_date(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        
        # Find the meta content items
        meta_content_items = driver.find_elements(By.CLASS_NAME, "tjp-meta__content-item")
        
        # Look for the date in the content items
        for item in meta_content_items:
            if any(month in item.text for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                                                  'July', 'August', 'September', 'October', 'November', 'December']):
                return convert_date_format(item.text.strip())
        return None
    except Exception as e:
        print(f"Error getting date for {url}: {str(e)}")
        return None

def update_article_dates():
    # Load existing processed articles
    try:
        with open('processed_articles_jkt__classified.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
            articles = [article for article in articles if article['is_related'] == True]
    except FileNotFoundError:
        print("processed_articles_jkt.json not found!")
        return
    
    print(f"Found {len(articles)} articles to update")
    
    # Setup the driver
    driver = setup_driver()
    
    # Counter for modified dates
    modified_count = 0
    
    # Update dates for each article
    try:
        for i, article in enumerate(articles):
            print(f"\nProcessing {i+1}/{len(articles)}: {article['url']}")
            print(f"Old date: {article['date']}")
            
            new_date = get_article_date(driver, article['url'])
            
            if new_date and new_date != article['date']:
                article['date'] = new_date
                modified_count += 1
                print(f"Updated date to: {new_date}")
            else:
                print("Date unchanged or couldn't fetch new date")
            
            # Save progress after each 10 articles
            if (i + 1) % 10 == 0:
                with open('processed_articles_jkt_updated.json', 'w', encoding='utf-8') as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                print(f"Progress saved. Processed {i+1}/{len(articles)} articles")
            
            time.sleep(2)  # Be nice to the server
            
    except Exception as e:
        print(f"Error during processing: {str(e)}")
    finally:
        # Save final results
        with open('processed_articles_jkt_updated.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        driver.quit()
    
    print(f"\nProcessing complete!")
    print(f"Modified {modified_count} dates")
    print(f"Saved to 'processed_articles_jkt_updated.json'")

if __name__ == "__main__":
    update_article_dates()