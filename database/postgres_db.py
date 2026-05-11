import os
from asyncpg_lite import DatabaseManager
from config import DATABASE_URL

# Инициализация менеджера базы данных
pg_manager = DatabaseManager(dsn=DATABASE_URL, deletion_password='astrobot_secure_key')

async def init_postgres_db():
    """Создаёт необходимые таблицы в PostgreSQL"""
    async with pg_manager:
        # Пользователи
        await pg_manager.execute('''
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
        # Платежи
        await pg_manager.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                stars_paid INTEGER NOT NULL,
                payment_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Запросы (если нужны)
        await pg_manager.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print("✅ Таблицы в PostgreSQL созданы/обновлены")

async def create_user(user_id: int, username: str = "", first_name: str = ""):
    async with pg_manager:
        await pg_manager.execute('''
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        ''', user_id, username, first_name)

async def get_user(user_id: int):
    async with pg_manager:
        return await pg_manager.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)

async def update_birth_data(user_id: int, birth_date: str, birth_time: str, birth_place: str):
    async with pg_manager:
        await pg_manager.execute('''
            UPDATE users SET birth_date = $2, birth_time = $3, birth_place = $4
            WHERE user_id = $1
        ''', user_id, birth_date, birth_time, birth_place)

async def set_subscription(user_id: int, days: int):
    from datetime import datetime, timedelta
    end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    async with pg_manager:
        await pg_manager.execute('''
            UPDATE users SET is_paid = TRUE, subscription_end = $2 WHERE user_id = $1
        ''', user_id, end_date)

async def is_paid(user_id: int) -> bool:
    from datetime import datetime
    async with pg_manager:
        row = await pg_manager.fetchrow(
            'SELECT is_paid, subscription_end FROM users WHERE user_id = $1', user_id
        )
    if not row:
        return False
    if row['is_paid'] and row['subscription_end'] and datetime.now().strftime('%Y-%m-%d') <= row['subscription_end']:
        return True
    if row['is_paid'] and row['subscription_end'] and datetime.now().strftime('%Y-%m-%d') > row['subscription_end']:
        async with pg_manager:
            await pg_manager.execute('UPDATE users SET is_paid = FALSE WHERE user_id = $1', user_id)
        return False
    return False

async def has_trial_used(user_id: int) -> bool:
    async with pg_manager:
        row = await pg_manager.fetchrow('SELECT trial_used FROM users WHERE user_id = $1', user_id)
        return row['trial_used'] if row else False

async def set_trial_used(user_id: int):
    async with pg_manager:
        await pg_manager.execute('UPDATE users SET trial_used = TRUE WHERE user_id = $1', user_id)

async def add_payment(user_id: int, stars_paid: int, payment_id: str):
    async with pg_manager:
        await pg_manager.execute('''
            INSERT INTO payments (user_id, stars_paid, payment_id) VALUES ($1, $2, $3)
        ''', user_id, stars_paid, payment_id)

async def get_stats():
    async with pg_manager:
        total = await pg_manager.fetchval('SELECT COUNT(*) FROM users')
        paid = await pg_manager.fetchval('SELECT COUNT(*) FROM users WHERE is_paid = TRUE')
        return {'total_users': total, 'paid_users': paid, 'free_users': total - paid}