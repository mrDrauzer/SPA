import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from habits.models import Habit


@pytest.mark.django_db
def test_is_public_field_is_read_only_in_crud(auth_client: APIClient):
    payload = {
        'place': 'Кухня',
        'time': '07:00:00',
        'action': 'Тест привычка',
        'is_pleasant': False,
        'periodicity_days': 1,
        'reward': '',
        'duration_seconds': 60,
        'is_public': True,  # попытка принудительно сделать публичной
    }
    resp = auth_client.post('/api/habits/', payload, format='json')
    assert resp.status_code == 201, resp.content
    assert resp.data['is_public'] is False  # поле проигнорировано сериализатором


@pytest.mark.django_db
def test_forbid_update_delete_public_templates_owned_by_public_user(auth_client: APIClient):
    # Засеять публичные шаблоны пользователя "public"
    call_command('seed_public_habits')
    # Попробуем удалить чужой публичный шаблон по его ID —
    # он не попадает в queryset (отфильтрован по пользователю), ожидаем 404
    template = Habit.objects.filter(is_public=True).first()
    assert template is not None
    del_resp = auth_client.delete(f'/api/habits/{template.id}/')
    assert del_resp.status_code == 404


@pytest.mark.django_db
def test_forbid_update_delete_if_own_habit_marked_public(auth_client: APIClient, user):
    # Создадим привычку текущего пользователя и вручную проставим is_public=True
    own_public = Habit.objects.create(
        user=user,
        place='Дом',
        time='08:00',
        action='Публичная (своя) для проверки защиты',
        is_pleasant=False,
        periodicity_days=1,
        reward='',
        duration_seconds=60,
        is_public=True,
    )

    # PATCH должен вернуть 403 (perform_update защищает публичные)
    patch_resp = auth_client.patch(
        f'/api/habits/{own_public.id}/',
        {'action': 'Новый текст'},
        format='json',
    )
    assert patch_resp.status_code == 403

    # DELETE также 403 (perform_destroy защищает публичные)
    del_resp = auth_client.delete(f'/api/habits/{own_public.id}/')
    assert del_resp.status_code == 403
