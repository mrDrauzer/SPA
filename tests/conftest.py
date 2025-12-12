import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username='u1', password='pass12345')


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    # Obtain JWT token and set auth header
    resp = api_client.post('/api/auth/jwt/create/', {'username': 'u1', 'password': 'pass12345'}, format='json')
    assert resp.status_code == 200, resp.content
    token = resp.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client
