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
    # Headlessブラウザ設定（GitHub Actionsやクラウド環境向け）
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"  # ← ここがポイント！
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.get(URL)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    sold_out_items = soup.find_all(string="SOLD OUT")

    if not sold_out_items:
        message = "🎉 金平糖が再入荷しました！\n👉 https://expo2025shop.jp/"
        logging.info(message)
        send_line_notify(message)
    else:
        logging.info("まだ売り切れです")

def send_line_notify(message):
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    data = {
        "message": message
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        logging.warning(f"LINE通知に失敗しました: {response.status_code} - {response.text}")

if __name__ == "__main__":
    check_stock()