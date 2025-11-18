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
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['bot_type']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.name} ({self.bot_type})"


class Order(models.Model):
    """Order model for tracking individual trade orders placed by bots"""
    ORDER_TYPES = [
        ('market', 'Market'),
        ('limit', 'Limit'),
    ]

    CATEGORIES = [
        ('spot', 'Spot'),
        ('futures', 'Futures'),
        ('swap', 'Swap'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    Pair = models.CharField(max_length=20, db_index=True)
    Category = models.CharField(max_length=20, choices=CATEGORIES, default='futures')
    Order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='market')
    Side = models.CharField(max_length=10)  # buy/sell
    Quantity = models.DecimalField(max_digits=20, decimal_places=8)
    Price = models.DecimalField(max_digits=20, decimal_places=8)
    Exchange = models.CharField(max_length=50, default='Bybit')
    Description = models.TextField(null=True, blank=True)
    Details = models.JSONField(default=dict)
    executed_at = models.DateTimeField(auto_now_add=True)
    filled = models.BooleanField(default=False)

    # Optional reference to indicator snapshot
    Indicators = models.OneToOneField('Indicator', on_delete=models.SET_NULL, null=True, blank=True, related_name='order')

    # PairConfig reference (from bot config)
    PairConfig_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'executed_at']),
            models.Index(fields=['bot', 'executed_at']),
            models.Index(fields=['Pair']),
            models.Index(fields=['Side']),
            models.Index(fields=['filled']),
        ]

    def __str__(self):
        return f"{self.Side} {self.Quantity} {self.Pair} @ {self.Price}"


class Indicator(models.Model):
    """Technical indicators snapshot for order analysis"""
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='indicators')
    Pair = models.CharField(max_length=20, db_index=True)
    EMA = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    RSI = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    Prev_RSI = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    Color = models.CharField(max_length=20, null=True, blank=True)  # RSI color
    Prev_Color = models.CharField(max_length=20, null=True, blank=True)  # Previous RSI color
    BB = models.CharField(max_length=100, null=True, blank=True)  # Bollinger Bands description
    TSI = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ADX = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['Pair']),
        ]

    def __str__(self):
        return f"Indicators for {self.Pair} at {self.timestamp}"


class TradeLog(models.Model):
    BUY_SELL_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    OUTCOMES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('partial', 'Partial'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='trades')
    exchange = models.CharField(max_length=50, db_index=True)
    symbol = models.CharField(max_length=20, db_index=True)
    amount = models.FloatField()
    buy_sell = models.CharField(max_length=4, choices=BUY_SELL_CHOICES, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    outcome = models.TextField()  # JSON string with success/failure details
    order_id = models.CharField(max_length=255, null=True, blank=True)
    outcome_type = models.CharField(max_length=20, choices=OUTCOMES, default='success')

    # Additional fields for better tracking
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    fees = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['bot', 'timestamp']),
            models.Index(fields=['symbol']),
            models.Index(fields=['outcome_type']),
        ]

    def __str__(self):
        return f"{self.bot.name} - {self.buy_sell} {self.symbol}"


class WebhookTrigger(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='webhook_triggers')
    secret_key = models.CharField(max_length=255, db_index=True)
    webhook_path = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Webhook for {self.bot.name}"