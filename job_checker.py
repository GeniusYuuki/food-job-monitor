import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# 飲食店.comのターゲットURL
TARGET_URL = "https://job.inshokuten.com/kanto/work/?searchJobType=opening&searchArea=tokyo23&sort=new"
DATA_FILE = "history.json"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    # 1. 前回のデータを読み込む（記憶を呼び起こす）
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = {}
    else:
        history = {}

    current_jobs = {}
    try:
        print("最新の求人情報をスキャン中...")
        res = requests.get(TARGET_URL, headers=headers, timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # 店名が載っていた時の成功したロジックをベースに抽出
            items = soup.select("article") or soup.select(".itemBox")
            
            for item in items:
                link_tag = item.find("a", href=True)
                if not link_tag: continue
                url = "https://job.inshokuten.com" + link_tag['href'].split("?")[0]
                
                # 店名を取得（前回の成功パターン）
                name_tag = item.select_one(".itemName") or item.select_one("h3")
                name_text = name_tag.get_text(strip=True) if name_tag else "店名不明"
                
                current_jobs[url] = name_text

        print(f"--- 完了：合計{len(current_jobs)}件を検知 ---")

        # 2. 差分（新着）だけを表示する
        # 履歴がある場合のみ、比較を行う
        new_items = []
        if history:
            for u, name in current_jobs.items():
                if u not in history:
                    new_items.append((u, name))
        
        if new_items:
            print(f"★【新着】{len(new_items)} 件見つかりました！")
            for u, name in new_items:
                print(f"求人：{name}\nURL: {u}\n" + "-"*20)
        else:
            if not history:
                print("初回実行のため、全件を履歴に保存しました（次回から差分が出ます）")
            else:
                print("新しい求人はありません。")

    except Exception as e:
        print(f"エラー発生: {e}")

    # 3. 今回のデータを保存する（記憶させる）
    # ここで保存しないと、次回もまた「全件新着」になってしまいます
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_jobs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
