import aiosqlite
from config import DB_PATH
import logging

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей (уже должна быть)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                birth_date TEXT,
                birth_time TEXT,
                birth_place TEXT,
                is_paid BOOLEAN DEFAULT 0,
                subscription_end TEXT,
                trial_used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Таблица платежей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stars_paid INTEGER NOT NULL,
                payment_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def create_user(user_id: int, username: str = "", first_name: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
            (user_id, username, first_name)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return await cur.fetchone()

async def update_birth_data(user_id: int, birth_date: str, birth_time: str, birth_place: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET birth_date = ?, birth_time = ?, birth_place = ? WHERE user_id = ?',
            (birth_date, birth_time, birth_place, user_id)
        )
        await db.commit()

async def set_subscription(user_id: int, days: int):
    """Активирует подписку на days дней (с текущего момента)"""
    from datetime import datetime, timedelta
    end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET is_paid = 1, subscription_end = ? WHERE user_id = ?',
            (end_date, user_id)
        )
        await db.commit()

async def is_paid(user_id: int) -> bool:
    """Проверяет, активна ли подписка (с учётом срока)"""
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('SELECT is_paid, subscription_end FROM users WHERE user_id = ?', (user_id,))
        row = await cur.fetchone()
        if not row:
            return False
        if row[0] and row[1] and datetime.now().strftime('%Y-%m-%d') <= row[1]:
            return True
        # Если истекла – отключаем флаг
        if row[0] and row[1] and datetime.now().strftime('%Y-%m-%d') > row[1]:
            await db.execute('UPDATE users SET is_paid = 0 WHERE user_id = ?', (user_id,))
            await db.commit()
        return False

async def has_trial_used(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('SELECT trial_used FROM users WHERE user_id = ?', (user_id,))
        row = await cur.fetchone()
        return row[0] if row else False

async def set_trial_used(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET trial_used = 1 WHERE user_id = ?', (user_id,))
        await db.commit()

async def add_payment(user_id: int, stars_paid: int, payment_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO payments (user_id, stars_paid, payment_id) VALUES (?, ?, ?)',
            (user_id, stars_paid, payment_id)
        )
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('SELECT COUNT(*) FROM users')
        total = (await cur.fetchone())[0]
        cur = await db.execute('SELECT COUNT(*) FROM users WHERE is_paid = 1')
        paid = (await cur.fetchone())[0]
        return {'total_users': total, 'paid_users': paid, 'free_users': total - paid}