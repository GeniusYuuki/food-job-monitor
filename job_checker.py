import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import os

# 日本時間(JST)の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
# サイトの表記に合わせて "2026年05月12日" 形式を作成
today_str_kanji = now.strftime("%Y年%m月%d日") 
# "2026/05/12" 形式も一応持っておく
today_str_slash = now.strftime("%Y/%m/%d")

url = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchKeyword_u=&district=kanto&desiredConditionArea=kanto&desiredConditionArea=kanto&searchRegionArea=tokyo-23ward"

def main():
    old_data = []
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    old_data = loaded
            except:
                old_data = []
    
    old_titles = {item["title"] for item in old_data if isinstance(item, dict) and "title" in item}

    # ヘッダーを追加（ブラウザからのアクセスに見せかける）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"エラー: アクセス失敗 {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 求人カード要素を取得
    # 飲食店ドットコムの最新クラス名（p-searchResult__item または section）を広くカバー
    job_items = soup.select(".p-searchResult__item, article, section[class*='item']") 
    
    current_today_items = []
    new_arrivals = []

    for item in job_items:
        # 全テキストを取得して「今日の日付」が含まれているかチェック（一番確実な方法）
        full_text = item.get_text()
        
        if today_str_kanji in full_text or today_str_slash in full_text or "本日" in full_text:
            # 店名取得 (画像に基づき、h3タグや特定のクラスを狙う)
            title_elem = item.select_one(".p-searchResult__title, h3")
            if not title_elem: continue
            title = title_elem.get_text(strip=True).replace("NEW", "").strip()
            
            # エリア取得
            area_elem = item.select_one(".p-searchResult__address, td, dd")
            area = area_elem.get_text(strip=True) if area_elem else "エリア未設定"
            
            link_elem = item.select_one("a")
            link = "https://job.inshokuten.com" + link_elem["href"] if link_elem and link_elem.has_attr('href') else ""
            
            job_info = {
                "title": title,
                "area": area,
                "url": link
            }
            current_today_items.append(job_info)

            if title not in old_titles:
                new_arrivals.append(job_info)

    # 結果の出力
    if new_arrivals:
        print(f"\n★新着あり！（{today_str_kanji} 更新分）★")
        print("=" * 40)
        for job in new_arrivals:
            print(f"店名: {job['title']}")
            print(f"エリア: {job['area']}")
            print(f"URL: {job['url']}")
            print("-" * 40)
    else:
        print(f"\n{today_str_kanji} 更新の新着はありませんでした。")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
