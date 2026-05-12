import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import os

# 日本時間(JST)の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
today_str = now.strftime("%Y/%m/%d")

url = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchKeyword_u=&district=kanto&desiredConditionArea=kanto&desiredConditionArea=kanto&searchRegionArea=tokyo-23ward"

def main():
    # 1. 前回のデータを読み込む
    old_data = []
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            try:
                old_data = json.load(f)
            except json.JSONDecodeError:
                old_data = []
    
    # 前回の店名リストを作成（差分比較用）
    old_titles = {item["title"] for item in old_data}

    # 2. サイトから最新情報を取得
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    job_items = soup.select(".p-searchResult__list .p-searchResult__item") 
    
    current_today_items = []
    new_arrivals = []

    for item in job_items:
        date_elem = item.select_one(".u-text--date")
        if not date_elem: continue
        
        date_text = date_elem.get_text(strip=True)
        
        # 「当日更新」の判定
        if today_str in date_text or "本日" in date_text or "時間前" in date_text:
            title = item.select_one(".p-searchResult__title").get_text(strip=True)
            # エリア情報の取得（飲食店ドットコムの構造に合わせた例）
            area_elem = item.select_one(".p-searchResult__address")
            area = area_elem.get_text(strip=True) if area_elem else "エリア不明"
            
            link = "https://job.inshokuten.com" + item.select_one("a")["href"]
            
            job_info = {
                "title": title,
                "area": area,
                "url": link,
                "updated_at": date_text
            }
            current_today_items.append(job_info)

            # 前回のリストにいなければ「新着」とする
            if title not in old_titles:
                new_arrivals.append(job_info)

    # 3. 結果の出力
    if new_arrivals:
        print("★新着あり！★")
        print("-" * 30)
        for job in new_arrivals:
            print(f"店名: {job['title']}")
            print(f"エリア: {job['area']}")
            print(f"URL: {job['url']}")
            print("-" * 30)
    else:
        print("新着はありませんでした。")

    # 4. 履歴を更新（当日分のみ保存）
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
