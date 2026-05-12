import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import os
import re

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
m, d = str(now.month), str(now.day)
m_zero, d_zero = now.strftime("%m"), now.strftime("%d")

url = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchKeyword_u=&district=kanto&desiredConditionArea=kanto&desiredConditionArea=kanto&searchRegionArea=tokyo-23ward&sort=new"

def main():
    old_data = []
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if isinstance(loaded, list): old_data = loaded
            except: old_data = []
    
    old_titles = {item["title"] for item in old_data if isinstance(item, dict) and "title" in item}

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all(["section", "div", "article"], class_=lambda x: x and ("item" in x.lower() or "list" in x.lower()))
    
    current_today_items = []
    new_arrivals = []

    for item in items:
        text = item.get_text(separator=' ', strip=True)
        
        # 当日更新判定（正規表現）
        if re.search(rf"({m}|{m_zero})[月/\.\- ]+({d}|{d_zero})", text) or "本日" in text or "時間前" in text:
            # タイトルとエリアを抽出
            title_tag = item.find(["h1", "h2", "h3"])
            if not title_tag: continue
            
            # 店名に駅名などが混ざる場合、カッコより前だけを抽出するなどの処理
            raw_title = title_tag.get_text(strip=True).replace("NEW", "").strip()
            # 「（」や「駅徒歩」以降を店名から削る
            clean_title = re.split(r'\(|（|駅徒歩', raw_title)[0].strip()

            # エリア情報を探す（住所に関わるキーワードを検索）
            area = "都内23区内"
            for tag in item.find_all(["dd", "p", "span"]):
                tag_text = tag.get_text(strip=True)
                if "区" in tag_text or "市" in tag_text:
                    area = tag_text[:30] # 住所っぽいのを見つけたら採用
                    break

            job_info = {"title": clean_title, "area": area}
            current_today_items.append(job_info)

            if clean_title not in old_titles:
                new_arrivals.append(job_info)

    if new_arrivals:
        print(f"\n★新着あり！（{m}/{d} 更新分）★")
        print("=" * 40)
        for job in new_arrivals:
            print(f"店名: {job['title']}")
            print(f"エリア: {job['area']}")
            print("-" * 40)
    else:
        print(f"\n本日（{m}月{d}日）の新しい更新はありませんでした。")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
