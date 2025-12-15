from django.contrib import admin

from .models import TelegramProfile, TelegramLinkToken


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'chat_id', 'username', 'linked_at')
    search_fields = ('user__username', 'user__email', 'chat_id', 'username')
    raw_id_fields = ('user',)
    ordering = ('-linked_at',)


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'created_at', 'expires_at', 'used_at')
    search_fields = ('user__username', 'user__email', 'code')
    list_filter = ('used_at',)
    raw_id_fields = ('user',)
    ordering = ('-created_at',)
