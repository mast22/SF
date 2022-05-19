import logging

import requests
from django.conf import settings

from apps.users.models import User

base_url = 'https://api.telegram.org/bot{}/{}'


def _request_telegram(method: str, data: dict or None = None):
    token = settings.TELEGRAM_BOT_TOKEN
    response = requests.post(base_url.format(token, method), json=data)
    if response.status_code != 200:
        logging.info(f"Sending message to {data['chat_id']}")


def send_message(user_id: int, msg: str):
    user = User.objects.get(pk=user_id)
    if user.telegram_id:
        data = {'chat_id': user.telegram_id, 'text': msg}
        _request_telegram(method='sendMessage', data=data)
    else:
        logging.info(f'User {user.id} has no telegram_id')
