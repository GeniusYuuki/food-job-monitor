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
        if res.status_code != 200:
            print(f"アクセス失敗: {res.status_code}")
            return {}
        
        soup = BeautifulSoup(res.text, "html.parser")
        # 店舗カードを広く探す
        job_blocks = soup.find_all("div", class_="p-searchResultList__item") or soup.find_all("section", class_="p-searchResult__item")
        
        page_data = {}
        for block in job_blocks:
            # 店名・タイトルの取得
            title_tag = block.find("h2", class_="p-searchResult__itemTitle")
            if title_tag and title_tag.find("a"):
                a_tag = title_tag.find("a")
                job_url = "https://job.inshokuten.com" + a_tag.get("href").split("?")[0]
                job_title = a_tag.get_text(strip=True)
                
                # 所在地/最寄駅の取得
                loc_tag = block.find("p", class_="p-searchResult__itemInfoText")
                location = loc_tag.get_text(strip=True) if loc_tag else "場所不明"
                
                page_data[job_url] = f"{job_title} （{location}）"
        
        return page_data
    except Exception as e:
        print(f"エラー詳細: {e}")
        return {}

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        time.sleep(random.uniform(3, 6))
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
