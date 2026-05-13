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

target_url = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchKeyword_u=&district=kanto&desiredConditionArea=kanto&desiredConditionArea=kanto&searchRegionArea=tokyo-23ward&sort=new"

def main():
    old_data = []
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    old_data = [item for item in loaded if isinstance(item, dict) and "title" in item]
            except:
                old_data = []
    
    old_titles = {item["title"] for item in old_data}

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.select("section, article, .p-searchResult__item, [class*='item']")
    
    current_today_items = []
    new_arrivals = []

    # 判定パターンの作成（2026年05月13日、05/13、5/13、本日、などを網羅）
    date_patterns = [
        f"{m}/{d}", f"{m_zero}/{d_zero}", 
        f"{m}月{d}日", f"{m_zero}月{d_zero}日",
        "本日", "時間前", "分前"
    ]

    for item in items:
        full_text = item.get_text(" ", strip=True)
        
        # いずれかの日付パターンに合致するかチェック
        is_today = any(p in full_text for p in date_patterns)
        
        if is_today:
            name_tag = item.find(["h1", "h2", "h3", "strong"])
            if not name_tag: continue
                
            name_text = name_tag.get_text(strip=True).replace("NEW", "").strip()
            # 店名を抽出
            clean_name = re.split(r'\(|（|駅徒歩|駅直結', name_text)[0].strip()
            
            if not clean_name or len(clean_name) < 2: continue

            a_tag = item.find("a", href=True)
            link = "https://job.inshokuten.com" + a_tag["href"] if a_tag else target_url

            job_info = {"title": clean_name, "url": link}
            
            if not any(x['title'] == clean_name for x in current_today_items):
                current_today_items.append(job_info)
                if clean_name not in old_titles:
                    new_arrivals.append(job_info)

    if new_arrivals:
        print(f"\n★新着 {len(new_arrivals)} 件 発見！（{m}/{d}）★")
        for job in new_arrivals:
            print(f"【店名】: {job['title']}")
            print(f"【URL】: {job['url']}")
            print("-" * 30)
    else:
        print(f"\n{m}/{d} の新着は見つかりませんでした。")

    # 見つかった分（空でも）で履歴を更新
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
