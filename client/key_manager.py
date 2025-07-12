import os
import hashlib  # Добавьте этот импорт

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def get_user_id(username):
    """Генерирует user_id как первые 16 байт SHA256 хеша имени"""
    return hashlib.sha256(username.encode()).digest()[:16]


def load_or_generate_keys(username):
    user_id = get_user_id(username)
    key_file = f"{username}.key"

    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return user_id, serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
    else:
        private_key = ec.generate_private_key(
            ec.SECP384R1(),
            default_backend()
        )
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        return user_id, private_key
