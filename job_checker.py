import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# 設定：東京23区・三鷹市／オープニング募集
BASE_URL = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchRegionArea=tokyo-23ward&searchRegionArea=mitaka-city&page={page}"
DATA_FILE = "history.json"

def get_jobs(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200: return {}
        
        soup = BeautifulSoup(res.text, "html.parser")
        job_blocks = soup.select("section.p-searchResult__item")
        
        page_data = {}
        for block in job_blocks:
            title_tag = block.select_one("h2.p-searchResult__itemTitle a")
            loc_tag = block.select_one(".p-searchResult__itemInfoText")
            
            if title_tag:
                job_url = "https://job.inshokuten.com" + title_tag.get("href").split("?")[0]
                job_title = title_tag.get_text(strip=True)
                location = loc_tag.get_text(strip=True) if loc_tag else "場所不明"
                page_data[job_url] = f"{job_title} （{location}）"
        return page_data
    except:
        return {}

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Referer": "https://job.inshokuten.com/"
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    all_current_jobs = {}
    for p in [1, 2]:
        print(f"スキャン中: {p}ページ目...")
        target_url = BASE_URL.format(page=p)
        time.sleep(random.uniform(5, 8))
        jobs = get_jobs(target_url, headers)
        all_current_jobs.update(jobs)

    print(f"--- 完了: 合計{len(all_current_jobs)}件を検知 ---")

    any_news = False
    new_links = [link for link in all_current_jobs.keys() if link not in history]
    
    if new_links:
        any_news = True
        print("★【飲食店ドットコム】新着のオープニング募集があります！")
        for link in new_links:
            print(f"  - {all_current_jobs[link]}")
            print(f"    URL: {link}")
    
    if not any_news:
        print("新着求人はありませんでした。")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_current_jobs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
