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

# スマホ版URL（パラメータに sort=new を維持）
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

    # ★User-AgentをiPhone(スマホ版)に設定
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # スマホ版の求人カード要素を探す（より広く取得）
    items = soup.find_all(["section", "div", "article"], class_=lambda x: x and ("item" in x.lower() or "list" in x.lower()))
    
    print(f"--- スマホ版偽装デバッグ ---")
    print(f"取得した要素数: {len(items)}")

    current_today_items = []
    new_arrivals = []

    for item in items:
        text = item.get_text(separator=' ', strip=True)
        
        # 日付判定（"5/12", "05/12", "5月12日", "本日"）
        # 正規表現をさらにシンプルに
        if re.search(rf"({m}|{m_zero})[月/\.\- ]+({d}|{d_zero})", text) or "本日" in text or "時間前" in text:
            # 店名取得
            title_tag = item.find(["h1", "h2", "h3", "strong"])
            if not title_tag: continue
            title = title_tag.get_text(strip=True).replace("NEW", "").strip()
            
            # エリア取得
            area = "不明"
            # スマホ版は dt/dd 構造が多い
            area_tag = item.find(["dd", "address", "span"])
            if area_tag: area = area_tag.get_text(strip=True)[:20]

            job_info = {"title": title, "area": area}
            current_today_items.append(job_info)

            if title not in old_titles:
                new_arrivals.append(job_info)

    if new_arrivals:
        print(f"\n★【スマホ版で発見！】新着あり！（{m}/{d}）★")
        for job in new_arrivals:
            print(f"店名: {job['title']} / エリア: {job['area']}")
            print("-" * 30)
    else:
        # デバッグ：一件目のテキストを少しだけ出す
        if items:
            print(f"サンプルテキスト: {items[0].get_text()[:50]}...")
        print(f"\n本日（{m}月{d}日）の更新分は見つかりませんでした。")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
