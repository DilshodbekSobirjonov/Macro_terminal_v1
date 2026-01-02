# services/telegram.py

import requests


class TelegramService:
    def __init__(self, token, channel_id, admin_id):
        self.token = token
        self.channel_id = channel_id
        self.admin_id = admin_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0

    def _send(self, chat_id, text):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)

    # 📢 канал
    def send_channel(self, text):
        self._send(self.channel_id, text)

    # 👤 админ
    def send_admin(self, text):
        self._send(self.admin_id, text)

    # 📥 получить команды
    def fetch_commands(self):
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 0
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        updates = r.json()["result"]
        commands = []

        for u in updates:
            self.offset = u["update_id"] + 1

            msg = u.get("message")
            if not msg:
                continue

            if msg["chat"]["id"] != int(self.admin_id):
                continue

            text = msg.get("text", "")
            if text.startswith("/"):
                commands.append(text)

        return commands