from django.db import models
from core.utils import generate_uuid


class ExchangeStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  # binance, bybit, etc.
    is_active = models.BooleanField(default=True)
    ccxt_config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ExchangeErrorLog(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user_id = models.UUIDField()
    exchange = models.CharField(max_length=50)
    error_message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exchange} error for {self.user_id}"


class ExchangeAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='exchange_accounts')
    exchange_status = models.ForeignKey(ExchangeStatus, on_delete=models.PROTECT)
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.exchange_status.name}"