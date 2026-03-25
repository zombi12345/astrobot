import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMINS
from database.db import UserDB
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)
router = Router()

# Состояния для FSM
class AdminStates:
    waiting_broadcast = "waiting_broadcast"
    waiting_user_id = "waiting_user_id"
    waiting_subscription_days = "waiting_subscription_days"
    waiting_search = "waiting_search"

async def show_admin_panel(target, edit=True):
    """Показывает главное меню админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Подписки", callback_data="admin_subs")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📦 Экспорт БД", callback_data="admin_export")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    text = "👑 **Админ-панель**\n\nВыберите действие:"
    
    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        if edit:
            await target.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await target.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Нет доступа")
        return
    await show_admin_panel(message)

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("Нет доступа")
        return
    await show_admin_panel(callback)

# ==================== СТАТИСТИКА ====================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    
    stats = await UserDB.get_stats()
    
    # Дополнительная статистика
    from database.db import DB_PATH
    import aiosqlite
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Всего запросов
        cur = await db.execute("SELECT COUNT(*) FROM requests")
        total_requests = (await cur.fetchone())[0]
        
        # Запросов за сегодня
        cur = await db.execute(
            "SELECT COUNT(*) FROM requests WHERE created_at > datetime('now', 'start of day')"
        )
        today_requests = (await cur.fetchone())[0]
        
        # Пользователей за последние 7 дней
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-7 days')"
        )
        new_last_week = (await cur.fetchone())[0]
    
    text = f"""📊 **СТАТИСТИКА**

👥 **Пользователи:**
• Всего: {stats['total_users']}
• Новых за 7 дней: {new_last_week}
• Платных: {stats['paid_users']}
• Бесплатных: {stats['free_users']}

📈 **Запросы:**
• Всего: {total_requests}
• За сегодня: {today_requests}

📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ==================== ПОЛЬЗОВАТЕЛИ ====================

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Список пользователей"""
    if callback.from_user.id not in ADMINS:
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
    
    text = "👥 **Последние 10 пользователей:**\n\n"
    for i, user in enumerate(users, 1):
        status = "💎" if user['is_paid'] else "🆓"
        name = user['first_name'] or user['username'] or str(user['user_id'])
        created = user['created_at'][:10] if user['created_at'] else "?"
        text += f"{i}. {status} `{user['user_id']}` - {name}\n   📅 {created}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    """Поиск пользователя по ID"""
    if callback.from_user.id not in ADMINS:
        return
    
    await callback.message.edit_text(
        "🔍 **Поиск пользователя**\n\nВведите ID пользователя:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_search)

@router.message(AdminStates.waiting_search)
async def process_user_search(message: Message, state: FSMContext):
    """Обработка поиска пользователя"""
    if message.from_user.id not in ADMINS:
        return
    
    try:
        user_id = int(message.text.strip())
        user_data = await UserDB.get_user(user_id)
        
        if not user_data:
            await message.answer("❌ Пользователь не найден")
            await state.clear()
            await show_admin_panel(message)
            return
        
        text = f"""👤 **Информация о пользователе**

🆔 ID: `{user_data['user_id']}`
📝 Имя: {user_data.get('first_name', 'Не указано')}
👤 Username: @{user_data.get('username', 'Нет')}

⭐ Статус: {'💎 Премиум' if user_data.get('is_paid') else '🆓 Бесплатный'}
📅 Подписка до: {user_data.get('subscription_end', 'Не активна')}

📅 Регистрация: {user_data.get('created_at', 'Неизвестно')[:10]}"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить подписку", callback_data=f"add_sub_{user_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")
    
    await state.clear()

# ==================== ПОДПИСКИ ====================

