import os
import csv
import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

URL = "https://tnstats.dev/season1/fyscchannels"
FOLDER_NAME = "HistoryDataLilianaS1"
CSV_FILE_PATH = os.path.join(FOLDER_NAME, "liliana_season1_history.csv")

os.makedirs(FOLDER_NAME, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "datetime", "channel_id", "name", "subs", "avatar"])

now_ts = int(datetime.now().timestamp())
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

rows_to_write = []

# Try 1: Check direct API endpoint if available
api_url = "https://tnstats.dev/api/season1/fyscchannels"
try:
    api_res = requests.get(api_url, headers=headers, timeout=10)
    if api_res.status_code == 200:
        data = api_res.json()
        channels = data if isinstance(data, list) else data.get("channels", data.get("data", []))
        for item in channels:
            cid = item.get("id", item.get("channel_id", item.get("name", "")))
            name = item.get("name", item.get("title", ""))
            subs = item.get("subs", item.get("subscribers", item.get("count", 0)))
            avatar = item.get("avatar", item.get("image", item.get("pfp", "")))
            if name:
                rows_to_write.append([now_ts, now_str, cid, name, subs, avatar])
except Exception as e:
    print(f"API attempt note: {e}")

# Try 2: HTML fallback parsing if API didn't return data
if not rows_to_write:
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Search for embedded JSON data inside <script> tags
            for script in soup.find_all('script'):
                if script.string and ('subs' in script.string or 'channels' in script.string):
                    json_matches = re.findall(r'(\[.*?\]|\{.*?\})', script.string)
                    for match in json_matches:
                        try:
                            parsed = json.loads(match)
                            if isinstance(parsed, list):
                                for item in parsed:
                                    if isinstance(item, dict) and ('name' in item or 'subs' in item):
                                        name = item.get('name', '')
                                        subs = item.get('subs', item.get('subscribers', 0))
                                        avatar = item.get('avatar', item.get('image', ''))
                                        cid = item.get('id', name)
                                        if name:
                                            rows_to_write.append([now_ts, now_str, cid, name, subs, avatar])
                        except Exception:
                            continue

            # Fallback DOM element loop
            if not rows_to_write:
                elements = soup.find_all(True)
                for el in elements:
                    text = el.get_text(strip=True)
                    img_el = el.find('img')
                    if img_el and any(char.isdigit() for char in text):
                        name = img_el.get('alt', '').strip()
                        avatar = img_el.get('src', '')
                        digits = ''.join(filter(str.isdigit, text))
                        if name and digits:
                            rows_to_write.append([now_ts, now_str, name, name, int(digits), avatar])

    except Exception as e:
        print(f"HTML parsing error: {e}")

# Write results
if rows_to_write:
    with open(CSV_FILE_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)
    print(f"Successfully recorded {len(rows_to_write)} channels.")
else:
    print("No channel data extracted this run.")
