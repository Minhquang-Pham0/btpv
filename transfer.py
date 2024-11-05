# app/models/entities/password.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...db.base import Base

class Password(Base):
    __tablename__ = "passwords"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    username = Column(String)
    encrypted_password = Column(String)
    encryption_key = Column(String)  # Added field for client-side encryption key
    url = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="passwords")
    
    
    # app/db/migrations/versions/[timestamp]_add_encryption_key.py
"""add encryption key field

Revision ID: [will be generated]
Revises: [previous revision]
Create Date: [timestamp]

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '[will be generated]'
down_revision: Union[str, None] = '[previous revision]'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add encryption_key column to passwords table
    op.add_column('passwords', sa.Column('encryption_key', sa.String(), nullable=True))
    
    # Initially, this can be nullable to allow for migration of existing data
    # After migration is complete, you may want to make it non-nullable

def downgrade() -> None:
    # Remove encryption_key column
    op.drop_column('passwords', 'encryption_key')
    
    // src/services/encryption.js
export class EncryptionService {
  // Convert string to buffer
  static async stringToBuffer(str) {
    const encoder = new TextEncoder();
    return encoder.encode(str);
  }

  // Convert buffer to string
  static async bufferToString(buffer) {
    const decoder = new TextDecoder();
    return decoder.decode(buffer);
  }

  // Convert buffer to base64
  static async bufferToBase64(buffer) {
    const binStr = String.fromCharCode(...new Uint8Array(buffer));
    return btoa(binStr);
  }

  // Convert base64 to buffer
  static async base64ToBuffer(base64) {
    const binStr = atob(base64);
    return Uint8Array.from(binStr, (c) => c.charCodeAt(0));
  }

  // Generate a random encryption key
  static async generateKey() {
    const key = await window.crypto.subtle.generateKey(
      {
        name: "AES-GCM",
        length: 256
      },
      true,
      ["encrypt", "decrypt"]
    );
    
    const exportedKey = await window.crypto.subtle.exportKey("raw", key);
    return await this.bufferToBase64(exportedKey);
  }

  // Import a key from base64
  static async importKey(base64Key) {
    const keyBuffer = await this.base64ToBuffer(base64Key);
    return await window.crypto.subtle.importKey(
      "raw",
      keyBuffer,
      {
        name: "AES-GCM",
        length: 256
      },
      true,
      ["encrypt", "decrypt"]
    );
  }

  // Encrypt data
  static async encrypt(plaintext, base64Key) {
    try {
      const key = await this.importKey(base64Key);
      const iv = window.crypto.getRandomValues(new Uint8Array(12));
      const data = await this.stringToBuffer(plaintext);

      const encrypted = await window.crypto.subtle.encrypt(
        {
          name: "AES-GCM",
          iv: iv
        },
        key,
        data
      );

      // Combine IV and encrypted data
      const combined = new Uint8Array(iv.byteLength + encrypted.byteLength);
      combined.set(new Uint8Array(iv), 0);
      combined.set(new Uint8Array(encrypted), iv.byteLength);

      return await this.bufferToBase64(combined);
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  // Decrypt data
  static async decrypt(encryptedData, base64Key) {
    try {
      const key = await this.importKey(base64Key);
      const combined = await this.base64ToBuffer(encryptedData);
      
      // Split IV and encrypted data
      const iv = combined.slice(0, 12);
      const data = combined.slice(12);

      const decrypted = await window.crypto.subtle.decrypt(
        {
          name: "AES-GCM",
          iv: iv
        },
        key,
        data
      );

      return await this.bufferToString(decrypted);
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
    // Generate a unique encryption key
    const encryptionKey = await EncryptionService.generateKey();
    
    // Encrypt the password
    const encryptedPassword = await EncryptionService.encrypt(
      passwordData.password,
      encryptionKey
    );

    // Create the password entry with encrypted data
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
    console.error('Failed to create password:', error);
    throw error;
  }
};

export const getGroupPasswords = async (groupId) => {
  try {
    const passwords = await authFetch(`/passwords/group/${groupId}`);
    // We don't decrypt passwords until they're needed
    return passwords;
  } catch (error) {
    console.error('Failed to fetch passwords:', error);
    throw error;
  }
};

export const getPassword = async (passwordId) => {
  try {
    const password = await authFetch(`/passwords/${passwordId}`);
    
    // Decrypt the password
    if (password.encrypted_password && password.encryption_key) {
      const decryptedPassword = await EncryptionService.decrypt(
        password.encrypted_password,
        password.encryption_key
      );
      return {
        ...password,
        decrypted_password: decryptedPassword
      };
    }
    
    return password;
  } catch (error) {
    console.error('Failed to fetch password:', error);
    throw error;
  }
};

export const generateSecurePassword = (length = 16) => {
  const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?";
  const array = new Uint8Array(length);
  window.crypto.getRandomValues(array);
  
  let password = '';
  for (let i = 0; i < length; i++) {
    password += charset[array[i] % charset.length];
  }
  return password;
};

import React, { useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Eye, EyeOff, RefreshCw } from 'lucide-react';
import { generateSecurePassword } from '../../services/passwords';

const PasswordForm = ({ onSubmit, groupId }) => {
  const [formData, setFormData] = useState({
    title: '',
    username: '',
    password: '',
    url: '',
    notes: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  
  const handleGeneratePassword = () => {
    const newPassword = generateSecurePassword();
    setFormData(prev => ({
      ...prev,
      password: newPassword
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await onSubmit({
      ...formData,
      group_id: groupId
    });
    setFormData({
      title: '',
      username: '',
      password: '',
      url: '',
      notes: ''
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        placeholder="Title"
        value={formData.title}
        onChange={(e) => setFormData(prev => ({
          ...prev,
          title: e.target.value
        }))}
        required
      />
      
      <Input
        placeholder="Username"
        value={formData.username}
        onChange={(e) => setFormData(prev => ({
          ...prev,
          username: e.target.value
        }))}
        required
      />
      
      <div className="flex gap-2">
        <Input
          type={showPassword ? "text" : "password"}
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData(prev => ({
            ...prev,
            password: e.target.value
          }))}
          required
        />
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowPassword(!showPassword)}
        >
          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={handleGeneratePassword}
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
      
      <Input
        placeholder="URL"
        type="url"
        value={formData.url}
        onChange={(e) => setFormData(prev => ({
          ...prev,
          url: e.target.value
        }))}
      />
      
      <Input
        placeholder="Notes"
        value={formData.notes}
        onChange={(e) => setFormData(prev => ({
          ...prev,
          notes: e.target.value
        }))}
      />
      
      <Button type="submit" className="w-full">
        Save Password
      </Button>
    </form>
  );
};

export default PasswordForm;



    
    