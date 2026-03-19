import asyncio
import logging
from datetime import datetime
from aiogram import Bot

logger = logging.getLogger(__name__)

async def send_morning_message(bot: Bot):
    """Отправка утреннего гороскопа всем админам (или позже всем пользователям)"""
    from database.db import UserDB
    from config import ADMINS

    text = "🌅 Доброе утро! Ваш гороскоп на сегодня готов!"

    # Отправляем админам
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
            logger.info(f"Утреннее сообщение отправлено админу {admin_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")

async def scheduler_worker(bot: Bot):
    """Фоновая задача, которая проверяет время и запускает нужные функции"""
    while True:
        now = datetime.now()
        # Проверяем, наступило ли 8 утра
        if now.hour == 8 and now.minute == 0:
            logger.info("Время 8:00, запускаю отправку утренних сообщений.")
            await send_morning_message(bot)
            # Ждем 61 секунду, чтобы не запустить задачу повторно в ту же минуту
            await asyncio.sleep(61)
        else:
            # Ждем 30 секунд перед следующей проверкой
            await asyncio.sleep(30)

async def start_scheduler(bot: Bot):
    """Запускает планировщик как фоновую задачу"""
    logger.info("Запуск планировщика на asyncio...")
    asyncio.create_task(scheduler_worker(bot))