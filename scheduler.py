import aioschedule
import asyncio
from aiogram import Bot

async def send_morning_message(bot: Bot):
    from config import ADMINS
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, 'Доброе утро!')
        except:
            pass

async def start_scheduler(bot: Bot):
    aioschedule.every().day.at('08:00').do(lambda: asyncio.create_task(send_morning_message(bot)))
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)
