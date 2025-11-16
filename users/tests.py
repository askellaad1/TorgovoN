import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from .models import User
from .serializers import UserRegistrationSerializer

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "securepass123",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.mark.django_db
def test_user_registration(api_client, user_data):
    response = api_client.post(reverse('api-user-register'), user_data, format='json')
    assert response.status_code == 201
    assert 'user_id' in response.data
    assert 'webhook_url' in response.data
    assert User.objects.filter(email=user_data['email']).exists()

@pytest.mark.django_db
def test_login(api_client, user_data):
    user = User.objects.create_user(**user_data)
    response = api_client.post(reverse('api-user-login'), {
        "email": user_data['email'],
        "password": user_data['password']
    }, format='json')
    assert response.status_code == 200
    assert 'access_token' in response.data

@pytest.mark.django_db
def test_dashboard_authenticated(api_client, user_data):
    user = User.objects.create_user(**user_data)
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('api-user-dashboard'))
    assert response.status_code == 200
    assert response.data['email'] == user_data['email']