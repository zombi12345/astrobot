from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMINS
from database.db import UserDB
from datetime import datetime
import logging

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

async def show_admin_panel(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats_simple")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    await message.answer("👑 **Админ-панель**", reply_markup=keyboard, parse_mode="Markdown")

@router.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    await show_admin_panel(message)

@router.callback_query(F.data == "admin_stats_simple")
async def admin_stats_simple(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    stats = await UserDB.get_stats()
    
    text = f"""📊 **Статистика**

👥 Всего: {stats['total_users']}
💎 Премиум: {stats['paid_users']}
🆓 Бесплатных: {stats['free_users']}

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_simple")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "admin_back_simple")
async def admin_back_simple(callback: CallbackQuery):
    await show_admin_panel(callback.message)