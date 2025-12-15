try:
    from .celery import app as celery_app  # type: ignore
except Exception:  # pragma: no cover - during initial setup celery may be absent
    celery_app = None  # fallback to avoid import errors before Celery is configured

__all__ = ("celery_app",)
