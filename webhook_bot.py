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
    """Запускает бота в отдельном процессе"""
    # ВСЕ ИМПОРТЫ ТОЛЬКО ВНУТРИ!
    import asyncio
    import logging
    import sys
    import os
    
    # Настраиваем логирование для дочернего процесса
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    from loader import bot, dp, setup_bot
    from scheduler import start_scheduler
    
    # Импортируем все роутеры
    from handlers.start import router as start_router
    from handlers.ai_handler import router as ai_router
    from handlers.natal import router as natal_router
    from handlers.admin import router as admin_router
    from handlers.horoscope import router as horoscope_router
    from handlers.compatibility import router as compatibility_router
    from handlers.profile import router as profile_router
    from handlers.pdf_handler import router as pdf_router
    
    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(ai_router)
    dp.include_router(natal_router)
    dp.include_router(admin_router)
    dp.include_router(horoscope_router)
    dp.include_router(compatibility_router)
    dp.include_router(profile_router)
    dp.include_router(pdf_router)
    
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
    bot_process = multiprocessing.Process(target=run_bot, daemon=False)
    bot_process.start()
    logger.info("✅ Бот запущен в отдельном процессе")
    
    # Даем боту время на инициализацию
    import time
    time.sleep(2)
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)