# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Encryption utilities for sensitive data at rest.

Uses Fernet (symmetric encryption) from cryptography library for encrypting
sensitive fields like API keys in the database.
"""
from django.db import models
from cryptography.fernet import Fernet
from decouple import config
import base64
import logging

logger = logging.getLogger(__name__)


class EncryptedCharField(models.CharField):
    """
    A CharField that encrypts data before storing in database and decrypts on retrieval.
    
    Uses Fernet (AES-128 in CBC mode) symmetric encryption.
    Encryption key is derived from environment variable: ENCRYPTION_KEY
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure max_length is sufficient for encrypted data (base64 encoded)
        # Encrypted data is approximately 33% larger than plaintext
        if self.max_length and self.max_length < 100:
            logger.warning(
                f"EncryptedCharField {self.name} max_length={self.max_length} may be too small. "
                "Encrypted data is ~33% larger than plaintext."
            )
    
    def get_cipher_suite(self):
        """Get or create Fernet cipher suite from environment encryption key."""
        encryption_key = config('ENCRYPTION_KEY', default=None)
        
        if not encryption_key:
            # In development, generate a consistent key from SECRET_KEY
            # In production, ENCRYPTION_KEY must be set
            from django.conf import settings
            encryption_key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode())[:44].decode()
            logger.warning(
                'ENCRYPTION_KEY not configured. Using derived key from SECRET_KEY. '
                'Set ENCRYPTION_KEY environment variable in production!'
            )
        
        # Ensure key is properly formatted for Fernet
        try:
            # If key is not valid base64, encode it
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            Fernet(encryption_key)  # Validate
            return Fernet(encryption_key)
        except Exception:
            # Key is not valid Fernet key, derive one from it
            derived_key = base64.urlsafe_b64encode(encryption_key[:32] if isinstance(encryption_key, bytes) else encryption_key[:32].encode())
            return Fernet(derived_key)
    
    def get_prep_value(self, value):
        """Encrypt value before storing in database."""
        if value is None or value == '':
            return value
        
        cipher_suite = self.get_cipher_suite()
        encrypted = cipher_suite.encrypt(value.encode() if isinstance(value, str) else value)
        return encrypted.decode()
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None or value == '':
            return value
        
        try:
            cipher_suite = self.get_cipher_suite()
            decrypted = cipher_suite.decrypt(value.encode() if isinstance(value, str) else value)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt field {self.name}: {e}")
            # Return value as-is if decryption fails (might be unencrypted legacy data)
            return value


class EncryptedTextField(models.TextField):
    """
    A TextField that encrypts data before storing in database and decrypts on retrieval.
    
    Same encryption as EncryptedCharField but for longer text content.
    """
    
    def get_cipher_suite(self):
        """Get or create Fernet cipher suite from environment encryption key."""
        encryption_key = config('ENCRYPTION_KEY', default=None)
        
        if not encryption_key:
            from django.conf import settings
            encryption_key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode())[:44].decode()
            logger.warning(
                'ENCRYPTION_KEY not configured. Using derived key from SECRET_KEY. '
                'Set ENCRYPTION_KEY environment variable in production!'
            )
        
        try:
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            Fernet(encryption_key)
            return Fernet(encryption_key)
        except Exception:
            derived_key = base64.urlsafe_b64encode(encryption_key[:32] if isinstance(encryption_key, bytes) else encryption_key[:32].encode())
            return Fernet(derived_key)
    
    def get_prep_value(self, value):
        """Encrypt value before storing in database."""
        if value is None or value == '':
            return value
        
        cipher_suite = self.get_cipher_suite()
        encrypted = cipher_suite.encrypt(value.encode() if isinstance(value, str) else value)
        return encrypted.decode()
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None or value == '':
            return value
        
        try:
            cipher_suite = self.get_cipher_suite()
            decrypted = cipher_suite.decrypt(value.encode() if isinstance(value, str) else value)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt field {self.name}: {e}")
            return value