@router.callback_query(F.data == "admin_subs")
async def admin_subs(callback: CallbackQuery):
    """Управление подписками"""
    if callback.from_user.id not in ADMINS:
        return
    
    from database.db import DB_PATH
    import aiosqlite
    
    today = datetime.now().strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_paid = 1")
        paid_count = (await cur.fetchone())[0]
        
        cur = await db.execute(
            "SELECT user_id, first_name, username, subscription_end "
            "FROM users WHERE is_paid = 1 AND subscription_end BETWEEN ? AND ? "
            "ORDER BY subscription_end LIMIT 5",
            (today, next_week)
        )
        expiring = await cur.fetchall()
    
    text = f"💎 **Управление подписками**\n\n"
    text += f"👥 Активных подписок: {paid_count}\n\n"
    
    if expiring:
        text += "⚠️ **Истекают в ближайшие 7 дней:**\n"
        for user in expiring:
            name = user[1] or user[2] or str(user[0])
            end = user[3]
            text += f"• `{user[0]}` - {name}\n  📅 до {end}\n"
    else:
        text += "✅ Нет подписок, истекающих в ближайшие 7 дней"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать подписку", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "admin_give_sub")
async def admin_give_sub_start(callback: CallbackQuery, state: FSMContext):
    """Начало выдачи подписки"""
    if callback.from_user.id not in ADMINS:
        return
    
    await callback.message.edit_text(
        "➕ **Выдача подписки**\n\nВведите ID пользователя:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_user_id)

@router.message(AdminStates.waiting_user_id)
async def process_user_id_for_sub(message: Message, state: FSMContext):
    """Получение ID пользователя для подписки"""
    if message.from_user.id not in ADMINS:
        return
    
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
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
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
    await show_admin_panel(callback, edit=False)

@router.callback_query(F.data.startswith("add_sub_"))
async def add_sub_from_user(callback: CallbackQuery, state: FSMContext):
    """Добавление подписки из карточки пользователя"""
    if callback.from_user.id not in ADMINS:
        return
    
    user_id = int(callback.data.split("_")[2])
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.waiting_subscription_days)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней", callback_data="sub_7")],
        [InlineKeyboardButton(text="30 дней", callback_data="sub_30")],
        [InlineKeyboardButton(text="90 дней", callback_data="sub_90")],
        [InlineKeyboardButton(text="365 дней", callback_data="sub_365")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        f"👤 Пользователь: {user_id}\n\nВыберите срок подписки:",
        reply_markup=keyboard
    )

# ==================== РАССЫЛКА ====================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    if callback.from_user.id not in ADMINS:
        return
    
    await callback.message.edit_text(
        "📢 **Рассылка**\n\n"
        "Введите текст сообщения для рассылки всем пользователям.\n\n"
        "Доступно форматирование Markdown.\n\n"
        "Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_broadcast)

@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    """Отправка рассылки"""
    if message.from_user.id not in ADMINS:
        return
    
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
            await asyncio.sleep(0.05)
        except Exception as e:
            fail += 1
            logger.error(f"Ошибка отправки {user_id}: {e}")
    
    await msg.edit_text(
        f"✅ **Рассылка завершена**\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {fail}\n"
        f"📊 Всего: {success + fail}"
    )
    
    await show_admin_panel(message)

# ==================== ЭКСПОРТ БД ====================

@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    """Экспорт базы данных"""
    if callback.from_user.id not in ADMINS:
        return
    
    import os
    from database.db import DB_PATH
    
    if not os.path.exists(DB_PATH):
        await callback.message.edit_text("❌ База данных не найдена")
        return
    
    await callback.message.edit_text("📦 Подготавливаю экспорт...")
    
    with open(DB_PATH, "rb") as f:
        await callback.message.answer_document(
            f,
            caption=f"📁 **Экспорт базы данных**\n\n"
                   f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                   f"📊 Размер: {os.path.getsize(DB_PATH) / 1024:.1f} KB"
        )
    
    await callback.message.answer("✅ Экспорт выполнен")
    await show_admin_panel(callback, edit=False)

# ==================== НАЗАД ====================

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в админ-панель"""
    await show_admin_panel(callback)