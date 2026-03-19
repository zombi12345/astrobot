import os
import logging
import multiprocessing
from flask import Flask

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200

def run_bot():
    """Запускает бота в отдельном ПРОЦЕССЕ (не в потоке)"""
    import asyncio
    from loader import bot, dp, setup_bot
    from scheduler import start_scheduler
    
    logger.info("🚀 Запуск бота в отдельном процессе...")
    
    async def start_bot():
        try:
            await setup_bot()
            logger.info("✅ Бот инициализирован")
            
            asyncio.create_task(start_scheduler(bot))
            logger.info("✅ Планировщик запущен")
            
            logger.info("🔄 Запуск polling...")
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            logger.error(f"❌ Ошибка в боте: {e}")
        finally:
            await bot.session.close()
    
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Запускаем бота в отдельном процессе
    bot_process = multiprocessing.Process(target=run_bot, daemon=True)
    bot_process.start()
    logger.info("✅ Бот запущен в отдельном процессе")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)