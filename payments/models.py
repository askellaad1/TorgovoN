from django.db import models
from django.utils import timezone
from core.utils import generate_uuid
from users.models import User
import uuid


class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic (Free)'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
        ('quantum', 'Quantum AI Access'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    webhook_limit = models.IntegerField(default=50)
    allows_custom_bots = models.BooleanField(default=False)
    allows_grid_bots = models.BooleanField(default=False)
    allows_martingale_bots = models.BooleanField(default=False)
    allows_telegram_signals = models.BooleanField(default=False)
    allows_telegram_alerts = models.BooleanField(default=False)
    allows_quantum_ai = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PaymentMethod(models.Model):
    METHOD_CHOICES = [
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('wise', 'Wise'),
        ('crypto', 'Cryptocurrency'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    purpose = models.CharField(max_length=100)  # e.g., "Bot Subscription", "Quantum AI Investment"
    status = models.CharField(max_length=20, default='pending')
    transaction_hash = models.CharField(max_length=255, null=True, blank=True)
    screenshot = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.method}"