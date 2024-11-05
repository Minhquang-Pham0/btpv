// src/services/encryption.js
import { Buffer } from 'buffer';

class EncryptionService {
  // Generate a random key for encryption
  static generateKey() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Buffer.from(array).toString('base64');
  }

  // Encrypt data using AES-GCM
  static async encrypt(plaintext, key) {
    try {
      // Convert base64 key to ArrayBuffer
      const keyBuffer = Buffer.from(key, 'base64');
      const iv = crypto.getRandomValues(new Uint8Array(12));
      
      // Import the key
      const cryptoKey = await crypto.subtle.importKey(
        'raw',
        keyBuffer,
        'AES-GCM',
        false,
        ['encrypt']
      );

      // Encrypt the data
      const encodedText = new TextEncoder().encode(plaintext);
      const encryptedData = await crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        cryptoKey,
        encodedText
      );

      // Combine IV and encrypted data and convert to base64
      const combined = new Uint8Array(iv.length + encryptedData.byteLength);
      combined.set(iv);
      combined.set(new Uint8Array(encryptedData), iv.length);
      
      return Buffer.from(combined).toString('base64');
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  // Decrypt data using AES-GCM
  static async decrypt(encryptedData, key) {
    try {
      // Convert base64 data to ArrayBuffer
      const combined = Buffer.from(encryptedData, 'base64');
      const keyBuffer = Buffer.from(key, 'base64');
      
      // Extract IV and encrypted data
      const iv = combined.slice(0, 12);
      const data = combined.slice(12);

      // Import the key
      const cryptoKey = await crypto.subtle.importKey(
        'raw',
        keyBuffer,
        'AES-GCM',
        false,
        ['decrypt']
      );

      // Decrypt the data
      const decryptedData = await crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        cryptoKey,
        data
      );

      return new TextDecoder().decode(decryptedData);
    } catch (error) {
      console.error('Decryption error:', error);
      throw new Error('Failed to decrypt data');
    }
  }
}

export default EncryptionService;



// src/services/passwords.js
import authFetch from './api';
import EncryptionService from './encryption';

export const createPassword = async (passwordData) => {
  try {
    // Generate a unique encryption key for this password
    const encryptionKey = EncryptionService.generateKey();
    
    // Encrypt the password before sending
    const encryptedPassword = await EncryptionService.encrypt(
      passwordData.password,
      encryptionKey
    );

    // Send encrypted password and key separately
    const response = await authFetch('/passwords', {
      method: 'POST',
      body: JSON.stringify({
        ...passwordData,
        password: encryptedPassword,
        encryption_key: encryptionKey
      }),
    });

    return response;
  } catch (error) {
    console.error('Error creating password:', error);
    throw error;
  }
};

export const getPassword = async (passwordId) => {
  try {
    const response = await authFetch(`/passwords/${passwordId}`);
    
    // Decrypt the password using the stored encryption key
    if (response.encrypted_password && response.encryption_key) {
      const decryptedPassword = await EncryptionService.decrypt(
        response.encrypted_password,
        response.encryption_key
      );
      return {
        ...response,
        password: decryptedPassword
      };
    }
    
    return response;
  } catch (error) {
    console.error('Error retrieving password:', error);
    throw error;
  }
};



from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends
from ..models.entities import Password, User, Group
from ..models.schemas import PasswordCreate, PasswordUpdate
from ..core.exceptions import NotFoundError, PermissionDenied
from ..db import get_db
from .encryption_service import EncryptionService

class PasswordService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        encryption: EncryptionService = Depends()
    ):
        self.db = db
        self.encryption = encryption

    async def create_password(self, password_data: PasswordCreate, current_user: User) -> Password:
        """Create a new password entry"""
        # Verify user is member of the group
        group = await self._verify_group_access(password_data.group_id, current_user)
        
        # Store the already-encrypted password and encryption key
        password = Password(
            title=password_data.title,
            username=password_data.username,
            encrypted_password=password_data.password,  # Already encrypted by client
            encryption_key=password_data.encryption_key,  # Store the encryption key
            url=password_data.url,
            notes=password_data.notes,
            group_id=group.id
        )
        
        self.db.add(password)
        self.db.commit()
        self.db.refresh(password)
        return password

    async def get_password(self, password_id: int, current_user: User) -> Password:
        """Get a password entry"""
        password = self.db.query(Password).filter(Password.id == password_id).first()
        if not password:
            raise NotFoundError("Password not found")
            
        # Verify access
        await self._verify_group_access(password.group_id, current_user)
        
        # Return the encrypted password and encryption key for client-side decryption
        return password

    # ... rest of the service methods remain the same ...
    
    
    from pydantic import BaseModel, AnyUrl
from typing import Optional
from datetime import datetime

class PasswordBase(BaseModel):
    title: str
    username: str
    url: Optional[AnyUrl] = None
    notes: Optional[str] = None

class PasswordCreate(PasswordBase):
    password: str  # This will now contain the client-encrypted password
    encryption_key: str  # Client-generated encryption key
    group_id: int

class PasswordUpdate(BaseModel):
    title: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Client-encrypted password
    encryption_key: Optional[str] = None  # New encryption key if password is changed
    url: Optional[AnyUrl] = None
    notes: Optional[str] = None

class Password(PasswordBase):
    id: int
    group_id: int
    encrypted_password: str
    encryption_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    



