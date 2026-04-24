import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

BASE_URL = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchRegionArea=tokyo-23ward&searchRegionArea=mitaka-city&page={page}"
DATA_FILE = "history.json"

def get_jobs(url, headers):
    try:
        # セッションを使って人間らしさを出す
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=25)
        
        if res.status_code != 200:
            print(f"アクセス失敗: {res.status_code}")
            return {}
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 店名が入っている要素を総当たりで探す
        page_data = {}
        # 飲食店ドットコムの求人アイテムの共通クラスを狙い撃ち
        items = soup.find_all("div", class_="p-searchResultList__item")
        if not items:
            items = soup.select(".p-searchResult__item")

        for item in items:
            # aタグの中から店名っぽいのを探す
            a_tag = item.find("a", href=True)
            if a_tag and "/kanto/work/detail/" in a_tag['href']:
                job_url = "https://job.inshokuten.com" + a_tag['href'].split("?")[0]
                # テキストを綺麗にする
                job_title = a_tag.get_text(strip=True)
                
                # 所在地情報の取得
                loc = item.find("p", class_="p-searchResult__itemInfoText")
                location = loc.get_text(strip=True) if loc else "場所不明"
                
                if job_title:
                    page_data[job_url] = f"{job_title} （{location}）"
        
        return page_data
    except Exception as e:
        print(f"エラー発生: {e}")
        return {}

def main():
    # 最強の人間なりすましヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
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
        # 待機時間を少し長めに
        time.sleep(random.uniform(7, 12))
        jobs = get_jobs(target_url, headers)
        all_current_jobs.update(jobs)

    count = len(all_current_jobs)
    print(f"--- 完了: 合計{count}件を検知 ---")

    if count == 0:
        print("【警告】0件でした。サイト側のガードを突破できていない可能性があります。")

    any_news = False
    new_links = [link for link in all_current_jobs.keys() if link not in history]
    
    if new_links:
        any_news = True
        print("★新着求人を発見！")
        for link in new_links:
            print(f"  - {all_current_jobs[link]}")
            print(f"    URL: {link}")
    
    if not any_news and count > 0:
        print("新着はありませんでした。")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_current_jobs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
