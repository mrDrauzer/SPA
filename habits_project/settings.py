import os
import sys
from datetime import timedelta
from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    PAGINATION_PAGE_SIZE=(int, 5),
)

# Read .env file at project root if present
environ.Env.read_env(str(BASE_DIR / '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY', default='change-me')
DEBUG = env('DEBUG')

ALLOWED_HOSTS = [h for h in env('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',') if h]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    # Local apps
    'users',
    'habits',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'habits_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'habits_project.wsgi.application'
ASGI_APPLICATION = 'habits_project.asgi.application'


# Database
# Force SQLite when running under pytest to avoid connecting to external Postgres.
# Rationale: environment var PYTEST_CURRENT_TEST may be set too late on some setups,
# so additionally detect pytest via loaded modules.
if ('PYTEST_CURRENT_TEST' in os.environ) or any(m.startswith('pytest') for m in sys.modules.keys()):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / 'test_db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# During pytest, force UTC timezone to avoid ambiguity when asserting hours in tests
if ('PYTEST_CURRENT_TEST' in os.environ) or any(m.startswith('pytest') for m in sys.modules.keys()):
    TIME_ZONE = 'UTC'


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CORS
_cors = env('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://127.0.0.1:3000')
CORS_ALLOWED_ORIGINS = [x for x in _cors.split(',') if x]


# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': env('PAGINATION_PAGE_SIZE'),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Habits API',
    'DESCRIPTION': 'SPA backend for habits tracker with Telegram reminders',
    'VERSION': '1.0.0',
}


# Celery
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False

# Celery Beat schedule
from celery.schedules import crontab  # type: ignore
CELERY_BEAT_SCHEDULE = {
    'check-and-notify-due-habits': {
        'task': 'habits.tasks.check_and_notify_due_habits',
        'schedule': 60.0,  # every minute
        # Alternatively: 'schedule': crontab(),
    },
}


# Telegram
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_CHAT_ID = env('TELEGRAM_CHAT_ID', default='')
