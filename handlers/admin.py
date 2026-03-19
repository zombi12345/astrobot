from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import ADMINS
from keyboards.admin import admin_panel_keyboard
from database.db import UserDB
from utils.helpers import md2_escape
router = Router()

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "👑 Админ-панель",
        reply_markup=admin_panel_keyboard()
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    stats = await UserDB.get_stats()
    text = f"""📊 Статистика

👥 Всего: {stats['total_users']}
💎 Премиум: {stats['paid_users']}
🆓 Бесплатно: {stats['free_users']}"""
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())