import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

# 【設定】ご提示のURL（東京23区・三鷹市／オープニング募集）
# ページ番号を差し込めるように {page} としています
BASE_URL = "https://job.inshokuten.com/kanto/work/search?searchShopCharacteristicId=40&searchRegionArea=tokyo-23ward&searchRegionArea=mitaka-city&page={page}"
DATA_FILE = "history.json"

def get_jobs(url, headers):
    """指定されたページの求人情報を取得する関数"""
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200: return {}
        
        soup = BeautifulSoup(res.text, "html.parser")
        # 求人枠の抽出（飲食店ドットコムの最新構造に対応）
        job_blocks = soup.select("section.p-searchResult__item")
        
        page_data = {}
        for block in job_blocks:
            # 店名・タイトルの取得
            title_tag = block.select_one("h2.p-searchResult__itemTitle a")
            # 所在地/最寄駅の取得
            loc_tag = block.select_one(".p-searchResult__itemInfoText")
            
            if title_tag:
                # URLの正規化（?以降をカット）
                job_url = "https://job.inshokuten.com" + title_tag.get("href").split("?")[0]
                job_title = title_tag.get_text(strip=True)
                location = loc_tag.get_text(strip=True) if loc_tag else "場所不明"
                
                page_data[job_url] = f"{job_title} （{location}）"
        return page_data
    except:
        return {}

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Referer": "https://job.inshokuten.com/"
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = {}
    else: history = {}

    all_current_jobs = {}
    # 【強化ポイント】1ページ目と2ページ目を順番にスキャン
    for p in [1, 2]:
        print(f"求人飲食店ドットコム {p}ページ目をスキャン中...")
        target_url = BASE_URL.format(page=p)
        time.sleep(random.uniform(5, 8)) # ブロック回避
        jobs = get_jobs(target_url, headers)
        all_current_jobs.update(jobs) # データを合体

    print(f"--- スキャン完了: 合計{len(all_current_jobs)}件を把握 ---")

    # 差分チェック
    any_news = False
    new_links = [link for link in all_current_jobs.keys() if link not in history]
    
    if new_links:
        any_news = True
        print("★【飲食店ドットコム】新着のオープニング募集が見つかりました！")
        for link in new_links:
            print(f"  - {all_current_jobs[link]}")
            print(f"    URL: {link}")
    
    if not any_news:
        print("今回のスキャン（最大40件）では新着求人はありませんでした。")

    # 最新の状態を履歴に保存
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_current_jobs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
ステップ3：指示書 (.github/workflows/run.yml) の作成
食べログの実行時間（毎時37分など）と重ならないように、**「毎時45分」**に設定しました。

YAML
name: Inshokuten-Job-Monitor

on:
  schedule:
    - cron: '45 * * * *' # 毎時45分に自動実行
  workflow_dispatch: # 手動実行ボタンを表示

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install requests beautifulsoup4
      - name: Run Job Check
        run: python job_checker.py
      - name: Commit and Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add history.json
          git commit -m "Update job history" || exit 0
          git push
