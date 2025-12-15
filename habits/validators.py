from django.core.exceptions import ValidationError


MAX_DURATION_SECONDS = 120
MIN_PERIOD_DAYS = 1
MAX_PERIOD_DAYS = 7


def validate_duration_seconds(value: int):
    if value is None:
        return
    if value > MAX_DURATION_SECONDS:
        raise ValidationError(f"Время на выполнение не должно превышать {MAX_DURATION_SECONDS} секунд.")


def validate_periodicity_days(value: int):
    if value < MIN_PERIOD_DAYS or value > MAX_PERIOD_DAYS:
        raise ValidationError("Периодичность должна быть от 1 до 7 дней (не реже одного раза в неделю).")
