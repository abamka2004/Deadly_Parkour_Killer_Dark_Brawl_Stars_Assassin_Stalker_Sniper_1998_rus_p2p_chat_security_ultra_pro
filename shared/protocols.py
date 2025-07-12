import json
import hmac
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


def encrypt_message(key, message):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    hmac_tag = hmac.new(key, ciphertext, 'sha256').digest()
    return iv + ciphertext + hmac_tag


def decrypt_message(key, encrypted_data):
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    received_tag = encrypted_data[-32:]

    # Проверка HMAC
    expected_tag = hmac.new(key, ciphertext, 'sha256').digest()
    if not hmac.compare_digest(received_tag, expected_tag):
        raise ValueError("HMAC verification failed")

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()


class MessageProtocol:
    @staticmethod
    def encode_register(user_id, public_key, username):
        return json.dumps({
            'action': 'register',
            'user_id': user_id.hex(),
            'public_key': public_key,
            'username': username
        }).encode()

    @staticmethod
    def encode_message(sender_id, encrypted_message):
        return json.dumps({
            'sender_id': sender_id.hex(),
            'encrypted_message': encrypted_message.hex()
        }).encode()

    @staticmethod
    def decode(data):
        return json.loads(data.decode())
