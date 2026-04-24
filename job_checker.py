import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# 設定：東京23区・三鷹市／オープニング募集
BASE_URL = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchRegionArea=tokyo-23ward&searchRegionArea=mitaka-city&page={page}"
DATA_FILE = "history.json"

def main():
    # Googlebotになりすましてサイトのガードを突破する
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
    
    # 1ページ目と2ページ目をスキャン（最大40件）
    for p in [1, 2]:
        print(f"ターゲット確認中: {p}ページ目...")
        try:
            time.sleep(random.uniform(5, 8))
            res = requests.get(BASE_URL.format(page=p), headers=headers, timeout=30)
            
            if res.status_code != 200:
                print(f"ページ{p}の取得に失敗しました (Status: {res.status_code})")
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 全てのリンクから求人詳細（/detail/）を探し、その中の店名を特定する
            links = soup.find_all("a")
            for a in links:
                href = a.get("href", "")
                if "/kanto/work/detail/" in href:
                    # URLを正規化
                    job_url = "https://job.inshokuten.com" + href.split("?")[0]
                    
                    # aタグの中にh2（店名）があればそれを、なければaタグ自体のテキストを取得
                    name_elem = a.find("h2") or a
                    job_title = name_elem.get_text(strip=True)
                    
                    # 「求人詳細へ」などの不要な文字を弾き、純粋な店名だけを保存
                    if len(job_title) > 2 and job_title != "求人詳細へ":
                        all_current_jobs[job_url] = job_title

        except Exception as e:
            print(f"エラー発生: {e}")

    count = len(all_current_jobs)
    print(f"--- 完了: 合計{count}件の有効な求人を検知 ---")

    any_news = False
    new_links = [link for link in all_current_jobs.keys() if link not in history]
    
    if new_links:
        any_news = True
        print("★【求人飲食店ドットコム】新着のオープニング案件を発見しました！")
        for link in new_links:
            print(f"  - {all_current_jobs[link]}")
            print(f"    URL: {link}")
    
    # 1件でも取れていれば履歴を更新。0件ならブロックされた可能性があるので更新しない。
    if count > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_current_jobs, f, ensure_ascii=False, indent=2)
    else:
        print("【警告】店舗データが取得できませんでした。")

if __name__ == "__main__":
    main()
