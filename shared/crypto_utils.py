from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )


def deserialize_public_key(serialized_key):
    try:
        # Пробуем PEM формат
        return serialization.load_pem_public_key(
            serialized_key,
            backend=default_backend()
        )
    except ValueError:
        # Если не PEM, пробуем DER
        try:
            return serialization.load_der_public_key(
                serialized_key,
                backend=default_backend()
            )
        except ValueError as e:
            raise ValueError("Failed to deserialize key in both PEM and DER formats") from e
