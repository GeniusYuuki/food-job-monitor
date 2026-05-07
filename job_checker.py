import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# ターゲット：飲食店.COM 求人（東京23区・オープニングスタッフ・新着順）
TARGET_URL = "https://job.inshokuten.com/kanto/work/?searchJobType=opening&searchArea=tokyo23"
DATA_FILE = "job_history.json"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-JP;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    # 履歴の読み込み
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    current_jobs = {}
    try:
        print("飲食店求人の新着（オープニング）をスキャン中...")
        time.sleep(random.uniform(5, 10))
        res = requests.get(TARGET_URL, headers=headers, timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 求人カードを抽出（サイトの構造に合わせて調整）
            # 飲食店.COMの場合、各求人は article や div.jobItem に入っていることが多い
            items = soup.select(".itemBox") or soup.select("article")
            
            for item in items:
                link_tag = item.find("a", href=True)
                if link_tag and "/kanto/work/detail/" in link_tag['href']:
                    # URLを整形
                    url = "https://job.inshokuten.com" + link_tag['href'].split("?")[0]
                    
                    # 店名とキャッチコピーを取得
                    title = item.select_one(".itemName") or item.select_one("h3")
                    catch = item.select_one(".itemCatch") or item.select_one(".text")
                    
                    name_text = title.get_text(strip=True) if title else "店名不明"
                    catch_text = catch.get_text(strip=True)[:50] if catch else ""
                    
                    current_jobs[url] = f"{name_text} | {catch_text}"

        print(f"--- 完了：合計{len(current_jobs)}件を検知 ---")

        # 差分（新着）チェック
        new_items = [u for u in current_jobs.keys() if u not in history]
        if new_items:
            print(f"★【新着求人】{len(new_items)} 件のオープニング募集が見つかりました！")
            for u in new_items:
                print(f"求人：{current_jobs[u]}")
                print(f"URL: {u}")
                print("-" * 30)
        else:
            print("新しい求人情報はありません。")

    except Exception as e:
        print(f"エラー発生: {e}")

    # 履歴を保存
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_jobs if current_jobs else history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
