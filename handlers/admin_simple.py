from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMINS
from database.db import UserDB
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    await message.answer("👑 **Админ-панель**\n\nВыберите действие:",
                         reply_markup=keyboard,
                         parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("Нет доступа")
        return
    stats = await UserDB.get_stats()
    text = f"""📊 **Статистика**

👥 Всего: {stats['total_users']}
💎 Премиум: {stats['paid_users']}
🆓 Бесплатных: {stats['free_users']}

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text("👑 **Админ-панель**\n\nВыберите действие:",
                                     reply_markup=keyboard,
                                     parse_mode="Markdown")