import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# Google検索の結果画面（飲食店.com内のオープニング案件）を直接狙います
TARGET_URL = "https://www.google.com/search?q=site:job.inshokuten.com+%22%E3%82%AA%E3%83%BC%E3%83%97%E3%83%8B%E3%83%B3%E3%82%B0%22+%22%E6%9D%B1%E4%BA%AC23%E5%8C%BA%22&tbs=qdr:d"
DATA_FILE = "history.json"

def main():
    # Googleに怪しまれないための「普通のPCブラウザ」設定
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-JP;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    current_jobs = {}
    try:
        print("Google検索経由で最新のオープニング案件を抽出中...")
        time.sleep(random.uniform(5, 10))
        res = requests.get(TARGET_URL, headers=headers, timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Google検索結果の各リンクを解析
            search_results = soup.select("div.g")
            for result in search_results:
                link_tag = result.select_one("a")
                title_tag = result.select_one("h3")
                
                if link_tag and title_tag:
                    url = link_tag['href'].split("&")[0]
                    # 飲食店.comの求人詳細URLのみ抽出
                    if "job.inshokuten.com/kanto/work/detail/" in url:
                        name = title_tag.get_text(strip=True).replace(" | 飲食店.COM", "")
                        current_jobs[url] = name

        print(f"--- 完了：合計{len(current_jobs)}件を検知 ---")

        new_count = 0
        for u, name in current_jobs.items():
            if u not in history:
                print(f"★新着オープニング求人：{name}")
                print(f"URL: {u}")
                print("-" * 30)
                new_count += 1
        
        if new_count == 0:
            print("24時間以内に更新された新しい求人は見つかりませんでした。")

    except Exception as e:
        print(f"エラー発生: {e}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_jobs if current_jobs else history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
