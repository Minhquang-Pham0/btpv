# app/services/encryption_service.py
from cryptography.fernet import Fernet
from base64 import b64encode, b64decode
import secrets
import string
from ..core import settings

class EncryptionService:
    def __init__(self):
        # Convert settings secret key to valid Fernet key
        key = b64encode(settings.SECRET_KEY.encode()[:32].ljust(32, b'='))
        self.fernet = Fernet(key)
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password string"""
        try:
            encrypted = self.fernet.encrypt(password.encode())
            return encrypted.decode()
        except Exception as e:
            raise RuntimeError(f"Password encryption failed: {str(e)}")
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt an encrypted password string"""
        try:
            decrypted = self.fernet.decrypt(encrypted_password.encode())
            return decrypted.decode()
        except Exception as e:
            raise RuntimeError(f"Password decryption failed: {str(e)}")
    