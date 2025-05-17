import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("LZT_TOKEN")  
API_URL = "https://prod-api.lzt.market"
FORUM_URL = "https://prod-api.lolz.live"

def get_sold_accounts():
    """Получает список проданных аккаунтов."""
    try:
        response = requests.get(
            f"{API_URL}/user/payments?type=sold_item", # посмотреть какие параметры вообще там возвращаются
            headers={"Authorization": TOKEN},
            params={"status": "sold", "limit": 10}  # Последние 10 проданных
        )
        response.raise_for_status()
        return response.json().get("accounts", [])
    except Exception as e:
        print(f"Ошибка при получении продаж: {e}")
        return []

def get_buyer_id(item_id):
    """Получает user_id покупателя по ID аккаунта."""
    try:
        response = requests.get(
            f"{API_URL}/{item_id}",
            headers={"Authorization": TOKEN},
            params={"parse_same_item_ids": True}
        )
        data = response.json()
        return data.get("buyer", {}).get("user_id")
    except Exception as e:
        print(f"Ошибка при получении buyer_id: {e}")
        return None

def send_feedback_request(user_id):
    """Отправляет сообщение покупателю."""
    try:
        response = requests.post(
            f"{FORUM_URL}/conversations",
            headers={"Authorization": TOKEN, "Content-Type": "application/json"},
            json={
                "recipient_id": user_id,
                "message_body": "Спасибо за покупку! Пожалуйста, оставьте отзыв здесь: [ссылка].",
                "is_group": False
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return False

def main():
    while True:
        print("Проверяю новые продажи...")
        sold_accounts = get_sold_accounts()
        
        for account in sold_accounts:
            item_id = account.get("item_id")
            buyer_id = get_buyer_id(item_id)
            
            if buyer_id:
                print(f"Отправляю сообщение покупателю {buyer_id}...")
                if send_feedback_request(buyer_id):
                    print("✅ Сообщение отправлено!")
                else:
                    print("❌ Ошибка отправки.")
            else:
                print(f"❌ Не удалось получить buyer_id для аккаунта {item_id}")
        
        time.sleep(300)  # Проверка каждые 5 минут

if __name__ == "__main__":
    main()