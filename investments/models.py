from django.db import models
from django.utils import timezone
from core.utils import generate_uuid
from users.models import User
import uuid


class QuantumInvestment(models.Model):
    BLOCKCHAIN_CHOICES = [
        ('erc20', 'ERC20 (Ethereum)'),
        ('aptos', 'Aptos'),
        ('trc20', 'TRC20 (Tron)'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quantum_investments')
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    blockchain = models.CharField(max_length=20, choices=BLOCKCHAIN_CHOICES)
    transaction_hash = models.CharField(max_length=255)
    screenshot = models.ImageField(upload_to='investments/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    wallet_address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} USDT"


class QuantumPool(models.Model):
    """Track total invested pool"""
    total_invested = models.DecimalField(max_digits=30, decimal_places=8, default=0.0)
    last_updated = models.DateTimeField(auto_now=True)


class QuantumTradeResult(models.Model):
    """Track admin trades for distribution"""
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    actual_profit_loss = models.DecimalField(max_digits=20, decimal_places=8)
    shown_adjustment = models.DecimalField(max_digits=20, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)