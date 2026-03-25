import os
import logging
import threading
from flask import Flask
from loader import bot, dp, setup_bot
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200

def run_flask():
    """Запускает Flask сервер для health check (в отдельном потоке)"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def run_bot():
    """Запускает бота в polling режиме (в основном потоке)"""
    import asyncio
    from handlers.start import router as start_router
    from handlers.ai_handler import router as ai_router
    from handlers.natal import router as natal_router
    from handlers.admin_simple import router as admin_router
    from handlers.horoscope import router as horoscope_router
    from handlers.compatibility import router as compatibility_router
    from handlers.profile import router as profile_router
    from handlers.pdf_handler import router as pdf_router

    # Подключаем все роутеры
    dp.include_router(start_router)
    dp.include_router(ai_router)
    dp.include_router(natal_router)
    dp.include_router(admin_router)
    dp.include_router(horoscope_router)
    dp.include_router(compatibility_router)
    dp.include_router(profile_router)
    dp.include_router(pdf_router)

    logger.info("Запуск polling...")

    async def start():
        await setup_bot()
        asyncio.create_task(start_scheduler(bot))
        await dp.start_polling(bot, skip_updates=True)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())

if __name__ == "__main__":
    # Запускаем Flask в фоновом потоке для health check
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask запущен в отдельном потоке")

    # Бот работает в основном потоке (polling)
    run_bot()