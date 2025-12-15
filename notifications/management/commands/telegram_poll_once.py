import json
import logging
import os
from pathlib import Path
from typing import Optional

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from notifications.models import TelegramLinkToken, TelegramProfile


logger = logging.getLogger(__name__)


API_BASE = "https://api.telegram.org"
OFFSET_FILE = ".telegram_offset"


def _token() -> str:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is not configured')
    return token


def _base_dir() -> Path:
    # BASE_DIR from settings
    return Path(getattr(settings, 'BASE_DIR', Path.cwd()))


def _load_offset() -> Optional[int]:
    p = _base_dir() / OFFSET_FILE
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        return int(data.get('update_id')) if data and 'update_id' in data else None
    except Exception:
        return None


def _save_offset(update_id: int) -> None:
    p = _base_dir() / OFFSET_FILE
    try:
        p.write_text(json.dumps({'update_id': int(update_id)}, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        logger.warning("Failed to save offset: %s", e)


def _send_reply(chat_id: int, text: str) -> None:
    token = _token()
    url = f"{API_BASE}/bot{token}/sendMessage"
    try:
        requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        }, timeout=10)
    except Exception as e:
        logger.warning("Failed to send reply: %s", e)


class Command(BaseCommand):
    help = "Poll Telegram getUpdates once and process /link <code> messages"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50, help='Max updates to fetch')

    def handle(self, *args, **options):
        token = _token()
        last_offset = _load_offset()
        params = {
            'timeout': 0,
            'limit': options['limit'],
        }
        if last_offset is not None:
            params['offset'] = last_offset + 1

        url = f"{API_BASE}/bot{token}/getUpdates"
        resp = requests.get(url, params=params, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        if not data.get('ok'):
            self.stderr.write(self.style.ERROR(f"getUpdates failed: {resp.text}"))
            return

        updates = data.get('result', [])
        max_update_id = last_offset or -1

        for upd in updates:
            update_id = upd.get('update_id')
            if update_id is not None and update_id > max_update_id:
                max_update_id = update_id

            msg = upd.get('message') or {}
            if not msg:
                continue

            chat = msg.get('chat') or {}
            chat_id = chat.get('id')
            from_user = msg.get('from') or {}
            username = from_user.get('username') or ''
            text = (msg.get('text') or '').strip()

            if not text.startswith('/link'):
                continue

            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                _send_reply(chat_id, 'Нужно передать код: /link <код>')
                continue

            code = parts[1].strip()
            now = timezone.now()
            try:
                token_obj = TelegramLinkToken.objects.select_related('user').get(code=code, used_at__isnull=True)
            except TelegramLinkToken.DoesNotExist:
                _send_reply(chat_id, 'Код не найден или уже использован. Сгенерируйте новый в личном кабинете.')
                continue

            if token_obj.expires_at <= now:
                _send_reply(chat_id, 'Код истёк. Сгенерируйте новый в личном кабинете.')
                continue

            # Create or update profile
            profile, _created = TelegramProfile.objects.update_or_create(
                user=token_obj.user,
                defaults={'chat_id': chat_id, 'username': username},
            )

            token_obj.used_at = now
            token_obj.save(update_fields=['used_at'])

            _send_reply(chat_id, '✅ Telegram успешно привязан к вашему аккаунту. Теперь вы будете получать уведомления.')

        if max_update_id >= 0 and max_update_id != (last_offset or -1):
            _save_offset(max_update_id)
        self.stdout.write(self.style.SUCCESS(f"Processed {len(updates)} updates. Offset={max_update_id}"))
