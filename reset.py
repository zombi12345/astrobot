import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в .env файле!")
    exit(1)

async def reset():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook удалён")
    await bot.session.close()

asyncio.run(reset())