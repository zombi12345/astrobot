#!/bin/bash
# Скрипт для запуска бота на Render с предварительной инициализацией PostgreSQL

# Выводим сообщение о начале процесса
echo "🚀 Запуск AstroBot на Render..."

# Убеждаемся, что переменная DATABASE_URL установлена (проверка)
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Ошибка: переменная окружения DATABASE_URL не установлена!"
    exit 1
fi

# Инициализируем таблицы в PostgreSQL (выполняем Python-скрипт)
echo "📦 Создание таблиц в Supabase (PostgreSQL)..."
python -c "
import asyncio
from database.postgres_db import init_postgres_db

async def main():
    await init_postgres_db()
    print('✅ Таблицы успешно созданы/обновлены')

asyncio.run(main())
"

# Проверяем код возврата последней команды
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при создании таблиц. Запуск бота отменён."
    exit 1
fi

# Запускаем основного бота
echo "🤖 Запуск webhook_bot.py..."
exec python webhook_bot.py