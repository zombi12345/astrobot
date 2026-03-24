from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMINS
from database.db import UserDB
from services.statistics import stats_gen
import logging
import os
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_user_id = State()
    waiting_subscription_days = State()

# Проверка прав администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ==================== ГЛАВНОЕ МЕНЮ ====================

async def show_admin_panel(message: Message):
    """Показывает главное меню админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Подписки", callback_data="admin_subs")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ])
    
    await message.answer(
        "👑 **Админ-панель**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.message(Command("admin"))
async def admin_command(message: Message):
    """Открывает админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await show_admin_panel(message)

# ==================== СТАТИСТИКА ====================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показывает статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text("📊 Собираю статистику...")
    
    try:
        stats = await UserDB.get_stats()
        
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

📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        await callback.message.edit_text("❌ Ошибка при получении статистики")

# ==================== ПОЛЬЗОВАТЕЛИ ====================

@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery):
    """Меню управления пользователями"""
    if not is_admin(callback.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="admin_search_id")],
        [InlineKeyboardButton(text="📋 Последние 10", callback_data="admin_list_recent")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
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
    
    await state.set_state(AdminStates.waiting_user_id)
    await callback.message.edit_text(
        "🔍 **Поиск пользователя**\n\nВведите ID пользователя:",
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_user_id)
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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ==================== ПОДПИСКИ ====================

@router.callback_query(F.data == "admin_subs")
async def admin_subs_menu(callback: CallbackQuery):
    """Меню управления подписками"""
    if not is_admin(callback.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="admin_add_sub")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
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

@router.callback_query(F.data.startswith("add_sub_"))
async def admin_add_sub_from_user(callback: CallbackQuery, state: FSMContext):
    """Добавление подписки из карточки пользователя"""
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split("_")[2])
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.waiting_subscription_days)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней", callback_data="sub_7")],
        [InlineKeyboardButton(text="30 дней", callback_data="sub_30")],
        [InlineKeyboardButton(text="90 дней", callback_data="sub_90")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        f"👤 Пользователь: {user_id}\n\nВыберите срок подписки:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("sub_"))
async def process_subscription_days(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора срока подписки"""
    days_map = {"sub_7": 7, "sub_30": 30, "sub_90": 90}
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
    import asyncio
    
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1
    
    await msg.edit_text(
        f"✅ **Рассылка завершена**\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {fail}\n"
        f"📊 Всего: {success + fail}"
    )
    
    await show_admin_panel(message)

# ==================== НАЗАД ====================

@router.callback_query(F.data == "admin_back")
async def back_to_admin_panel(callback: CallbackQuery):
    """Возврат в админ-панель"""
    await show_admin_panel(callback.message)