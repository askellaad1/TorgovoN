from django.db import models
from django.utils import timezone
from core.utils import generate_uuid
from users.models import User
from exchanges.models import ExchangeAccount
import uuid


class Bot(models.Model):
    BOT_TYPES = [
        ('custom', 'Custom Bot'),
        ('grid', 'Grid Bot'),
        ('martingale', 'Martingale Bot'),
        ('quantum', 'Quantum AI Bot'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bots')
    bot_type = models.CharField(max_length=20, choices=BOT_TYPES)
    name = models.CharField(max_length=100)
    exchange_account = models.ForeignKey(ExchangeAccount, on_delete=models.CASCADE)
    trading_pair = models.CharField(max_length=20)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    # Bot-specific parameters (JSON for flexibility)
    config = models.JSONField()

    class Meta:
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.bot_type})"


class TradeLog(models.Model):
    BUY_SELL_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='trades')
    exchange = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    amount = models.FloatField()
    buy_sell = models.CharField(max_length=4, choices=BUY_SELL_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    outcome = models.TextField()  # JSON string with success/failure details
    order_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.bot.name} - {self.buy_sell} {self.symbol}"


class WebhookTrigger(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='webhook_triggers')
    secret_key = models.CharField(max_length=255)
    webhook_path = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook for {self.bot.name}"