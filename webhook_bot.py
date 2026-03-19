import os
import logging
import threading
import asyncio
from flask import Flask
from loader import bot, dp, setup_bot
from scheduler import start_scheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)

@app.route('/health')
def health():
    """Health check для Render"""
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200

def run_bot():
    """Запускает бота в отдельном потоке с собственным event loop"""
    logger.info("Запуск бота в фоновом потоке...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def start_bot():
        await setup_bot()
        logger.info("Бот инициализирован")
        asyncio.create_task(start_scheduler(bot))
        logger.info("Планировщик запущен")
        await dp.start_polling(bot, skip_updates=True)
    
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Бот запущен в фоновом потоке")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Запуск Flask сервера на порту {port}")
    
    # Важно: debug=False, threaded=True для production
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)