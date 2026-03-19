import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH, ADMINS

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            birth_date TEXT,
            birth_time TEXT,
            birth_place TEXT,
            is_paid BOOLEAN DEFAULT FALSE,
            subscription_end TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_type TEXT,
            question TEXT,
            response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        await db.commit()

class UserDB:
    @staticmethod
    async def create_user(user_id, username, first_name):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', (user_id, username, first_name))
            await db.commit()
    
    @staticmethod
    async def get_user(user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = await cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    async def is_paid(user_id):
        if user_id in ADMINS:
            return True
        user = await UserDB.get_user(user_id)
        if not user:
            return False
        return bool(user.get('is_paid', False))
    
    @staticmethod
    async def set_subscription(user_id, days):
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE users SET is_paid = TRUE, subscription_end = ? WHERE user_id = ?', (end_date, user_id))
            await db.commit()
    
    @staticmethod
    async def update_birth_data(user_id, birth_date, birth_time=None, birth_place=None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE users SET birth_date = ?, birth_time = ?, birth_place = ? WHERE user_id = ?', (birth_date, birth_time, birth_place, user_id))
            await db.commit()
    
    # Добавляем этот метод
    @staticmethod
    async def log_request(user_id, request_type, question, response):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'INSERT INTO requests (user_id, request_type, question, response) VALUES (?, ?, ?, ?)',
                (user_id, request_type, question, response)
            )
            await db.commit()