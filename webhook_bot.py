import os
import logging
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import BOT_TOKEN
from loader import setup_bot  # <--- ДОБАВЬТЕ ЭТОТ ИМПОРТ

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Импорт всех роутеров
from handlers.start import router as start_router
from handlers.ai_handler import router as ai_router
from handlers.natal import router as natal_router
from handlers.admin_simple import router as admin_router
from handlers.horoscope import router as horoscope_router
from handlers.compatibility import router as compatibility_router
from handlers.profile import router as profile_router
from handlers.pdf_handler import router as pdf_router
from handlers.compatibility import router as compatibility_router
from handlers.payment import router as payment_router

# Подключение всех роутеров
dp.include_router(start_router)
dp.include_router(ai_router)
dp.include_router(natal_router)
dp.include_router(admin_router)
dp.include_router(horoscope_router)
dp.include_router(compatibility_router)
dp.include_router(profile_router)
dp.include_router(pdf_router)
dp.include_router(compatibility_router)
dp.include_router(payment_router)

# Глобальный цикл событий
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик веб-хука"""
    try:
        data = request.get_json()
        update = Update.model_validate(data, context={'bot': bot})
        
        future = asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        future.result(timeout=10)
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка в веб-хуке: {e}")
        return 'Error', 500

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200

async def setup_webhook():
    # ИНИЦИАЛИЗИРУЕМ БАЗУ ДАННЫХ
    await setup_bot()  # <--- ЭТО ВАЖНО!
    
    webhook_url = f"{os.environ.get('RENDER_EXTERNAL_URL', 'https://astrobot-spui.onrender.com')}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

def run_loop():
    """Запускает цикл событий в отдельном потоке"""
    loop.run_forever()

if __name__ == "__main__":
    # Настраиваем веб-хук и инициализируем базу
    loop.run_until_complete(setup_webhook())
    
    # Запускаем цикл событий в фоне
    import threading
    threading.Thread(target=run_loop, daemon=True).start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)