import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def setup_bot():
    logger.info('Инициализация...')
    await init_db()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f'Webhook warning: {e}')
    logger.info('Готов к работе!')

async def shutdown_bot():
    logger.info('Отключение...')
    await bot.session.close()
