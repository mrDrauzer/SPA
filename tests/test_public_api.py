import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from habits.models import Habit


@pytest.mark.django_db
def test_public_list_and_filter(api_client: APIClient):
    call_command('seed_public_habits')

    # List all public
    resp = api_client.get('/api/habits/public/')
    assert resp.status_code == 200
    total = resp.data.get('count', len(resp.data))
    assert total > 0

    # Filter by substring that should match at least one item (e.g., вода)
    resp_q = api_client.get('/api/habits/public/?q=вода')
    assert resp_q.status_code == 200
    # Either paginated or plain list
    items = resp_q.data.get('results', resp_q.data)
    assert any('выпить' in i['action'].lower() or 'вода' in i['action'].lower() for i in items)


@pytest.mark.django_db
def test_adopt_template_and_clone_linked(auth_client: APIClient, user):
    call_command('seed_public_habits')

    # Find a useful public template that has a pleasant linked habit
    template = (
        Habit.objects
        .select_related('linked_habit', 'user')
        .filter(is_public=True, is_pleasant=False, linked_habit__isnull=False, user__username='public')
        .first()
    )
    assert template is not None
    assert template.linked_habit is not None and template.linked_habit.is_pleasant

    # Adopt
    url = f'/api/habits/public/{template.id}/adopt/'
    resp = auth_client.post(url)
    assert resp.status_code == 201, resp.content
    created_id = resp.data['id']

    # Created habit belongs to current user and is not public
    created = Habit.objects.get(id=created_id)
    assert created.user_id == user.id
    assert created.is_public is False

    # Linked pleasant habit should be cloned for the same user
    assert created.linked_habit is not None
    assert created.linked_habit.user_id == user.id
    assert created.linked_habit.is_pleasant is True
