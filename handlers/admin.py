import asyncio
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMINS
from database.db import UserDB
from services.statistics import stats_gen
from services.pdf_generator import pdf_gen
import logging
import os
import io
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_user_id = State()
    waiting_subscription_days = State()
    waiting_promo_days = State()
    waiting_search = State()
    waiting_pin_message = State()

# Проверка прав администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ==================== КОМАНДЫ ====================

@router.message(Command("admin"))
async def admin_command(message: Message):
    """Открывает админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await show_admin_panel(message)

async def show_admin_panel(message: Message):
    """Показывает главное меню админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📈 Графики", callback_data="admin_charts")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Управление подписками", callback_data="admin_subs")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📝 Список команд", callback_data="admin_commands")],
        [InlineKeyboardButton(text="🔄 Экспорт базы данных", callback_data="admin_export")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ])
    
    await message.answer(
        "👑 **Админ-панель**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ==================== СТАТИСТИКА ====================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показывает статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    stats = await UserDB.get_stats()
    
    # Дополнительная статистика
    from database.db import DB_PATH
    import aiosqlite
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Пользователи за последние 7 дней
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-7 days')"
        )
        new_last_week = (await cur.fetchone())[0]
        
        # Всего запросов
        cur = await db.execute("SELECT COUNT(*) FROM requests")
        total_requests = (await cur.fetchone())[0]
        
        # Запросов за сегодня
        cur = await db.execute(
            "SELECT COUNT(*) FROM requests WHERE created_at > datetime('now', 'start of day')"
        )
        today_requests = (await cur.fetchone())[0]
    
    text = f"""📊 **СТАТИСТИКА**

👥 **Пользователи:**
• Всего: {stats['total_users']}
• Новых за 7 дней: {new_last_week}
• Платных: {stats['paid_users']}
• Бесплатных: {stats['free_users']}

📈 **Запросы:**
• Всего: {total_requests}
• За сегодня: {today_requests}

💎 **Подписки:**
• Активных: {stats['paid_users']}
• Истекают сегодня: {await get_expiring_today()}

📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")

async def get_expiring_today():
    """Возвращает количество подписок, истекающих сегодня"""
    from database.db import DB_PATH
    import aiosqlite
    
    today = datetime.now().strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE subscription_end = ?",
            (today,)
        )
        return (await cur.fetchone())[0]

# ==================== ГРАФИКИ ====================

@router.callback_query(F.data == "admin_charts")
async def admin_charts_menu(callback: CallbackQuery):
    """Меню графиков"""
    if not is_admin(callback.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Регистрации", callback_data="chart_users")],
        [InlineKeyboardButton(text="🎯 Активность", callback_data="chart_activity")],
        [InlineKeyboardButton(text="💎 Подписки", callback_data="chart_subscriptions")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(
        "📊 **Выберите график:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "chart_users")
async def chart_users(callback: CallbackQuery):
    """График регистраций"""
    if not is_admin(callback.from_user.id):
        return
    
    msg = await callback.message.edit_text("📊 Генерирую график...")
    
    chart_path = await stats_gen.generate_users_chart()
    
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as photo:
            await callback.message.answer_photo(
                photo,
                caption="📈 **График регистраций пользователей**"
            )
        os.remove(chart_path)
    
    await msg.delete()
    await show_admin_panel(callback.message)

@router.callback_query(F.data == "chart_activity")
async def chart_activity(callback: CallbackQuery):
    """График активности"""
    if not is_admin(callback.from_user.id):
        return
    
    msg = await callback.message.edit_text("📊 Генерирую график активности...")
    
    chart_path = await stats_gen.generate_activity_chart()
    
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as photo:
            await callback.message.answer_photo(
                photo,
                caption="🎯 **График активности пользователей**"
            )
        os.remove(chart_path)
    
    await msg.delete()
    await show_admin_panel(callback.message)

@router.callback_query(F.data == "chart_subscriptions")
async def chart_subscriptions(callback: CallbackQuery):
    """График подписок"""
    if not is_admin(callback.from_user.id):
        return
    
    msg = await callback.message.edit_text("📊 Генерирую график подписок...")
    
    chart_path = await stats_gen.generate_subscription_chart()
    
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as photo:
            await callback.message.answer_photo(
                photo,
                caption="💎 **График подписок**"
            )
        os.remove(chart_path)
    
    await msg.delete()
    await show_admin_panel(callback.message)

# ==================== ПОЛЬЗОВАТЕЛИ ====================

@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery):
    """Меню управления пользователями"""
    if not is_admin(callback.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="admin_search_id")],
        [InlineKeyboardButton(text="📋 Список последних", callback_data="admin_list_recent")],
        [InlineKeyboardButton(text="💰 Премиум пользователи", callback_data="admin_list_premium")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(
        "👥 **Управление пользователями**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_search_id")
async def admin_search_id(callback: CallbackQuery, state: FSMContext):
    """Поиск пользователя по ID"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_search)
    await callback.message.edit_text(
        "🔍 **Поиск пользователя**\n\nВведите ID пользователя:",
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_search)
async def process_user_search(message: Message, state: FSMContext):
    """Обработка поиска пользователя"""
    await state.clear()
    
    try:
        user_id = int(message.text.strip())
        user_data = await UserDB.get_user(user_id)
        
        if not user_data:
            await message.answer("❌ Пользователь не найден")
            await show_admin_panel(message)
            return
        
        await show_user_info(message, user_data)
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")
        await show_admin_panel(message)

