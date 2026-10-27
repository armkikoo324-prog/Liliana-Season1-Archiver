import os
import csv
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

URL = "https://tnstats.dev/season1/fyscchannels"
FOLDER_NAME = "HistoryDataLilianaS1"
CSV_FILE_PATH = os.path.join(FOLDER_NAME, "liliana_season1_history.csv")

os.makedirs(FOLDER_NAME, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "datetime", "channel_id", "name", "subs", "avatar"])

try:
    response = requests.get(URL, headers=headers, timeout=15)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        now_ts = int(datetime.now().timestamp())
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        items = soup.find_all(['div', 'tr'], class_=lambda x: x and ('channel' in x.lower() or 'card' in x.lower() or 'item' in x.lower()))
        if not items:
            items = soup.find_all('div')

        count = 0
        with open(CSV_FILE_PATH, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for item in items:
                name_el = item.find(['h3', 'h4', 'span', 'a'], class_=lambda x: x and 'name' in x.lower())
                subs_el = item.find(['span', 'p', 'div'], class_=lambda x: x and ('sub' in x.lower() or 'count' in x.lower()))
                img_el = item.find('img')

                if name_el and subs_el:
                    name = name_el.get_text(strip=True)
                    subs_text = subs_el.get_text(strip=True).replace(',', '').replace('subs', '')
                    try:
                        subs = int(''.join(filter(str.isdigit, subs_text)))
                    except ValueError:
                        subs = 0

                    avatar = img_el['src'] if img_el and img_el.has_attr('src') else ''
                    channel_id = img_el.get('alt', name) if img_el else name

                    writer.writerow([now_ts, now_str, channel_id, name, subs, avatar])
                    count += 1
        print(f"Recorded {count} channels.")
    else:
        print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
