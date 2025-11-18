from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from core.utils import generate_uuid, encrypt_data, mask_key, decrypt_data
import uuid


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    secret_key = models.CharField(max_length=255, unique=True, editable=False)
    referral_code = models.CharField(max_length=50, unique=True, editable=False)

    # Subscription fields
    subscription_plan = models.ForeignKey('payments.SubscriptionPlan', on_delete=models.SET_NULL, null=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    webhook_alerts_used = models.IntegerField(default=0)

    # Quantum AI balance
    quantum_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email or self.phone

    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = str(uuid.uuid4())
        if not self.referral_code:
            self.referral_code = f"TRV{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def auth_token(self):
        return RefreshToken.for_user(self).access_token

    @property
    def refresh_token(self):
        return RefreshToken.for_user(self)


class UserManager(models.Manager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('Either email or phone must be provided')

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, password=password, **extra_fields)


