import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from typing import Dict, Tuple, Any
import time
# BASE_URL = "https://www.thejakartapost.com/"
BASE_URL = "https://www.inquirer.net/"

def scrape_site(endpoint: str) -> Tuple[BeautifulSoup, int]:
    """
    Scrape a website using requests and BeautifulSoup (equivalent to axios + cheerio)
    """
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup, response.status_code
    except Exception as e:
        raise e

def selenium_open_browser(endpoint: str, base_url: str = BASE_URL) -> Tuple[BeautifulSoup, Any]:
    """
    Open a browser using Selenium and wait for specific elements (equivalent to puppeteerOpenBrowser)
    """
    # Configure Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)
        
        # Navigate to the page
        print(f"{base_url}{endpoint}")
        driver.get(f"{base_url}{endpoint}")
        
        # Wait for the specified class with increased timeout
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gsc-result-info")))
        
        # Get the page content
        content = driver.page_source
        
        # Parse with BeautifulSoup (equivalent to cheerio)
        soup = BeautifulSoup(content, 'html.parser')
        
        return soup, driver
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise e
    finally:
        if 'driver' in locals():
            driver.quit()

def check_empty_obj(obj: Dict) -> bool:
    """
    Check if a dictionary is empty
    """
    return len(obj) == 0