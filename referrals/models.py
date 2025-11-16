from django.db import models
from django.utils import timezone
from core.utils import generate_uuid
from users.models import User
import uuid


class Referral(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referred = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    code_used = models.CharField(max_length=50)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    claimed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['referrer', 'referred']

    def __str__(self):
        return f"{self.referrer.email} referred {self.referred.email}"


class ReferralBonusConfig(models.Model):
    bonus_type = models.CharField(max_length=20, choices=[
        ('alerts', 'Free Alerts'),
        ('discount', 'Discount Percentage'),
        ('usdt', 'USDT Equivalent'),
    ])
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)