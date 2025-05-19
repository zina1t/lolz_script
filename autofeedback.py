import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://prod-api.lzt.market"
FORUM_URL = "https://prod-api.lolz.live"
TOKEN = os.getenv("LZT_TOKEN")
HEADERS = {
    "Authorization": TOKEN,
    "Accept": "application/json"
}

THIRTY_DAYS_AGO = int(time.time()) - 30 * 24 * 60 * 60
CHECK_INTERVAL = 300  # 5 минут
REQUEST_DELAY = 0.5   # 0.5 сек между запросами
LOG_FILE = "buyers.log"

known_user_ids = set()

def load_logged_user_ids():
    """Загружает user_id из файла логов"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line.isdigit():
                    known_user_ids.add(int(line))
    print(f"Загружено {len(known_user_ids)} user_id из логов")

def log_user_id(user_id):
    """Добавляет user_id в лог-файл"""
    with open(LOG_FILE, "a") as file:
        file.write(f"{user_id}\n")

def get_recent_sold_item_ids():
    all_item_ids = []
    page = 1
    while True:
        try:
            print(f"Получение продаж (страница {page})...")
            response = requests.get(
                f"{API_URL}/user/payments",
                headers=HEADERS,
                params={"type": "sold_item", "page": page}
            )
            response.raise_for_status()
            payments = response.json().get("payments", {})
            if not payments:
                break

            for payment in payments.values():
                operation_date = payment.get("operation_date", 0)
                if operation_date < THIRTY_DAYS_AGO:
                    return all_item_ids
                item_id = payment.get("item_id")
                if item_id:
                    all_item_ids.append(item_id)

            page += 1
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            print(f"Ошибка получения item_id: {e}")
            break

    return all_item_ids

def get_buyer_user_id(item_id):
    try:
        url = f"{API_URL}/{item_id}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        buyer = data.get("item", {}).get("buyer", {})

        return buyer.get("user_id")
    except Exception as e:
        print(f"Ошибка при получении user_id для item_id {item_id}: {e}")
        return None

def send_feedback_request(user_id, item_id):
    try:
        response = requests.post(
            f"{FORUM_URL}/conversations",
            headers={"Authorization": TOKEN, "Content-Type": "application/json"},
            json={
                "recipient_id": user_id,
                "message_body": f"Спасибо, что выбрали нас! Если у вас есть минута, будем очень благодарны за честный отзыв — это поможет другим покупателям. Если что-то не так — сразу пишите, исправим! Ссылка:{API_URL}/{item_id}",
                "is_group": False
            }
        )
        time.sleep(REQUEST_DELAY)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки сообщения для user_id {user_id}: {e}")
        return False

def daily_refresh_user_ids():
    """Обновляет known_user_ids"""
    item_ids = get_recent_sold_item_ids()
    print(f"Найдено {len(item_ids)} item_id за последние 30 дней")

    for item_id in item_ids:
        user_id = get_buyer_user_id(item_id)
        if user_id and user_id not in known_user_ids:
            known_user_ids.add(user_id)
        time.sleep(REQUEST_DELAY)

    print(f"Обновлено: {len(known_user_ids)} уникальных покупателей")

def check_new_sales():
    """Проверка новых продаж и отправка сообщений новым покупателям"""
    print("Проверка новых продаж")
    try:
        response = requests.get(
            f"{API_URL}/user/payments",
            headers=HEADERS,
            params={"type": "sold_item", "page": 1}
        )
        response.raise_for_status()
        payments = response.json().get("payments", {})

        for payment in payments.values():
            operation_date = payment.get("operation_date", 0)
            if operation_date < THIRTY_DAYS_AGO:
                continue

            item_id = payment.get("item_id")
            if not item_id:
                continue

            user_id = get_buyer_user_id(item_id)
            if not user_id:
                continue

            if user_id not in known_user_ids:
                print(f"Новый покупатель {user_id}, отправка сообщения")
                if send_feedback_request(user_id, item_id):
                    print("Сообщение отправлено")
                    known_user_ids.add(user_id)
                    log_user_id(user_id)
                else:
                    print("Ошибка отправки")
            time.sleep(REQUEST_DELAY)
    except Exception as e:
        print(f"Ошибка проверки новых продаж: {e}")

def main():
    load_logged_user_ids()
    last_refresh_day = -1
    while True:
        current_day = time.localtime().tm_yday
        if current_day != last_refresh_day:
            print("Ежедневное обновление списка покупателей")
            daily_refresh_user_ids()
            last_refresh_day = current_day

        check_new_sales()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
