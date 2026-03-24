import os
import logging
from flask import Flask, request
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Импортируем все роутеры
from handlers.start import router as start_router
from handlers.ai_handler import router as ai_router
from handlers.natal import router as natal_router
from handlers.admin_simple import router as admin_router
from handlers.horoscope import router as horoscope_router
from handlers.compatibility import router as compatibility_router
from handlers.profile import router as profile_router
from handlers.pdf_handler import router as pdf_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(ai_router)
dp.include_router(natal_router)
dp.include_router(admin_router)
dp.include_router(horoscope_router)
dp.include_router(compatibility_router)
dp.include_router(profile_router)
dp.include_router(pdf_router)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Обработка веб-хуков от Telegram"""
    update = Update.model_validate(await request.json, context={'bot': bot})
    await dp.feed_update(bot, update)
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200

@app.route('/health')
def health():
    return 'OK', 200

async def setup_webhook():
    """Настройка веб-хука при запуске"""
    from loader import setup_bot
    await setup_bot()
    webhook_url = f"{os.environ.get('RENDER_EXTERNAL_URL', 'https://astrobot-spui.onrender.com')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

def run_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    # Настраиваем веб-хук
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    
    # Запускаем Flask
    run_flask()