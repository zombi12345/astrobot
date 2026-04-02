import asyncio
import logging
from datetime import datetime
from aiogram import Bot

logger = logging.getLogger(__name__)

async def send_morning_message(bot: Bot):
    """Отправка утреннего гороскопа"""
    from database.db import UserDB
    from config import ADMINS

    text = "🌅 Доброе утро! Ваш гороскоп на сегодня готов!"

    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
            logger.info(f"Утреннее сообщение отправлено админу {admin_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")

async def daily_backup():
    """Ежедневное создание бэкапа базы данных"""
    try:
        from backup_db import create_backup
        logger.info("🔄 Запуск ежедневного бэкапа...")
        create_backup()
    except Exception as e:
        logger.error(f"❌ Ошибка бэкапа: {e}")

async def scheduler_worker(bot: Bot):
    """Фоновая задача, которая проверяет время и запускает нужные функции"""
    last_backup_date = None
    
    while True:
        now = datetime.now()
        
        # Утренняя рассылка в 8:00
        if now.hour == 8 and now.minute == 0:
            logger.info("Время 8:00, запускаю отправку утренних сообщений.")
            await send_morning_message(bot)
            await asyncio.sleep(61)
        
        # Ежедневный бэкап в 3:00
        elif now.hour == 3 and now.minute == 0 and last_backup_date != now.date():
            await daily_backup()
            last_backup_date = now.date()
            await asyncio.sleep(61)
        
        else:
            await asyncio.sleep(30)

async def start_scheduler(bot: Bot):
    """Запускает планировщик как фоновую задачу"""
    logger.info("Запуск планировщика на asyncio...")
    asyncio.create_task(scheduler_worker(bot))