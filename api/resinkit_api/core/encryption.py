import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from resinkit_api.core.config import settings


# Generate or get encryption key
def get_encryption_key():
    # Use a system environment variable or setting for the secret key
    # In a real system, this would be a securely stored secret
    secret_key = settings.VARIABLE_ENCRYPTION_KEY

    # Derive a key using PBKDF2
    salt = b"resinkit-salt"  # In production, use a secure, randomly-generated salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key


# Encrypt a value
def encrypt_value(value: str) -> str:
    if not value:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()


# Decrypt a value
def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    try:
        # Decode the base64 encrypted value first
        decoded_data = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        # Log the error but don't expose details
        print(f"Error decrypting value: {str(e)}")
        return ""
