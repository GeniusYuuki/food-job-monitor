import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import os
import re

# 日本時間(JST)の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
m, d = str(now.month), str(now.day)
m_zero, d_zero = now.strftime("%m"), now.strftime("%d")

# ターゲットURL（新着順）
target_url = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchKeyword_u=&district=kanto&desiredConditionArea=kanto&desiredConditionArea=kanto&searchRegionArea=tokyo-23ward&sort=new"

def main():
    # 1. 履歴の読み込み
    old_data = []
    if os.path.exists("history.json"):
        with open("history.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if isinstance(loaded, list): old_data = loaded
            except: old_data = []
    
    old_titles = {item["title"] for item in old_data if isinstance(item, dict) and "title" in item}

    # 2. スマホ版としてアクセス
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # 求人要素を特定
    items = soup.find_all(["section", "div", "article"], class_=lambda x: x and ("item" in x.lower() or "list" in x.lower()))
    
    current_today_items = []
    new_arrivals = []

    # 3. 解析と抽出
    for item in items:
        text = item.get_text(separator=' ', strip=True)
        
        # 当日更新判定（正規表現）
        if re.search(rf"({m}|{m_zero})[月/\.\- ]+({d}|{d_zero})", text) or "本日" in text or "時間前" in text:
            # タイトル（店名）取得
            title_tag = item.find(["h1", "h2", "h3"])
            if not title_tag: continue
            
            raw_title = title_tag.get_text(strip=True).replace("NEW", "").strip()
            # 店名のみ抽出（カッコ以降をカット）
            clean_title = re.split(r'\(|（|駅徒歩', raw_title)[0].strip()

            # 個別URL取得
            link_tag = item.find("a", href=True)
            job_url = "https://job.inshokuten.com" + link_tag["href"] if link_tag else target_url

            # エリア取得
            area = "都内23区"
            address_tag = item.find(class_=lambda x: x and ("address" in x or "map" in x))
            if address_tag:
                area = address_tag.get_text(strip=True)
            elif item.find("dd"):
                area = item.find("dd").get_text(strip=True)

            job_info = {"title": clean_title, "area": area, "url": job_url}
            current_today_items.append(job_info)

            # 差分（新着）チェック
            if clean_title not in old_titles:
                new_arrivals.append(job_info)

    # 4. ログ出力
    if new_arrivals:
        print(f"\n★新着 {len(new_arrivals)} 件 発見！（{m}/{d} 更新分）★")
        print("=" * 50)
        for job in new_arrivals:
            print(f"【店名】: {job['title']}")
            print(f"【エリア】: {job['area']}")
            print(f"【URL】: {job['url']}")
            print("-" * 50)
    else:
        print(f"\n本日（{m}月{d}日）の新しい更新は見つかりませんでした。")

    # 5. 履歴保存
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
