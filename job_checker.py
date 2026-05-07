import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import re

# 飲食店.comのターゲットURL
TARGET_URL = "https://job.inshokuten.com/kanto/work/?searchJobType=opening&searchArea=tokyo23&sort=new"
DATA_FILE = "history.json"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    # 履歴の読み込み（保存されている求人IDのリストを読み込む）
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
    else:
        history = []

    current_job_ids = []
    new_jobs = []

    try:
        print("求人ID（末尾数字）で新着をスキャン中...")
        res = requests.get(TARGET_URL, headers=headers, timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.select("article") or soup.select(".itemBox")
            
            for item in items:
                link_tag = item.find("a", href=True)
                if not link_tag: continue
                
                url = "https://job.inshokuten.com" + link_tag['href'].split("?")[0]
                
                # URLから末尾の数字（求人ID）を抜き出す
                match = re.search(r'/(\.d+)$', url) or re.search(r'/(\d+)$', url)
                if match:
                    job_id = match.group(1)
                    current_job_ids.append(job_id)
                    
                    # 履歴にこのIDがなければ「新着」！
                    if job_id not in history:
                        new_jobs.append(url)

        print(f"--- 完了：合計{len(current_job_ids)}件を検知 ---")

        if new_jobs:
            print(f"★【新着】{len(new_jobs)} 件見つかりました！")
            for url in new_jobs:
                print(f"求人：店名不明（ID: {url.split('/')[-1]}）")
                print(f"URL: {url}")
                print("-" * 20)
        else:
            print("新しい求人はありません。")

    except Exception as e:
        print(f"エラー発生: {e}")

    # 今回検知したIDリストを保存して、次回の比較に使う
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_job_ids, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
