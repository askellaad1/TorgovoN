from django.db import models
from django.conf import settings
from core.utils import generate_uuid, mask_key
from cryptography.fernet import Fernet
import base64
import re


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
    exchange_name = models.CharField(max_length=50)
    api_key_encrypted = models.TextField()
    api_secret_encrypted = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.exchange_status.name}"

    @property
    def masked_api_key(self):
        try:
            decrypted = self.decrypt_api_key(self.api_key_encrypted)
            return mask_key(decrypted)
        except Exception:
            return "****"

    def encrypt_api_key(self, api_key):
        """Encrypt API key using Fernet encryption"""
        if not api_key:
            raise ValueError("API key cannot be empty")

        # Validate API key format (basic alphanumeric with possible underscores/hyphens)
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            raise ValueError("Invalid API key format")

        try:
            # Get encryption key from settings or generate a default
            key = getattr(settings, 'ENCRYPT_KEY', Fernet.generate_key())
            if isinstance(key, str):
                key = key.encode()

            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(api_key.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt API key: {str(e)}")

    def decrypt_api_key(self, encrypted_key):
        """Decrypt API key using Fernet decryption"""
        if not encrypted_key:
            return ""

        try:
            # Handle legacy format (starting with 'gAAAAA')
            if encrypted_key.startswith('gAAAAA'):
                # Use legacy decryption method if available
                from core.utils import decrypt_data
                return decrypt_data(encrypted_key)

            # Use new Fernet decryption
            key = getattr(settings, 'ENCRYPT_KEY', Fernet.generate_key())
            if isinstance(key, str):
                key = key.encode()

            fernet = Fernet(key)
            encrypted_data = base64.b64decode(encrypted_key.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception:
            raise ValueError("Failed to decrypt API key - invalid format or corrupted data")

    def save(self, *args, **kwargs):
        # Encrypt API keys before saving if they're not already encrypted
        if self.api_key_encrypted and not self.api_key_encrypted.startswith(('gAAAAA', 'eyJ')):
            self.api_key_encrypted = self.encrypt_api_key(self.api_key_encrypted)

        if self.api_secret_encrypted and not self.api_secret_encrypted.startswith(('gAAAAA', 'eyJ')):
            self.api_secret_encrypted = self.encrypt_api_key(self.api_secret_encrypted)

        super().save(*args, **kwargs)