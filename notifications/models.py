from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram',
        verbose_name='Пользователь',
    )
    chat_id = models.BigIntegerField(unique=True, verbose_name='Chat ID')
    username = models.CharField(max_length=255, blank=True, verbose_name='Username')
    linked_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата привязки')

    class Meta:
        verbose_name = 'Telegram профиль'
        verbose_name_plural = 'Telegram профили'

    def __str__(self):
        return f"{self.user} ↔ {self.chat_id}"


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_link_tokens',
        verbose_name='Пользователь',
    )
    code = models.CharField(max_length=64, unique=True, verbose_name='Код привязки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    expires_at = models.DateTimeField(verbose_name='Годен до')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='Использован в')

    class Meta:
        verbose_name = 'Код привязки Telegram'
        verbose_name_plural = 'Коды привязки Telegram'
        indexes = [models.Index(fields=['code'])]

    def __str__(self):
        state = 'used' if self.used_at else 'active'
        return f"{self.user} | {self.code} ({state})"
