import asyncpg
import logging
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)

class Database:
    pool = None

    @classmethod
    async def create_pool(cls):
        if cls.pool is None:
            cls.pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                min_size=1,
                max_size=10
            )
            logger.info("✅ Пул соединений с PostgreSQL создан (по параметрам).")
        return cls.pool

    @classmethod
    async def close_pool(cls):
        if cls.pool:
            await cls.pool.close()
            logger.info("Пул соединений закрыт.")

db = Database()

async def init_postgres_db():
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                birth_date TEXT,
                birth_time TEXT,
                birth_place TEXT,
                is_paid BOOLEAN DEFAULT FALSE,
                subscription_end TEXT,
                trial_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                stars_paid INTEGER NOT NULL,
                payment_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print("✅ Таблицы в PostgreSQL созданы/обновлены")

# ---- Все функции работы с БД (create_user, get_user, update_birth_data, set_subscription, is_paid, has_trial_used, set_trial_used, add_payment, get_stats) ----
# Они остаются точно такими же, как в предыдущем исправленном файле. Скопируйте их из моего предыдущего сообщения (где был asyncpg).
# Чтобы не повторять, привожу их ещё раз:
async def create_user(user_id: int, username: str = "", first_name: str = ""):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        ''', user_id, username, first_name)

async def get_user(user_id: int):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)

async def update_birth_data(user_id: int, birth_date: str, birth_time: str, birth_place: str):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE users SET birth_date = $2, birth_time = $3, birth_place = $4
            WHERE user_id = $1
        ''', user_id, birth_date, birth_time, birth_place)

async def set_subscription(user_id: int, days: int):
    from datetime import datetime, timedelta
    end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE users SET is_paid = TRUE, subscription_end = $2 WHERE user_id = $1
        ''', user_id, end_date)

async def is_paid(user_id: int) -> bool:
    from datetime import datetime
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT is_paid, subscription_end FROM users WHERE user_id = $1', user_id)
    if not row:
        return False
    if row['is_paid'] and row['subscription_end'] and datetime.now().strftime('%Y-%m-%d') <= row['subscription_end']:
        return True
    if row['is_paid'] and row['subscription_end'] and datetime.now().strftime('%Y-%m-%d') > row['subscription_end']:
        pool = await db.create_pool()
        async with pool.acquire() as conn:
            await conn.execute('UPDATE users SET is_paid = FALSE WHERE user_id = $1', user_id)
        return False
    return False

async def has_trial_used(user_id: int) -> bool:
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT trial_used FROM users WHERE user_id = $1', user_id)
        return row['trial_used'] if row else False

async def set_trial_used(user_id: int):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET trial_used = TRUE WHERE user_id = $1', user_id)

async def add_payment(user_id: int, stars_paid: int, payment_id: str):
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO payments (user_id, stars_paid, payment_id) VALUES ($1, $2, $3)
        ''', user_id, stars_paid, payment_id)

async def get_stats():
    pool = await db.create_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval('SELECT COUNT(*) FROM users')
        paid = await conn.fetchval('SELECT COUNT(*) FROM users WHERE is_paid = TRUE')
    return {'total_users': total, 'paid_users': paid, 'free_users': total - paid}