import logging
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# SecretsからアクセストークンとユーザーIDを取得（環境変数に設定しておく）
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID1")  # Push API用、Notifyのみであれば不要

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("konpeito_check.log", encoding='utf-8')
    ]
)

URL = "https://expo2025shop.jp/item_list.html?siborikomi_clear=1&keyword=%E9%87%91%E5%B9%B3%E7%B3%96"

def check_stock():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    available_items = []
    boxes = soup.select("div.box")

    for box in boxes:
        # SOLD OUTのバッジがあるか判定
        soldout_badge = box.select_one("b.eds-badge:contains('SOLD OUT')")
        
        # 上記はcontains疑似セレクタ風ですが、BeautifulSoupで互換性ないため以下を使います
        badges = box.select("b.eds-badge")
        has_soldout = any(badge.get_text(strip=True) == "SOLD OUT" for badge in badges)

        if not has_soldout:
            title_tag = box.select_one("h3 a")
            title = title_tag.get_text(strip=True) if title_tag else "商品名不明"
            available_items.append(title)

    if available_items:
        message = "🎉 金平糖の在庫あり！\n" + "\n".join(f"・{name}" for name in available_items)
        message += "\n👉 https://expo2025shop.jp/"
        logging.info(message)
        send_line_message(message)
    else:
        logging.info("すべて売り切れです")

def send_line_message(message, access_token = ACCESS_TOKEN, user_id = USER_ID):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    logging.info(f"{headers=}, {body=}")
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        logging.warning(f"LINE送信失敗: {response.status_code} - {response.text}")
    else:
        logging.info("LINE送信成功")


if __name__ == "__main__":
    check_stock()
    