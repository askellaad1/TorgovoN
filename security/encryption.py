"""
Centralized encryption utilities for Torgovo Platform
Provides Fernet encryption, key rotation, and API key masking
"""

import os
import secrets
import string
import re
from typing import Optional
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger('TorgovoN.Security')


class EncryptionManager:
    """Centralized encryption manager with key rotation support"""

    def __init__(self):
        self._current_key = None
        self._fernet = None
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption with proper key management"""
        # Try to get key from settings
        encrypt_key = getattr(settings, 'ENCRYPT_KEY', None)

        if encrypt_key:
            # Use provided key
            if isinstance(encrypt_key, str):
                self._current_key = encrypt_key.encode()
            else:
                self._current_key = encrypt_key
        else:
            # Generate and warn (for development only)
            logger.warning("No ENCRYPT_KEY found in settings. Generating temporary key.")
            self._current_key = Fernet.generate_key()

        try:
            self._fernet = Fernet(self._current_key)
        except Exception as e:
            raise ImproperlyConfigured(f"Failed to initialize encryption: {e}")

    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet encryption"""
        if not data:
            return ""

        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet decryption"""
        if not encrypted_data:
            return ""

        try:
            decrypted_data = self._fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise ValueError(f"Decryption failed: {str(e)}")

    def generate_secure_key(self) -> str:
        """Generate a cryptographically secure encryption key"""
        return Fernet.generate_key().decode()

    def generate_api_key(self, length: int = 32) -> str:
        """Generate secure API key with specific format"""
        # Generate alphanumeric with underscores and hyphens
        charset = string.ascii_letters + string.digits + '_-'
        return ''.join(secrets.choice(charset) for _ in range(length))

    def generate_webhook_secret(self, length: int = 64) -> str:
        """Generate secure webhook secret"""
        # Use URL-safe characters for webhook secrets
        charset = string.ascii_letters + string.digits
        return ''.join(secrets.choice(charset) for _ in range(length))

    def mask_api_key(self, api_key: str) -> str:
        """Mask API key for display (show first 4 and last 4 characters)"""
        if not api_key or len(api_key) < 8:
            return "****"

        start = api_key[:4]
        end = api_key[-4:]
        middle = '*' * (len(api_key) - 8)

        return f"{start}{middle}{end}"

    def validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format (basic alphanumeric with underscores/hyphens)"""
        if not api_key:
            return False

        # Check for allowed characters (alphanumeric, underscore, hyphen)
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, api_key))

    def rotate_key(self, new_key: Optional[str] = None):
        """Rotate encryption key (for scheduled key rotation)"""
        if new_key:
            self._current_key = new_key.encode() if isinstance(new_key, str) else new_key
        else:
            self._current_key = Fernet.generate_key()

        self._fernet = Fernet(self._current_key)
        logger.info("Encryption key rotated successfully")

    def get_current_key_info(self) -> dict:
        """Get information about current encryption key (for admin purposes)"""
        return {
            'key_length': len(self._current_key) if self._current_key else 0,
            'algorithm': 'Fernet (AES-128-CBC with HMAC-SHA256)',
            'is_configured': self._current_key is not None
        }


# Singleton instance
encryption_manager = EncryptionManager()


def encrypt_sensitive_data(data: str) -> str:
    """Convenience function to encrypt sensitive data"""
    return encryption_manager.encrypt_data(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Convenience function to decrypt sensitive data"""
    return encryption_manager.decrypt_data(encrypted_data)


def mask_sensitive_key(key: str) -> str:
    """Convenience function to mask sensitive keys for display"""
    return encryption_manager.mask_api_key(key)


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return encryption_manager.generate_api_key(length)


def validate_encryption_setup():
    """Validate that encryption is properly set up"""
    try:
        test_data = "test_encryption_validation"
        encrypted = encrypt_sensitive_data(test_data)
        decrypted = decrypt_sensitive_data(encrypted)

        if test_data != decrypted:
            logger.error("Encryption validation failed - roundtrip mismatch")
            return False

        logger.info("Encryption setup validated successfully")
        return True
    except Exception as e:
        logger.error(f"Encryption validation failed: {e}")
        return False