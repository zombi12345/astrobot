import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в .env файле!")
    print("Создайте файл .env с содержимым: BOT_TOKEN=ваш_токен")
    exit(1)

async def force_reset():
    print("🔄 Подключаюсь к Telegram...")
    bot = Bot(token=BOT_TOKEN)
    
    # Получаем информацию о веб-хуке
    webhook_info = await bot.get_webhook_info()
    print(f"📡 Текущий веб-хук: {webhook_info.url}")
    
    # Удаляем веб-хук и сбрасываем обновления
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Веб-хук удалён, обновления сброшены")
    
    # Ждём 5 секунд, чтобы Telegram обработал запрос
    await asyncio.sleep(5)
    
    # Проверяем, что веб-хук действительно удалён
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url:
        print(f"⚠️ Веб-хук всё ещё активен: {webhook_info.url}")
    else:
        print("✅ Веб-хук успешно удалён")
    
    # Закрываем сессию
    await bot.session.close()
    print("✅ Готово! Теперь можно перезапускать бота.")

if __name__ == "__main__":
    asyncio.run(force_reset())