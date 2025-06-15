import requests
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import re

def escape_markdown_v2(text):
    # Escape the characters that MarkdownV2 requires:
    # _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'[_*\[\]()~`>#+\-=|{}.!]'
    return re.sub(escape_chars, r'\\\g<0>', text)

def send_telegram(message, image_bytes=None):
    url_base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    escaped_message = escape_markdown_v2(message)

    if image_bytes:
        url = f"{url_base}/sendPhoto"
        files = {'photo': ('chart.png', image_bytes)}
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': escaped_message,
            'parse_mode': 'MarkdownV2'
        }
        resp = requests.post(url, data=data, files=files)
    else:
        url = f"{url_base}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': escaped_message,
            'parse_mode': 'MarkdownV2'
        }
        resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()
