import asyncio
import sys
from aiohttp import ClientSession, ClientError
from cryptography.hazmat.primitives import serialization

from shared.crypto_utils import deserialize_public_key
from crypto import CryptoManager
from key_manager import load_or_generate_keys, get_user_id
from shared.protocols import MessageProtocol
from shared.utils import format_message


async def receive_messages(base_url, user_id, crypto, peer_public_key):
    last_id = 0
    async with ClientSession() as session:
        while True:
            try:
                url = f"{base_url}/messages?user_id={user_id.hex()}&last_id={last_id}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        messages = await resp.json()
                        for msg in messages:
                            # Получаем имя отправителя
                            sender_id = bytes.fromhex(msg['sender_id'])
                            async with session.get(
                                    f"{base_url}/user_public_key?user_id={sender_id.hex()}") as user_resp:
                                if user_resp.status == 200:
                                    # Запрашиваем имя пользователя
                                    async with session.get(
                                            f"{base_url}/user_info?user_id={sender_id.hex()}") as info_resp:
                                        if info_resp.status == 200:
                                            user_info = await info_resp.json()
                                            sender_name = user_info['username']
                                        else:
                                            sender_name = "Unknown"
                                else:
                                    sender_name = "Unknown"

                            encrypted = bytes.fromhex(msg['encrypted_message'])
                            decrypted = crypto.decrypt_message(peer_public_key, encrypted)
                            print(format_message({
                                'sender_name': sender_name,  # Используем имя вместо ID
                                'text': decrypted.decode(),
                                'timestamp': msg['timestamp']
                            }))
                            last_id = max(last_id, msg['id'])
                    elif resp.status != 404:
                        error = await resp.text()
                        print(f"\nServer error ({resp.status}): {error}")
            except ClientError as e:
                print(f"\nNetwork error: {str(e)}")
            except Exception as e:
                print(f"\nUnknown error: {str(e)}")
            await asyncio.sleep(0.3)


async def send_messages(base_url, user_id, crypto, peer_id, peer_public_key):
    async with ClientSession() as session:
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    continue

                text = line.rstrip('\n')
                if not text.strip():
                    continue

                encrypted = crypto.encrypt_message(peer_public_key, text)
                data = {
                    'sender_id': user_id.hex(),
                    'recipient_id': peer_id.hex(),
                    'encrypted_message': encrypted.hex()
                }
                async with session.post(f"{base_url}/message", json=data) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        print(f"Send error ({resp.status}): {error}")
            except Exception as e:
                print(f"Error: {str(e)}")


async def main():
    if len(sys.argv) < 3:
        print("Usage: python client.py <your_name> <peer_name> [server_url]")
        return

    username = sys.argv[1]
    peer_name = sys.argv[2]
    base_url = sys.argv[3] if len(sys.argv) > 3 else 'http://localhost:8080'

    # Генерация ключей
    user_id, private_key = load_or_generate_keys(username)
    crypto = CryptoManager(private_key)

    # ID собеседника
    peer_id = get_user_id(peer_name)

    async with ClientSession() as session:
        # Регистрация
        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        register_data = MessageProtocol.encode_register(
            user_id,
            public_key_bytes.decode('utf-8'),
            username
        )
        async with session.post(f"{base_url}/register", data=register_data) as resp:
            if resp.status != 200:
                print(f"Registration failed: {await resp.text()}")
                return

        # Получение ключа собеседника
        async with session.get(f"{base_url}/user_public_key?user_id={peer_id.hex()}") as resp:
            if resp.status != 200:
                print(f"Failed to get peer key: {await resp.text()}")
                return

            try:
                pem_key = (await resp.text()).encode()
                peer_public_key = deserialize_public_key(pem_key)
            except ValueError as e:
                print(f"Invalid peer key format: {str(e)}")
                return

    print(f"Welcome to secure chat, {username}!")
    print(f"You are chatting with: {peer_name}")
    print("Type messages and press Enter. Ctrl+C to exit.\n")

    await asyncio.gather(
        receive_messages(base_url, user_id, crypto, peer_public_key),
        send_messages(base_url, user_id, crypto, peer_id, peer_public_key)
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nChat session ended")
