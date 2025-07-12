import time
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os


class CryptoManager:
    def __init__(self, private_key):
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.shared_keys = {}

    def derive_shared_key(self, peer_public_key):
        # Создаем уникальный ключ для каждой пары
        key_id = hashlib.sha256(
            peer_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).digest()

        if key_id in self.shared_keys:
            return self.shared_keys[key_id]

        # ECDH обмен ключами
        shared_key = self.private_key.exchange(ec.ECDH(), peer_public_key)

        # HKDF для получения ключа фиксированной длины
        derived_key = hashlib.pbkdf2_hmac(
            'sha256',
            shared_key,
            b'chat-app-salt',
            100000,
            32  # 256-битный ключ для AES
        )

        self.shared_keys[key_id] = derived_key
        return derived_key

    def encrypt_message(self, peer_public_key, message):
        key = self.derive_shared_key(peer_public_key)
        iv = os.urandom(16)

        # Шифрование
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # PKCS7 паддинг
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return iv + ciphertext

    def decrypt_message(self, peer_public_key, encrypted_data):
        try:
            key = self.derive_shared_key(peer_public_key)
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]

            # Дешифрование
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()

            # Удаление паддинга
            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded_data) + unpadder.finalize()
        except Exception as e:
            time.sleep(0.5)  # Защита от timing-атак
            print(f"Decryption error: {str(e)}")
            raise ValueError("Decryption failed") from e
