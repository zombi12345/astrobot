import asyncio
import signal
import sys
import logging
from loader import bot, dp, setup_bot, shutdown_bot
from scheduler import start_scheduler

from handlers.start import router as start_router
from handlers.ai_handler import router as ai_router
from handlers.natal import router as natal_router
from handlers.admin import router as admin_router
from handlers.horoscope import router as horoscope_router
from handlers.compatibility import router as compatibility_router
from handlers.profile import router as profile_router
from handlers.pdf_handler import router as pdf_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp.include_router(start_router)
dp.include_router(ai_router)
dp.include_router(natal_router)
dp.include_router(admin_router)
dp.include_router(horoscope_router)
dp.include_router(compatibility_router)
dp.include_router(profile_router)
dp.include_router(pdf_router)

async def main():
    logger.info('=' * 40)
    logger.info('ЗАПУСК ASTROBOT')
    logger.info('=' * 40)
    try:
        await setup_bot()
        logger.info('Запуск планировщика...')
        asyncio.create_task(start_scheduler(bot))
        logger.info('AstroBot готов к работе!')
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info('Остановка по Ctrl+C')
    except Exception as e:
        logger.error(f'Критическая ошибка: {e}')
    finally:
        await shutdown_bot()

if __name__ == '__main__':
    asyncio.run(main())
