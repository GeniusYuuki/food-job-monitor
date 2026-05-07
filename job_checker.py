import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

TARGET_URL = "https://job.inshokuten.com/kanto/work/?searchJobType=opening&searchArea=tokyo23&sort=new"
DATA_FILE = "history.json"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    current_jobs = {}
    try:
        print("求人情報を詳細スキャン中...")
        res = requests.get(TARGET_URL, headers=headers, timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 求人項目をより広範囲に探す
            items = soup.find_all(["article", "div"], class_=lambda x: x and ("item" in x or "list" in x))
            
            for item in items:
                link_tag = item.find("a", href=True)
                if not link_tag or "/kanto/work/detail/" not in link_tag['href']:
                    continue
                    
                url = "https://job.inshokuten.com" + link_tag['href'].split("?")[0]
                if url in current_jobs: continue

                # 【店名取得の執念設定】
                # クラス名、タグ、親要素、兄弟要素、あらゆる可能性から店名を探す
                name = "店名不明"
                
                # 候補1: クラス名（想定されるものすべて）
                name_tag = item.select_one(".itemName, .itemTitle, .title, h3, .shopName, .companyName")
                
                # 候補2: クラス名がなくても、リンク自体のテキスト（空でなければ）
                if not name_tag or not name_tag.get_text(strip=True):
                    name_tag = link_tag
                
                if name_tag:
                    name = name_tag.get_text(strip=True)
                
                # もし求人タイトルのような長い文章が取れてしまった場合、最初の部分だけ切り出す
                name = name.split("\n")[0][:40]

                # 補足情報
                catch = item.select_one(".itemCatch, .text, p")
                catch_text = f" | {catch.get_text(strip=True)[:40]}" if catch else ""
                
                current_jobs[url] = f"{name}{catch_text}"

        print(f"--- 完了：合計{len(current_jobs)}件を検知 ---")

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

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_jobs if current_jobs else history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
