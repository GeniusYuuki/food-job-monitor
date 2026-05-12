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
                # 念のため、要素が辞書形式であることを確認しながらリスト化
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
        response.raise_for_status()
    except Exception as e:
        print(f"アクセスエラー: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all(["section", "div", "article"], class_=lambda x: x and ("item" in x.lower() or "list" in x.lower()))
    
    current_today_items = []
    new_arrivals = []

    for item in items:
        try:
            text = item.get_text(separator=' ', strip=True)
            
            # 当日更新判定
            if re.search(rf"({m}|{m_zero})[月/\.\- ]+({d}|{d_zero})", text) or "本日" in text or "時間前" in text:
                # タイトル取得（エラーが出にくいよう安全に取得）
                title_tag = item.find(["h1", "h2", "h3"])
                if not title_tag:
                    continue
                
                raw_title = title_tag.get_text(strip=True).replace("NEW", "").strip()
                clean_title = re.split(r'\(|（|駅徒歩', raw_title)[0].strip()
                if not clean_title:
                    continue

                link_tag = item.find("a", href=True)
                job_url = "https://job.inshokuten.com" + link_tag["href"] if link_tag else target_url

                # エリア情報の抽出（失敗しても空文字にするだけで止まらないようにする）
                area = ""
                address_tag = item.find(class_=lambda x: x and ("address" in x or "map" in x))
                if address_tag:
                    area = address_tag.get_text(strip=True)

                job_info = {"title": clean_title, "area": area, "url": job_url}
                
                # 今日のリストに追加（重複排除）
                if not any(d['title'] == clean_title for d in current_today_items):
                    current_today_items.append(job_info)

                    # 履歴になければ新着として出力
                    if clean_title not in old_titles:
                        new_arrivals.append(job_info)
        except Exception as e:
            # ループ内の1件でエラーが起きても、次の店の解析へ進む
            print(f"スキップ: 解析エラー")
            continue

    if new_arrivals:
        print(f"\n★新着 {len(new_arrivals)} 件 発見！★")
        for job in new_arrivals:
            print(f"【店名】: {job['title']}")
            print(f"【URL】: {job['url']}")
            print("-" * 30)
    else:
        print(f"\n新着はありませんでした。")

    # 全件をしっかり履歴に書き込む
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(current_today_items, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
