from django.contrib import admin

from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'action', 'time', 'place', 'is_pleasant', 'periodicity_days',
        'duration_seconds', 'is_public', 'created_at',
    )
    list_filter = (
        'is_pleasant', 'is_public', 'periodicity_days',
    )
    search_fields = ('action', 'place', 'user__username', 'user__email')
    autocomplete_fields = ('linked_habit',)
    raw_id_fields = ('user',)
    ordering = ('-created_at',)
