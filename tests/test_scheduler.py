from datetime import time, datetime, timedelta

import pytest
from django.utils import timezone

from habits.tasks import calc_next_run, check_and_notify_due_habits
from habits.models import Habit


@pytest.mark.django_db
def test_calc_next_run_before_and_after_today(monkeypatch):
    # Fix current time to 2025-01-01 10:00+tz
    fixed_now = timezone.make_aware(datetime(2025, 1, 1, 10, 0, 0), timezone.get_current_timezone())

    # Case 1: time later today → same day
    later = time(11, 30, 0)
    dt1 = calc_next_run(later, periodicity_days=3, now=fixed_now)
    assert dt1.date() == fixed_now.date()
    assert dt1.hour == 11 and dt1.minute == 30

    # Case 2: time earlier today → today + periodicity_days
    earlier = time(9, 0, 0)
    dt2 = calc_next_run(earlier, periodicity_days=2, now=fixed_now)
    assert dt2.date() == (fixed_now + timedelta(days=2)).date()
    assert dt2.hour == 9 and dt2.minute == 0


@pytest.mark.django_db
def test_check_and_notify_initializes_and_moves_schedule(monkeypatch, user):
    # Fix now
    fixed_now = timezone.make_aware(datetime(2025, 1, 1, 8, 0, 0), timezone.get_current_timezone())

    # Monkeypatch timezone.now used inside the task
    monkeypatch.setattr(timezone, 'now', lambda: fixed_now)

    # Stub telegram sender to always succeed and record calls
    calls = {'count': 0}

    def fake_send(user_arg, text):
        calls['count'] += 1
        return True

    monkeypatch.setattr('habits.tasks.send_telegram_message', fake_send)

    # Create a non-public habit without next_run_at (should be initialized)
    h = Habit.objects.create(
        user=user,
        place='Дом',
        time=time(8, 0, 0),
        action='Напоминание',
        is_pleasant=False,
        periodicity_days=1,
        reward='',
        duration_seconds=60,
        is_public=False,
    )

    # First run: initialize next_run_at to today 08:00, it's <= now → send once and move by +1 day
    check_and_notify_due_habits()  # celery task is regular callable in tests
    h.refresh_from_db()
    assert calls['count'] == 1
    assert h.last_notified_at == fixed_now
    assert h.next_run_at.date() == (fixed_now + timedelta(days=1)).date()
    assert h.next_run_at.time().hour == 8

    # Second immediate run within idempotency window: should not send again
    check_and_notify_due_habits()
    h.refresh_from_db()
    assert calls['count'] == 1
