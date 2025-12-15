# SPA Habits Backend

Backend для SPA‑трекера привычек (Django + DRF + JWT + Celery + Redis + Telegram + drf‑spectacular).

## Быстрый старт (локально)

1) Виртуальное окружение (рекомендуется)
   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

2) Зависимости
   ```bash
   pip install -r requirements.txt
   ```

3) .env (пример минимальных значений)
   Скопируйте `.env.example` в `.env` и задайте переменные:
   ```env
   DJANGO_SECRET_KEY=change-me
   DEBUG=True
   # Разрешим локальные хосты и доступ по 0.0.0.0
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

   # PostgreSQL (пример для локальной БД SPA)
   DATABASE_URL=postgresql://django_user:password123@127.0.0.1:5433/SPA

   # Redis для Celery
   REDIS_URL=redis://localhost:6379/0

   # Telegram Bot (токен своего бота из @BotFather)
   TELEGRAM_BOT_TOKEN=<ваш_токен>
   TELEGRAM_BOT_USERNAME=<имя_бота>

   # Пагинация API
   PAGINATION_PAGE_SIZE=5
   ```
   Примечание: под pytest проект автоматически использует SQLite, чтобы не требовать доступ к Postgres при тестах.

4) Создайте БД и примените миграции
   - Создайте базу данных `SPA` в PostgreSQL (через pgAdmin/psql) и убедитесь, что доступна по `127.0.0.1:5433`.
   - Примените миграции:
     ```bash
     python manage.py migrate
     ```

5) Запустите сервер
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   Если видите DisallowedHost для `0.0.0.0`, добавьте `0.0.0.0` в `ALLOWED_HOSTS` или заходите по `http://127.0.0.1:8000/`.

6) Документация API
   - Swagger UI: `http://127.0.0.1:8000/api/docs/swagger/`
   - ReDoc: `http://127.0.0.1:8000/api/docs/redoc/`
   - OpenAPI схема: `http://127.0.0.1:8000/api/schema/`

7) Аутентификация (JWT) и Users API
   - Получить токен: `POST /api/auth/jwt/create/` с полями `username` и `password`.
   - Обновить токен: `POST /api/auth/jwt/refresh/`.

   Users API:
   - Регистрация: `POST /api/users/register/`
     - Поля: `username`, `email` (обязателен, уникален), `password`, `password2`, опц. `first_name`, `last_name`.
   - Профиль: `GET /api/users/me/` (JWT), частичное обновление: `PATCH /api/users/me/` (поля: `email`, `first_name`, `last_name`).
   - Смена пароля: `POST /api/users/change-password/` (JWT; поля: `old_password`, `new_password`).
   - Статус привязки Telegram: `GET /api/users/telegram/` (JWT) → `{ linked: true/false, ... }`.

## Telegram: привязка пользователя и рассылка напоминаний

В проекте бот используется для отправки уведомлений. Привязка аккаунта к боту — через одноразовый код привязки. Создание привычек через бота пока не реализовано (см. планы ниже), привычки создаются через админку или REST API.

1) Убедитесь, что у бота нет webhook (для polling):
   ```powershell
   curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/deleteWebhook"
   ```

2) Сгенерируйте код привязки через API (рекомендуется):
   - Запрос: `POST /api/telegram/link/` с заголовком `Authorization: Bearer <JWT>`.
   - Ответ: `{ "code": "<код>", "expires_at": <ISO>, "tme_link": "https://t.me/<bot>?start=<код>" (если передать `?bot=<bot_username>` в запросе) }`.

   Альтернатива (через Django shell для отладки):
   ```powershell
   python manage.py shell -c "from django.utils import timezone; from datetime import timedelta; from django.contrib.auth import get_user_model; from notifications.models import TelegramLinkToken; User=get_user_model(); u=User.objects.get(username='admin'); t=TelegramLinkToken.objects.create(user=u, code='ABC123', expires_at=timezone.now()+timedelta(minutes=30)); print('CODE='+t.code)"
   ```

3) Отправьте боту в Telegram команду со сгенерированным кодом (клиент может использовать `/start <код>` или `/link <код>` — зависит от логики бота).

4) Обработайте апдейты (polling) и привяжите профиль:
   ```bash
   python manage.py telegram_poll_once
   ```
   При успехе бот ответит в чате, а в админке появится Telegram профиль с `chat_id`.

5) Проверка отправки сообщения напрямую:
   ```bash
   python manage.py shell -c "from django.contrib.auth import get_user_model; from notifications.services import send_telegram_message; User=get_user_model(); u=User.objects.get(username='admin'); print(send_telegram_message(u, 'Тестовое сообщение'))"
   ```

## Напоминания (Celery + Redis)

- Периодическая задача: `habits.tasks.check_and_notify_due_habits` (каждую минуту).
- Для работы нужны процессы Celery и Redis.

Запуск компонентов локально (в отдельных окнах):
```bash
# Веб‑сервер
python manage.py runserver 0.0.0.0:8000

# Celery worker
celery -A habits_project worker -l info

# Celery beat (расписание задач)
celery -A habits_project beat -l info
```

Создайте непубличную привычку (is_public=False) для себя со временем на ближайшие 1–3 минуты — придёт напоминание в Telegram. Либо вызовите задачу вручную:
```bash
python manage.py shell -c "from habits.tasks import check_and_notify_due_habits; check_and_notify_due_habits()"
```

## Публичные привычки и их принятие

- Список публичных привычек (доступен всем, с пагинацией):
  - `GET /api/habits/public/`
  - Фильтрация по подстроке в действии/месте: `?q=слово`

- Принять публичный шаблон (создать себе копию):
  - `POST /api/habits/public/{id}/adopt/` — только для аутентифицированных
  - Возвращает созданный объект привычки пользователя (с `is_public=False`).
  - Если шаблон (полезная привычка) ссылается на «приятную», сначала клонируется приятная, затем полезная связывается на неё.
  - Любые клиентские поля игнорируются: владелец всегда `request.user`, `is_public` всегда `False`, `linked_habit` проставляется только на созданную копию «приятной» (если есть).

- Свои привычки (закрытый CRUD):
  - `GET/POST /api/habits/`
  - `GET/PATCH/PUT/DELETE /api/habits/{id}/`

## Сидинг публичных привычек

Добавлена management-команда для наполнения базы публичными шаблонами от системного пользователя `public`.

Запуск:

```bash
python manage.py seed_public_habits
```

Команда идемпотентна — повторный запуск не создаёт дублей существующих записей.

## Напоминания (Celery + Telegram)

— В модели `Habit` есть поля `last_notified_at`, `next_run_at`; расчёт следующего запуска учитывает время привычки и `periodicity_days`.
— Есть небольшое «окно идемпотентности», чтобы избежать дублей при частых запусках.

Токен бота Telegram и Redis настраиваются через `.env` (`TELEGRAM_BOT_TOKEN`, `REDIS_URL`). Привязка аккаунта — через `/link <код>` и management‑команду `telegram_poll_once` (см. раздел Telegram выше).

## Планируемое улучшение: создание привычек через бота

Сейчас бот используется для привязки и отправки напоминаний. Поддержка создания привычек через чат с ботом (например, команда `/habit ...` или пошаговый мастер `/newhabit`) будет добавлена отдельно.
