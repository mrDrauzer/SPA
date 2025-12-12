from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from celery import shared_task

from .models import Habit
from notifications.services import send_telegram_message


def calc_next_run(habit_time, periodicity_days: int, now=None):
    """Return timezone-aware datetime for the next run.

    - If today's time hasn't passed yet, schedule for today at `habit_time`.
    - Otherwise, schedule for today + `periodicity_days` at `habit_time`.
    """
    if now is None:
        now = timezone.now()

    # Build today's datetime at habit_time in the same timezone
    tz = timezone.get_current_timezone()
    today_dt = timezone.make_aware(
        datetime(now.year, now.month, now.day, habit_time.hour, habit_time.minute, habit_time.second),
        tz,
    )

    # If today's time hasn't passed yet (including equality), schedule for today.
    # Otherwise, move by `periodicity_days`.
    if now <= today_dt:
        return today_dt
    return today_dt + timedelta(days=int(periodicity_days))


@shared_task
def check_and_notify_due_habits():
    """Select due habits and send Telegram notifications.

    Rules:
    - Skip public templates and any habits owned by the `public` user.
    - Use a small idempotency window to avoid duplicates if the task overlaps.
    - After sending, update `last_notified_at` and recalc `next_run_at`.
    - If `next_run_at` is null, initialize it via `calc_next_run`.
    """
    now = timezone.now()
    window_seconds = 90

    qs = (
        Habit.objects
        .select_related('user')
        .filter(is_public=False)
        .exclude(user__username='public')
    )

    # Initialize next_run_at for habits where it's not set
    to_init = qs.filter(next_run_at__isnull=True)
    for h in to_init:
        h.next_run_at = calc_next_run(h.time, h.periodicity_days, now=now)
        h.save(update_fields=['next_run_at'])

    # Now pick due habits
    due = qs.filter(next_run_at__lte=now)
    for h in due:
        # Idempotency window
        if h.last_notified_at and (now - h.last_notified_at).total_seconds() < window_seconds:
            # Too soon since the last notification
            continue

        # Prepare message
        time_str = h.time.strftime('%H:%M') if h.time else ''
        place_str = f" в месте: {h.place}" if h.place else ''
        text = f"Напоминание о привычке:\n• {h.action}{place_str}\n⏰ {time_str}"

        sent = send_telegram_message(h.user, text)
        # Regardless of sent result, move the schedule to avoid spamming
        h.last_notified_at = now if sent else h.last_notified_at or now
        # Advance reference time by 1 second to ensure next run moves to the future day
        h.next_run_at = calc_next_run(h.time, h.periodicity_days, now=now + timedelta(seconds=1))
        h.save(update_fields=['last_notified_at', 'next_run_at'])
