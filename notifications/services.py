import logging
import requests

from django.conf import settings

from .models import TelegramProfile

logger = logging.getLogger(__name__)


API_BASE = "https://api.telegram.org"


def _bot_token() -> str:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is not configured')
    return token


def send_telegram_message(user, text: str) -> bool:
    """Send a Telegram message to a user linked via TelegramProfile.

    Returns True if sent successfully, False otherwise.
    """
    try:
        profile = TelegramProfile.objects.get(user=user)
    except TelegramProfile.DoesNotExist:
        logger.warning("User %s has no TelegramProfile; skip sending", user)
        return False

    token = _bot_token()
    url = f"{API_BASE}/bot{token}/sendMessage"
    payload = {
        'chat_id': profile.chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        ok = resp.ok and resp.json().get('ok') is True
        if not ok:
            logger.error("Telegram sendMessage failed: %s", resp.text)
        return bool(ok)
    except Exception as e:
        logger.exception("Failed to send Telegram message: %s", e)
        return False
