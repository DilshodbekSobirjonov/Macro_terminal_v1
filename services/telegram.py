# services/telegram.py

import requests


class TelegramService:
    def __init__(self, token, channel_id, admin_id):
        self.token = token
        self.channel_id = channel_id
        self.admin_id = admin_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0

    # ---------------- SEND ----------------

    def _send(self, chat_id, text):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except requests.RequestException:
            pass

    def send_channel(self, text):
        self._send(self.channel_id, text)

    def send_admin(self, text):
        self._send(self.admin_id, text)

    # ---------------- COMMANDS ----------------

    def fetch_commands(self):
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 0
        }

        try:
            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()
        except requests.RequestException:
            return []

        data = r.json()
        updates = data.get("result", [])
        commands = []

        for update in updates:
            self.offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            if message["chat"]["id"] != int(self.admin_id):
                continue

            text = message.get("text", "")
            if text.startswith("/"):
                commands.append(text)

        return commands