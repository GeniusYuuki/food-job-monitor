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

# 正規表現パターン
date_pattern = re.compile(f"({m}|{m_zero})[年/\. ]+({d}|{d_zero})")

# ★URLの末尾に &sort=new を追加して、新着を強制的に上に持ってくる
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all(["article", "section", "div"], class_=lambda x: x and ("item" in x or "Result" in x))
    
    print(f"--- 読み込みデバッグ情報 ---")
    print(f"取得したアイテム数: {len(items)}")

    current_today_items = []
    new_arrivals = []

    for item in items:
        text_content = item.get_text(separator=' ', strip=True)
        
        # もし今日が見つからない場合、どんな日付が入っているかデバッグ表示
        # (ログが爆発しないよう、最初の一件だけ出す)
        if items.index(item) == 0:
            found_dates = re.findall(r"\d{1,2}[年/\.]\d{1,2}", text_content)
            print(f"先頭アイテム内の日付サンプル: {found_dates}")

        if date_pattern.search(text_content) or "本日" in text_content or "時間前" in text_content:
            title_tag = item.find(["h3", "h2", "strong", "p"], class_=lambda x: x and "title" in x)
            if not title_tag: title_tag = item.find(["h3", "h2"])
            if not title_tag: continue
            
            title = title_tag.get_text(strip=True).replace("NEW", "").strip()
            area_tag = item.find(class_=lambda x: x and ("address" in x or "map" in x))
            area = area_tag.get_text(strip=True) if area_tag else "エリア不明"

            job_info = {"title": title, "area": area}
            current_today_items.append(job_info)

            if title not in old_titles:
                new_arrivals.append(job_info)

    if new_arrivals:
        print(f"\n★新着あり！★ (判定対象: {m}/{d})")
        print("=" * 40)
        for job in new_arrivals:
            print(f"店名: {job['title']} / エリア: {job['area']}")
            print("-" * 40)
    else:
        print(f"\n本日（{m}月{d}日）の更新分は見つかりませんでした。")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
