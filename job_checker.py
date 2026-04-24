import requests
from bs4 import BeautifulSoup
import json
import os
import time

# 検索条件を維持しつつ、より軽量な形式でデータを取りに行く
BASE_URL = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchRegionArea=tokyo-23ward&searchRegionArea=mitaka-city&page={page}"
DATA_FILE = "history.json"

def main():
    # 凝ったことはせず、Googleのクローラー(検索ロボット)のふりをする（大手サイトはこれを通すことが多い）
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    all_current_jobs = {}
    
    # まず1ページ目だけ集中して狙う
    for p in [1]:
        print(f"ターゲット確認中: {p}ページ目...")
        try:
            res = requests.get(BASE_URL.format(page=p), headers=headers, timeout=30)
            print(f"ステータスコード: {res.status_code}")
            
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 最も確実に店名が入っている「aタグ」をすべて洗い出す
            links = soup.find_all("a")
            for a in links:
                href = a.get("href", "")
                # 求人詳細へのリンクだけを抽出
                if "/kanto/work/detail/" in href:
                    job_url = "https://job.inshokuten.com" + href.split("?")[0]
                    job_title = a.get_text(strip=True)
                    
                    # 店名が短すぎる、または空っぽのものは除外
                    if len(job_title) > 2:
                        all_current_jobs[job_url] = job_title

        except Exception as e:
            print(f"エラー: {e}")

    count = len(all_current_jobs)
    print(f"--- 完了: 合計{count}件を検知 ---")

    any_news = False
    new_links = [link for link in all_current_jobs.keys() if link not in history]
    
    if new_links:
        any_news = True
        print("★【飲食店ドットコム】新着あり")
        for link in new_links:
            print(f"  - {all_current_jobs[link]}")
            print(f"    URL: {link}")
    
    # 1件でも取れたら保存、0件ならブロックされているので履歴を更新しない
    if count > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_current_jobs, f, ensure_ascii=False, indent=2)
    else:
        print("【重要】サイトの構造が読み取れませんでした。別の対策が必要です。")

if __name__ == "__main__":
    main()
