import os
import logging
import multiprocessing
from flask import Flask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200

def run_bot():
    import asyncio
    from loader import bot, dp, setup_bot
    from scheduler import start_scheduler
    
    from handlers.start import router as start_router
    from handlers.ai_handler import router as ai_router
    from handlers.natal import router as natal_router
    from handlers.admin_simple import router as admin_router
    from handlers.horoscope import router as horoscope_router
    from handlers.compatibility import router as compatibility_router
    from handlers.profile import router as profile_router
    from handlers.pdf_handler import router as pdf_router
    
    dp.include_router(start_router)
    dp.include_router(ai_router)
    dp.include_router(natal_router)
    dp.include_router(admin_router)
    dp.include_router(horoscope_router)
    dp.include_router(compatibility_router)
    dp.include_router(profile_router)
    dp.include_router(pdf_router)
    
    logger.info("Бот запускается...")
    
    async def start():
        await setup_bot()
        logger.info("Бот инициализирован")
        asyncio.create_task(start_scheduler(bot))
        logger.info("Планировщик запущен")
        await dp.start_polling(bot, skip_updates=True)
    
    asyncio.run(start())

if __name__ == "__main__":
    bot_process = multiprocessing.Process(target=run_bot)
    bot_process.start()
    logger.info("Бот запущен в отдельном процессе")
    
    import time
    time.sleep(2)
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)