import sqlite3
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / 'chat.db'
LIMIT = 100


class Database:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        with self._get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BLOB PRIMARY KEY,
                    public_key BLOB NOT NULL,
                    username TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id BLOB NOT NULL,
                    recipient_id BLOB NOT NULL,
                    encrypted_message BLOB NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY(sender_id) REFERENCES users(id),
                    FOREIGN KEY(recipient_id) REFERENCES users(id)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id)')

    @contextmanager
    def _get_cursor(self):
        conn = sqlite3.connect(DATABASE_PATH, timeout=10)
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA synchronous = NORMAL')
        conn.execute('PRAGMA cache_size = -10000')  # 10MB кэша
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            conn.close()

    def register_user(self, user_id, public_key, username):
        with self._get_cursor() as cursor:
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, public_key, username)
                VALUES (?, ?, ?)
            ''', (user_id, public_key, username))

    def get_user(self, user_id):
        with self._get_cursor() as cursor:
            cursor.execute('SELECT public_key, username FROM users WHERE id = ?', (user_id,))
            return cursor.fetchone()

    def add_message(self, sender_id, recipient_id, encrypted_message, timestamp):
        with self._get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO messages (sender_id, recipient_id, encrypted_message, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (sender_id, recipient_id, encrypted_message, timestamp))
            return cursor.lastrowid

    def get_messages(self, recipient_id, last_id=0):
        with self._get_cursor() as cursor:
            cursor.execute('''
                SELECT id, sender_id, encrypted_message, timestamp
                FROM messages
                WHERE recipient_id = ? AND id > ?
                ORDER BY id ASC
                LIMIT ?
            ''', (recipient_id, last_id, LIMIT))
            return cursor.fetchall()
