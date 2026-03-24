from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database.db import UserDB
from keyboards.main import welcome_keyboard, main_menu_keyboard, payment_keyboard
from utils import md2_escape

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    await UserDB.create_user(user_id, username, first_name)
    
    text = md2_escape(f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!\n\nЯ помогу вам узнать всё о вашей судьбе, звёздах и планетах.")
    
    await message.answer(text, reply_markup=welcome_keyboard(), parse_mode="MarkdownV2")

@router.callback_query(F.data == "check_status")
async def check_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_paid = await UserDB.is_paid(user_id)
    
    if is_paid:
        await callback.message.edit_text(
            md2_escape("Главное меню AstroBot v2 PRO:"),
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="MarkdownV2"
        )
    else:
        await callback.message.edit_text(
            md2_escape("Выберите тариф:"),
            reply_markup=payment_keyboard(),
            parse_mode="MarkdownV2"
        )

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        md2_escape("Главное меню:"),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data.startswith("pay_"))
async def payment_handler(callback: CallbackQuery):
    plan = callback.data.split("_")[1]
    days = {"7": 7, "30": 30, "90": 90}.get(plan, 7)
    
    await UserDB.set_subscription(callback.from_user.id, days)
    
    await callback.message.edit_text(
        md2_escape("✅ Подписка активирована!"),
        reply_markup=main_menu_keyboard(callback.from_user.id),
        parse_mode="MarkdownV2"
    )