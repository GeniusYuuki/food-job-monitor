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
    # 履歴の読み込み
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
        response.encoding = response.apparent_encoding # 文字化け防止
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # スマホ版のアイテム要素を広く取得
    items = soup.select("section, article, .p-searchResult__item, [class*='item']")
    
    current_today_items = []
    new_arrivals = []

    for item in items:
        # 要素内の全テキストを結合
        full_text = item.get_text(" ", strip=True)
        
        # 今日（5/12）の更新か判定
        if re.search(rf"({m}|{m_zero})[月/\.\- ]+({d}|{d_zero})", full_text) or "本日" in full_text or "時間前" in full_text:
            # 店名の抽出（h1〜h3、または特定のクラスを狙う）
            name_tag = item.find(["h1", "h2", "h3", "strong"])
            if not name_tag:
                continue
                
            name_text = name_tag.get_text(strip=True).replace("NEW", "").strip()
            # カッコや駅名より前を店名として確定
            clean_name = re.split(r'\(|（|駅徒歩|駅直結', name_text)[0].strip()
            
            if not clean_name or len(clean_name) < 2:
                continue

            # URLの取得
            a_tag = item.find("a", href=True)
            link = "https://job.inshokuten.com" + a_tag["href"] if a_tag else target_url

            # データ構築
            job_info = {"title": clean_name, "url": link}
            
            # リストに追加（重複チェック）
            if not any(x['title'] == clean_name for x in current_today_items):
                current_today_items.append(job_info)
                # 履歴になければ「新着」
                if clean_name not in old_titles:
                    new_arrivals.append(job_info)

    # 結果出力
    if new_arrivals:
        print(f"\n★新着 {len(new_arrivals)} 件 発見！★")
        for job in new_arrivals:
            print(f"【店名】: {job['title']}")
            print(f"【URL】: {job['url']}")
            print("-" * 30)
    else:
        print("\n新しく更新された店舗はありませんでした。")

    # 履歴を保存（今日見つけた全ての店を保存）
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
