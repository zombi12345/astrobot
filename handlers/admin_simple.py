from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMINS
from database.db import UserDB
from datetime import datetime

router = Router()

async def show_admin_panel(target):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Подписки", callback_data="admin_subs")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    if isinstance(target, Message):
        await target.answer("👑 Админ-панель", reply_markup=keyboard)
    else:
        await target.message.edit_text("👑 Админ-панель", reply_markup=keyboard)

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

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    stats = await UserDB.get_stats()
    text = f"📊 Статистика\n\nВсего: {stats['total_users']}\nПремиум: {stats['paid_users']}\nБесплатных: {stats['free_users']}\n\n{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]))

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await show_admin_panel(callback)