@router.callback_query(F.data == "admin_list_recent")
async def admin_list_recent(callback: CallbackQuery):
    """Список последних пользователей"""
    if not is_admin(callback.from_user.id):
        return
    
    from database.db import DB_PATH
    import aiosqlite
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT user_id, first_name, username, created_at, is_paid "
            "FROM users ORDER BY created_at DESC LIMIT 10"
        )
        users = await cur.fetchall()
    
    if not users:
        await callback.message.edit_text("Нет пользователей")
        return
    
    text = "📋 **Последние 10 пользователей:**\n\n"
    for i, user in enumerate(users, 1):
        status = "💎" if user['is_paid'] else "🆓"
        name = user['first_name'] or user['username'] or str(user['user_id'])
        created = user['created_at'][:10] if user['created_at'] else "?"
        text += f"{i}. {status} `{user['user_id']}` - {name}\n   📅 {created}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "admin_list_premium")
async def admin_list_premium(callback: CallbackQuery):
    """Список премиум пользователей"""
    if not is_admin(callback.from_user.id):
        return
    
    from database.db import DB_PATH
    import aiosqlite
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT user_id, first_name, username, subscription_end "
            "FROM users WHERE is_paid = 1 ORDER BY subscription_end DESC LIMIT 20"
        )
        users = await cur.fetchall()
    
    if not users:
        await callback.message.edit_text("💎 Премиум пользователей нет")
        return
    
    text = "💎 **Премиум пользователи:**\n\n"
    for i, user in enumerate(users, 1):
        name = user['first_name'] or user['username'] or str(user['user_id'])
        end = user['subscription_end'] or "бессрочно"
        text += f"{i}. `{user['user_id']}` - {name}\n   📅 До: {end}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_user_info(message: Message, user_data: dict):
    """Показывает информацию о пользователе"""
    from datetime import datetime
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Добавить подписку", callback_data=f"add_sub_{user_data['user_id']}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ])
    
    status = "💎 Премиум" if user_data.get('is_paid') else "🆓 Бесплатный"
    end = user_data.get('subscription_end', 'Не активна')
    
    text = f"""👤 **Информация о пользователе**

🆔 ID: `{user_data['user_id']}`
📝 Имя: {user_data.get('first_name', 'Не указано')}
👤 Username: @{user_data.get('username', 'Нет')}

⭐ Статус: {status}
📅 Подписка до: {end}

📅 Регистрация: {user_data.get('created_at', 'Неизвестно')[:10]}

🎂 Дата рождения: {user_data.get('birth_date', 'Не указана')}
⏰ Время рождения: {user_data.get('birth_time', 'Не указано')}
📍 Место рождения: {user_data.get('birth_place', 'Не указано')}"""
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# ==================== УПРАВЛЕНИЕ ПОДПИСКАМИ ====================

