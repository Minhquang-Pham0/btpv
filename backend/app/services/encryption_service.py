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
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Generate a secure random password"""
        if length < 8:
            length = 8  # Minimum length for security
        elif length > 128:
            length = 128  # Maximum reasonable length
            
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
            
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)