import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import os

# 日本時間(JST)の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)

# 判定用ワード：月日だけに絞ってヒット率を最大化する
target_m_d = now.strftime("%m月%d日") # "05月12日"
target_slash = now.strftime("%m/%d")   # "05/12"
target_today = "本日"

url = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchKeyword_u=&district=kanto&desiredConditionArea=kanto&desiredConditionArea=kanto&searchRegionArea=tokyo-23ward"

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
    
    # 214個取得できているので、そのままのロジックを継続
    items = soup.find_all(["article", "section", "div"], class_=lambda x: x and ("item" in x or "Result" in x))
    
    print(f"--- 読み込みデバッグ情報 ---")
    print(f"取得したアイテム数: {len(items)}")

    current_today_items = []
    new_arrivals = []

    for item in items:
        # カード内の全テキストを取得
        text_content = item.get_text(strip=True)
        
        # 月日が含まれているかチェック
        if target_m_d in text_content or target_slash in text_content or target_today in text_content:
            title_tag = item.find(["h3", "h2", "strong", "p"], class_=lambda x: x and "title" in x)
            if not title_tag:
                title_tag = item.find(["h3", "h2"]) # 予備
            
            if not title_tag: continue
            
            title = title_tag.get_text(strip=True).replace("NEW", "").strip()
            
            # エリア情報の取得
            area = "エリア不明"
            # addressやmapなどのクラスを持つ要素を探す
            area_tag = item.find(class_=lambda x: x and ("address" in x or "map" in x))
            if area_tag:
                area = area_tag.get_text(strip=True)

            job_info = {"title": title, "area": area}
            current_today_items.append(job_info)

            if title not in old_titles:
                new_arrivals.append(job_info)

    # 結果の出力
    if new_arrivals:
        print(f"\n★新着あり！（{target_m_d} 更新分）★")
        print("=" * 40)
        for job in new_arrivals:
            print(f"店名: {job['title']}")
            print(f"エリア: {job['area']}")
            print("-" * 40)
    else:
        print(f"\n{target_m_d} 更新分は見つかりませんでした。")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