@router.callback_query(F.data == "admin_subs")
async def admin_subs_menu(callback: CallbackQuery):
    """Меню управления подписками"""
    if not is_admin(callback.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="admin_add_sub")],
        [InlineKeyboardButton(text="📋 Список истекающих", callback_data="admin_expiring")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(
        "💎 **Управление подписками**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_add_sub")
async def admin_add_sub_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления подписки"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_user_id)
    await callback.message.edit_text(
        "➕ **Добавление подписки**\n\nВведите ID пользователя:",
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_user_id)
async def process_user_id(message: Message, state: FSMContext):
    """Получение ID пользователя"""
    try:
        user_id = int(message.text.strip())
        user_data = await UserDB.get_user(user_id)
        
        if not user_data:
            await message.answer("❌ Пользователь не найден")
            await state.clear()
            await show_admin_panel(message)
            return
        
        await state.update_data(user_id=user_id)
        await state.set_state(AdminStates.waiting_subscription_days)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="7 дней", callback_data="sub_7")],
            [InlineKeyboardButton(text="30 дней", callback_data="sub_30")],
            [InlineKeyboardButton(text="90 дней", callback_data="sub_90")],
            [InlineKeyboardButton(text="365 дней", callback_data="sub_365")],
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_subs")]
        ])
        
        await message.answer(
            f"👤 Пользователь: {user_data.get('first_name', user_id)}\n\n"
            "Выберите срок подписки:",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")

@router.callback_query(F.data.startswith("sub_"))
async def process_subscription_days(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора срока подписки"""
    days_map = {"sub_7": 7, "sub_30": 30, "sub_90": 90, "sub_365": 365}
    days = days_map.get(callback.data, 7)
    
    data = await state.get_data()
    user_id = data.get('user_id')
    
    if user_id:
        await UserDB.set_subscription(user_id, days)
        
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        await callback.message.edit_text(
            f"✅ Подписка активирована!\n\n"
            f"👤 Пользователь: {user_id}\n"
            f"📅 Дней: {days}\n"
            f"🗓️ Действует до: {end_date}"
        )
        
        # Уведомляем пользователя
        from loader import bot
        try:
            await bot.send_message(
                user_id,
                f"🎉 **Подписка активирована!**\n\n"
                f"Доступна на {days} дней\n"
                f"Действует до: {end_date}\n\n"
                f"Спасибо за использование AstroBot! 🌟",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await state.clear()
    await show_admin_panel(callback.message)

@router.callback_query(F.data == "admin_expiring")
async def admin_expiring(callback: CallbackQuery):
    """Список истекающих подписок"""
    if not is_admin(callback.from_user.id):
        return
    
    from database.db import DB_PATH
    import aiosqlite
    
    today = datetime.now().strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT user_id, first_name, username, subscription_end "
            "FROM users WHERE is_paid = 1 AND subscription_end BETWEEN ? AND ? "
            "ORDER BY subscription_end",
            (today, next_week)
        )
        users = await cur.fetchall()
    
    if not users:
        await callback.message.edit_text(
            "📅 Нет подписок, истекающих в ближайшие 7 дней"
        )
        return
    
    text = "⚠️ **Подписки, истекающие в ближайшие 7 дней:**\n\n"
    for user in users:
        name = user['first_name'] or user['username'] or str(user['user_id'])
        end = user['subscription_end']
        text += f"• `{user['user_id']}` - {name}\n  📅 до {end}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_subs")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ==================== РАССЫЛКА ====================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📢 **Рассылка**\n\n"
        "Введите текст сообщения для рассылки всем пользователям.\n\n"
        "Доступно форматирование Markdown.\n\n"
        "Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    """Отправка рассылки"""
    text = message.text
    
    if text == "/cancel":
        await state.clear()
        await show_admin_panel(message)
        return
    
    await state.clear()
    
    # Получаем всех пользователей
    from database.db import DB_PATH
    import aiosqlite
    
    msg = await message.answer("📢 Начинаю рассылку...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users")
        users = await cur.fetchall()
    
    success = 0
    fail = 0
    
    from loader import bot
    
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)  # Защита от ограничений Telegram
        except:
            fail += 1
    
    await msg.edit_text(
        f"✅ **Рассылка завершена**\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {fail}\n"
        f"📊 Всего: {success + fail}"
    )
    
    await show_admin_panel(message)

# ==================== ЭКСПОРТ БАЗЫ ДАННЫХ ====================

@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    """Экспорт базы данных"""
    if not is_admin(callback.from_user.id):
        return
    
    from database.db import DB_PATH
    
    if not os.path.exists(DB_PATH):
        await callback.message.edit_text("❌ База данных не найдена")
        return
    
    msg = await callback.message.edit_text("📦 Подготавливаю экспорт...")
    
    # Создаем бэкап перед экспортом
    from backup_db import create_backup
    create_backup()
    
    # Отправляем файл
    with open(DB_PATH, "rb") as f:
        await callback.message.answer_document(
            f,
            caption=f"📁 **Экспорт базы данных**\n\n"
                   f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                   f"📊 Размер: {os.path.getsize(DB_PATH) / 1024:.1f} KB"
        )
    
    await msg.delete()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    
    await callback.message.answer(
        "✅ Экспорт выполнен",
        reply_markup=keyboard
    )

# ==================== СПИСОК КОМАНД ====================

@router.callback_query(F.data == "admin_commands")
async def admin_commands_list(callback: CallbackQuery):
    """Список доступных команд"""
    if not is_admin(callback.from_user.id):
        return
    
    text = """📝 **Доступные команды для администратора:**

🔹 **/admin** - открыть админ-панель
🔹 **/stats** - быстрая статистика
🔹 **/broadcast** - рассылка (быстрый доступ)

👑 **Через админ-панель:**

• 📊 Статистика — полная статистика
• 📈 Графики — визуализация данных
• 👥 Пользователи — поиск и управление
• 💎 Подписки — выдача и просмотр
• 📢 Рассылка — массовая отправка
• 🔄 Экспорт — выгрузка базы данных

💡 **Совет:** Используйте /admin для быстрого доступа к панели"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

@router.callback_query(F.data == "admin_panel")
async def back_to_admin_panel(callback: CallbackQuery):
    """Возврат в админ-панель"""
    await show_admin_panel(callback.message)

@router.message(Command("stats"))
async def quick_stats(message: Message):
    """Быстрая статистика"""
    if not is_admin(message.from_user.id):
        return
    
    stats = await UserDB.get_stats()
    await message.answer(
        f"📊 **Быстрая статистика**\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"💎 Премиум: {stats['paid_users']}\n"
        f"🆓 Бесплатных: {stats['free_users']}",
        parse_mode="Markdown"
    )

@router.message(Command("broadcast"))
async def quick_broadcast(message: Message, state: FSMContext):
    """Быстрая рассылка"""
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_broadcast)
    await message.answer(
        "📢 Введите текст для рассылки.\n\n"
        "Для отмены отправьте /cancel"
    )