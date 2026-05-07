import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# ターゲット：飲食店.COM 求人（東京23区・オープニング・新着順）
TARGET_URL = "https://job.inshokuten.com/kanto/work/?searchJobType=opening&searchArea=tokyo23&sort=new"
DATA_FILE = "history.json" # history.jsonに統一して差分管理を確実にします

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-JP;q=0.9",
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    current_jobs = {}
    try:
        print("飲食店求人の情報を精査中...")
        res = requests.get(TARGET_URL, headers=headers, timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 各求人カードを取得
            items = soup.select("article") or soup.select(".itemBox")
            
            for item in items:
                # 1. URLの取得
                link_tag = item.find("a", href=True)
                if not link_tag: continue
                url = "https://job.inshokuten.com" + link_tag['href'].split("?")[0]
                
                # 2. 店名の取得（複数のパターンで試行）
                # 飲食店.comの構造に合わせて、クラス名を複数指定
                name_tag = item.select_one(".itemName") or \
                           item.select_one(".itemTitle") or \
                           item.select_one("h3") or \
                           item.select_one("strong")
                
                name_text = name_tag.get_text(strip=True) if name_tag else "店名不明"
                
                # 3. キャッチコピーやエリア情報の補足
                info_tag = item.select_one(".itemCatch") or item.select_one(".itemText")
                info_text = info_tag.get_text(strip=True)[:60] if info_tag else ""
                
                current_jobs[url] = f"{name_text} | {info_text}"

        print(f"--- 完了：合計{len(current_jobs)}件を検知 ---")

        # 差分チェック
        new_count = 0
        for u, info in current_jobs.items():
            if u not in history:
                print(f"★新着求人：{info}")
                print(f"URL: {u}")
                print("-" * 30)
                new_count += 1
        
        if new_count == 0:
            print("新しい求人情報はありません。")

    except Exception as e:
        print(f"エラー発生: {e}")

    # 履歴を保存
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_jobs if current_jobs else history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
