from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .validators import (
    validate_duration_seconds,
    validate_periodicity_days,
)


class Habit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='habits', verbose_name='Пользователь')
    place = models.CharField(max_length=255, verbose_name='Место')
    time = models.TimeField(verbose_name='Время')
    action = models.CharField(max_length=255, verbose_name='Действие')

    is_pleasant = models.BooleanField(default=False, verbose_name='Приятная привычка')
    linked_habit = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='linked_with', verbose_name='Связанная привычка')

    periodicity_days = models.PositiveSmallIntegerField(default=1, validators=[validate_periodicity_days], verbose_name='Периодичность (дни)')
    reward = models.CharField(max_length=255, blank=True, verbose_name='Вознаграждение')
    duration_seconds = models.PositiveSmallIntegerField(default=60, validators=[validate_duration_seconds], verbose_name='Время на выполнение (сек)')

    is_public = models.BooleanField(default=False, verbose_name='Публичная')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} @ {self.time} ({'приятная' if self.is_pleasant else 'полезная'})"

    def clean(self):
        # Периодичность ограничена валидатором validate_periodicity_days

        # Время на выполнение ограничено validate_duration_seconds

        # Исключить одновременный выбор связанной привычки и указания вознаграждения
        if self.reward and self.linked_habit:
            raise ValidationError('Нельзя одновременно указывать вознаграждение и связанную привычку.')

        # В связанные привычки могут попадать только привычки с признаком приятной
        if self.linked_habit and not self.linked_habit.is_pleasant:
            raise ValidationError('Связанной может быть только приятная привычка.')

        # У приятной привычки не может быть вознаграждения или связанной привычки
        if self.is_pleasant:
            if self.reward:
                raise ValidationError('У приятной привычки не должно быть вознаграждения.')
            if self.linked_habit is not None:
                raise ValidationError('У приятной привычки не должно быть связанной привычки.')

        # Нельзя выполнять привычку реже, чем 1 раз в 7 дней — обеспечено валидатором диапазона
