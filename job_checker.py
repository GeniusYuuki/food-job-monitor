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
    # 1. 前回のデータを読み込む（安全策を強化）
    old_data = []
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if isinstance(loaded, list): # リスト形式の場合のみ読み込む
                    old_data = loaded
            except:
                old_data = []
    
    # 文字列エラー（TypeError）を防ぐためのチェック
    old_titles = set()
    for item in old_data:
        if isinstance(item, dict) and "title" in item:
            old_titles.add(item["title"])

    # 2. サイトから情報を取得
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"エラー: アクセス失敗 {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    job_items = soup.select(".p-searchResult__list .p-searchResult__item") 
    
    current_today_items = []
    new_arrivals = []

    for item in job_items:
        date_elem = item.select_one(".u-text--date")
        title_elem = item.select_one(".p-searchResult__title")
        if not date_elem or not title_elem:
            continue
            
        date_text = date_elem.get_text(strip=True)
        
        # 当日更新判定
        if today_str in date_text or "本日" in date_text or "時間前" in date_text:
            title = title_elem.get_text(strip=True)
            
            area_elem = item.select_one(".p-searchResult__address")
            area = area_elem.get_text(strip=True) if area_elem else "エリア未設定"
            
            link_elem = item.select_one("a")
            link = "https://job.inshokuten.com" + link_elem["href"] if link_elem else ""
            
            job_info = {
                "title": title,
                "area": area,
                "url": link,
                "updated_at": date_text
            }
            current_today_items.append(job_info)

            if title not in old_titles:
                new_arrivals.append(job_info)

    # 3. 結果の出力
    if new_arrivals:
        print("\n★新着あり！★")
        print("=" * 40)
        for job in new_arrivals:
            print(f"店名: {job['title']}")
            print(f"エリア: {job['area']}")
            print(f"URL: {job['url']}")
            print("-" * 40)
    else:
        print("\n新着はありませんでした。")

    # 4. 保存
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
