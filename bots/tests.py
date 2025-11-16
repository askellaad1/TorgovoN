import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User, ExchangeAccount
from .models import Bot
from exchanges.models import ExchangeStatus


@pytest.fixture
def exchange_account(user):
    exchange = ExchangeStatus.objects.create(name='binance', is_active=True)
    return ExchangeAccount.objects.create(
        user=user,
        exchange_name='binance',
        api_key_encrypted='test_key',
        api_secret_encrypted='test_secret'
    )


@pytest.mark.django_db
def test_create_bot(api_client, user, exchange_account):
    api_client.force_authenticate(user=user)
    bot_data = {
        "name": "Test Grid Bot",
        "bot_type": "grid",
        "exchange_account_id": str(exchange_account.id),
        "trading_pair": "BTCUSDT",
        "config": {
            "percentage_difference": 2.0,
            "amount_per_level": 100.0,
            "starting_amount": 500.0
        }
    }
    response = api_client.post(reverse('api-bot-create'), bot_data, format='json')
    assert response.status_code == 201
    assert Bot.objects.filter(name="Test Grid Bot").exists()


@pytest.mark.django_db
def test_webhook_validation(api_client, user, exchange_account):
    bot = Bot.objects.create(
        user=user,
        bot_type='custom',
        exchange_account=exchange_account,
        name="Test Custom Bot",
        trading_pair="BTCUSDT",
        config={}
    )
    webhook_path = f"/api/v1/webhooks/custom_bots/{bot.id}/"

    # Invalid secret key
    response = api_client.post(webhook_path, {
        "secret_key": "wrong-secret",
        "buy_sell": "buy",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "amount": 0.001
    }, format='json')
    assert response.status_code == 403

    # Valid secret key
    response = api_client.post(webhook_path, {
        "secret_key": user.secret_key,
        "buy_sell": "buy",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "amount": 0.001
    }, format='json')
    assert response.status_code == 200