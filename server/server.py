import sys
import os
import asyncio
from aiohttp import web
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from auth import generate_key_pair
from shared.crypto_utils import serialize_public_key, deserialize_public_key

routes = web.RouteTableDef()
db = Database()
server_private_key, server_public_key = generate_key_pair()


@routes.post('/register')
async def register(request):
    data = await request.json()
    user_id = bytes.fromhex(data['user_id'])
    public_key = data['public_key'].encode()  # Преобразуем строку в байты
    username = data['username']

    db.register_user(user_id, public_key, username)
    return web.Response(text='OK')


@routes.get('/user_check')
async def user_check(request):
    user_id = bytes.fromhex(request.query['user_id'])
    user = db.get_user(user_id)
    if not user:
        return web.Response(status=404, text='User not found')
    return web.Response(text='User registered')


@routes.post('/message')
async def post_message(request):
    data = await request.json()
    sender_id = bytes.fromhex(data['sender_id'])
    recipient_id = bytes.fromhex(data['recipient_id'])

    # Проверка существования пользователей
    if not db.get_user(sender_id):
        return web.Response(text='Sender not found', status=404)
    if not db.get_user(recipient_id):
        return web.Response(text='Recipient not found', status=404)

    encrypted_message = bytes.fromhex(data['encrypted_message'])

    timestamp = asyncio.get_event_loop().time()
    db.add_message(sender_id, recipient_id, encrypted_message, timestamp)
    return web.Response(text='OK')


@routes.get('/messages')
async def get_messages(request):
    recipient_id = bytes.fromhex(request.query['user_id'])
    last_id = int(request.query.get('last_id', 0))

    messages = db.get_messages(recipient_id, last_id)
    formatted = [
        {
            'id': row[0],
            'sender_id': row[1].hex(),
            'encrypted_message': row[2].hex(),
            'timestamp': row[3]
        }
        for row in messages
    ]
    return web.json_response(formatted)


@routes.get('/public_key')
async def get_public_key(request):
    pem_key = server_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return web.Response(text=pem_key.decode('utf-8'))


@routes.get('/user_public_key')
async def get_user_public_key(request):
    user_id = bytes.fromhex(request.query['user_id'])
    user = db.get_user(user_id)
    if not user:
        return web.Response(status=404, text='User not found')

    # public_key уже в PEM формате
    public_key_bytes = user[0]

    try:
        # Десериализуем ключ
        public_key = deserialize_public_key(public_key_bytes)

        # Конвертируем в PEM для отправки
        pem_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return web.Response(text=pem_key.decode('utf-8'))
    except Exception as e:
        return web.Response(status=500, text=f"Key processing error: {str(e)}")


@routes.get('/user_info')
async def get_user_info(request):
    user_id = bytes.fromhex(request.query['user_id'])
    user = db.get_user(user_id)
    if not user:
        return web.Response(status=404, text='User not found')

    # user[0] - public_key, user[1] - username
    return web.json_response({
        'user_id': user_id.hex(),
        'username': user[1]
    })


app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app, port=8080, access_log=None)
