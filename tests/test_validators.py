import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from habits.models import Habit


@pytest.mark.django_db
def test_reward_and_linked_cannot_be_together(auth_client: APIClient, user):
    # Prepare a pleasant habit to link to (owned by same user)
    pleasant = Habit.objects.create(
        user=user,
        place='Дом',
        time='10:00',
        action='Отдых',
        is_pleasant=True,
        periodicity_days=1,
        reward='',
        duration_seconds=60,
        is_public=False,
    )

    payload = {
        'place': 'Работа',
        'time': '11:00:00',
        'action': 'Полезная с конфликтом',
        'is_pleasant': False,
        'linked_habit': pleasant.id,
        'periodicity_days': 1,
        'reward': 'конфликт',
        'duration_seconds': 60,
    }
    resp = auth_client.post('/api/habits/', payload, format='json')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_pleasant_cannot_have_reward_or_link(auth_client: APIClient, user):
    # Reward not allowed
    resp1 = auth_client.post('/api/habits/', {
        'place': 'Дом', 'time': '09:00:00', 'action': 'Приятная с наградой',
        'is_pleasant': True, 'periodicity_days': 1, 'reward': 'не должно быть', 'duration_seconds': 60,
    }, format='json')
    assert resp1.status_code == 400

    # Linked habit not allowed
    another = Habit.objects.create(
        user=user, place='Где-то', time='08:00', action='Другая', is_pleasant=True,
        periodicity_days=1, reward='', duration_seconds=60,
    )
    resp2 = auth_client.post('/api/habits/', {
        'place': 'Дом', 'time': '09:30:00', 'action': 'Приятная со связью',
        'is_pleasant': True, 'periodicity_days': 1, 'reward': '', 'duration_seconds': 60,
        'linked_habit': another.id,
    }, format='json')
    assert resp2.status_code == 400


@pytest.mark.django_db
def test_linked_must_be_pleasant(auth_client: APIClient, user):
    # Create a non-pleasant habit to (incorrectly) link to
    wrong = Habit.objects.create(
        user=user, place='Офис', time='12:00', action='Не приятная', is_pleasant=False,
        periodicity_days=1, reward='', duration_seconds=60,
    )
    resp = auth_client.post('/api/habits/', {
        'place': 'Дом', 'time': '13:00:00', 'action': 'Связь на не-приятную',
        'is_pleasant': False, 'periodicity_days': 1, 'reward': '', 'duration_seconds': 60,
        'linked_habit': wrong.id,
    }, format='json')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_linked_must_belong_to_same_user(auth_client: APIClient, user):
    # Create another user and a pleasant habit owned by them
    Other = get_user_model()
    other_user = Other.objects.create_user(username='u2', password='pass12345')
    foreign_pleasant = Habit.objects.create(
        user=other_user, place='Парк', time='15:00', action='Чужая приятная', is_pleasant=True,
        periodicity_days=1, reward='', duration_seconds=60,
    )
    resp = auth_client.post('/api/habits/', {
        'place': 'Дом', 'time': '16:00:00', 'action': 'Связь на чужую',
        'is_pleasant': False, 'periodicity_days': 1, 'reward': '', 'duration_seconds': 60,
        'linked_habit': foreign_pleasant.id,
    }, format='json')
    assert resp.status_code == 400
