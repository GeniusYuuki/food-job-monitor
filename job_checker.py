import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
import os

# 日本時間(JST)の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
# 複数の形式で日付を用意
date_format_1 = now.strftime("%Y年%m月%d日") # 2026年05月12日
date_format_2 = now.strftime("%Y/%m/%d")    # 2026/05/12
date_format_3 = "本日"

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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 求人アイテムを抽出（クラス名に頼りすぎないよう broad に取得）
    items = soup.find_all(["article", "section", "div"], class_=lambda x: x and ("item" in x or "Result" in x))
    
    print(f"--- 読み込みデバッグ情報 ---")
    print(f"取得したアイテム数: {len(items)}")

    current_today_items = []
    new_arrivals = []

    for i, item in enumerate(items):
        text_content = item.get_text(separator=' ', strip=True)
        
        # タイトルの抽出（h3を探す、なければ最初の太字系）
        title_tag = item.find(["h3", "h2", "strong"])
        if not title_tag: continue
        title = title_tag.get_text(strip=True).replace("NEW", "").strip()
        
        # ログに出力（全アイテムのタイトルとテキストの一部）
        # print(f"DEBUG [{i}]: {title[:20]}... / Text contains date: {date_format_1 in text_content}")

        # 当日判定
        if any(d in text_content for d in [date_format_1, date_format_2, date_format_3]):
            # エリア情報の抽出
            area = "エリア不明"
            address_tag = item.find(class_=lambda x: x and "address" in x)
            if address_tag:
                area = address_tag.get_text(strip=True)

            job_info = {"title": title, "area": area, "url": url} # 詳細URL特定が難しければ一覧URLで代用
            current_today_items.append(job_info)

            if title not in old_titles:
                new_arrivals.append(job_info)

    # 結果の出力
    if new_arrivals:
        print(f"\n★新着あり！（{date_format_1}）★")
        for job in new_arrivals:
            print(f"店名: {job['title']}")
            print(f"エリア: {job['area']}")
            print("-" * 30)
    else:
        print(f"\n{date_format_1} 更新分は見つかりませんでした。")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
