import os
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

URL = "https://tnstats.dev/season1/fyscchannels"
FOLDER_NAME = "HistoryDataLilianaS1"
CSV_FILE_PATH = os.path.join(FOLDER_NAME, "liliana_season1_history.csv")

os.makedirs(FOLDER_NAME, exist_ok=True)

# Set up CSV header if file doesn't exist
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "datetime", "channel_id", "name", "subs", "avatar"])

# Configure headless Chrome browser
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

rows_to_write = []
now_ts = int(datetime.now().timestamp())
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    driver.get(URL)
    # Wait up to 15 seconds for dynamic content to render
    time.sleep(5)

    # Find images or channel elements loaded by JS
    images = driver.find_elements(By.TAG_NAME, "img")
    
    for img in images:
        avatar = img.get_attribute("src") or ""
        name = img.get_attribute("alt") or ""
        
        # Grab parent element text to extract subscriber count
        try:
            parent = img.find_element(By.XPATH, "..")
            text = parent.text
        except Exception:
            text = ""

        digits = ''.join(filter(str.isdigit, text))
        subs = int(digits) if digits else 0

        if name:
            rows_to_write.append([now_ts, now_str, name, name, subs, avatar])

    # Fallback to page source parsing if image tags weren't structured
    if not rows_to_write:
        items = driver.find_elements(By.XPATH, "//*[contains(@class, 'channel') or contains(@class, 'card') or contains(@class, 'item')]")
        for item in items:
            text = item.text
            try:
                img_el = item.find_element(By.TAG_NAME, "img")
                avatar = img_el.get_attribute("src") or ""
                name = img_el.get_attribute("alt") or item.text.split('\n')[0]
            except Exception:
                avatar = ""
                name = ""
            
            digits = ''.join(filter(str.isdigit, text))
            subs = int(digits) if digits else 0
            if name:
                rows_to_write.append([now_ts, now_str, name, name, subs, avatar])

except Exception as e:
    print(f"Scraping error: {e}")
finally:
    driver.quit()

# Write extracted data to CSV
if rows_to_write:
    with open(CSV_FILE_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)
    print(f"Successfully recorded {len(rows_to_write)} channels.")
else:
    print("No channels found on page render.")
