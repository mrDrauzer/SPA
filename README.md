# SPA Habits Backend 2

Backend для SPA-трекера привычек (Django + DRF + JWT + Celery + Redis + Telegram + drf-spectacular).

## Быстрый старт (локально)

1) Создайте и активируйте виртуальное окружение (рекомендуется):
   - Windows PowerShell
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

2) Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3) Подготовьте переменные окружения:
   - Скопируйте `.env.example` в `.env` и при необходимости скорректируйте значения.
   - В `.env` позже внесите реальные `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` (в Git не коммитятся).

4) Примените миграции и запустите сервер:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5) Документация API:
   - Swagger UI: `http://127.0.0.1:8000/api/docs/swagger/`
   - ReDoc: `http://127.0.0.1:8000/api/docs/redoc/`
   - OpenAPI схема: `http://127.0.0.1:8000/api/schema/`

6) Аутентификация (JWT):
   - Получить токен: `POST /api/auth/jwt/create/` с полями `username` и `password`.
   - Обновить токен: `POST /api/auth/jwt/refresh/`.

## Celery и напоминания в Telegram (позже в курсе)

Celery/beat и интеграция с Telegram будут добавлены в следующих шагах (задачи для рассылки напоминаний). Для работы потребуется Redis (см. `REDIS_URL` в `.env`).

## Стек (по умолчанию)

- Django 5, DRF, Simple JWT, drf-spectacular, django-cors-headers, django-environ
- PostgreSQL (или SQLite локально), Redis
- Celery + celery-beat
- python-telegram-bot (либо Bot API запросы)
- Пагинация: 5 элементов на страницу

## Статус

- Сконфигурирован каркас проекта (настройки, URLs, JWT, CORS, Swagger/Redoc).
- Дальше: модели и валидаторы привычек, CRUD эндпоинты, публичный список, Celery-напоминания, тесты ≥80%, Docker Compose.
