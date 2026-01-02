# services/telegram.py

import requests


class TelegramService:
    def __init__(self, token, channel_id, admin_id):
        self.token = token
        self.channel_id = channel_id
        self.admin_id = admin_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def _send(self, chat_id, text):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)

    # 📢 в канал
    def send_channel(self, text):
        self._send(self.channel_id, text)

    # 👤 в личку админу
    def send_admin(self, text):
        self._send(self.admin_id, text)
