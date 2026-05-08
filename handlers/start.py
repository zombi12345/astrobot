from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database.db import create_user, is_paid, has_trial_used, set_trial_used, set_subscription
from keyboards.main import welcome_keyboard, main_menu_keyboard, payment_keyboard
from utils import md2_escape
from datetime import datetime, timedelta

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    await create_user(user_id, username, first_name)
    
    # Активация пробного периода (1 день), если ещё не использован и нет активной подписки
    trial_used = await has_trial_used(user_id)
    paid = await is_paid(user_id)
    if not trial_used and not paid:
        await set_subscription(user_id, 1)          # 1 день пробного периода
        await set_trial_used(user_id)
        await message.answer(
            "🎁 **Вам активирован пробный период на 1 день!**\n"
            "Вы можете пользоваться всеми функциями бота бесплатно.\n\n"
            "После окончания пробного периода потребуется оплатить подписку.",
            parse_mode="Markdown"
        )
    
    text = md2_escape(f"🌟 Добро пожаловать в AstroBot v2 PRO, {first_name}!\n\n"
                      "Я помогу вам узнать всё о вашей судьбе, звёздах и планетах.")
    await message.answer(text, reply_markup=welcome_keyboard(), parse_mode="MarkdownV2")

@router.callback_query(F.data == "check_status")
async def check_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_paid_user = await is_paid(user_id)
    
    if is_paid_user:
        await callback.message.edit_text(
            md2_escape("Главное меню AstroBot v2 PRO:"),
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="MarkdownV2"
        )
    else:
        await callback.message.edit_text(
            md2_escape("🔒 Ваш пробный период закончился.\n\nВыберите тариф для продления подписки:"),
            reply_markup=payment_keyboard(),
            parse_mode="MarkdownV2"
        )

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not await is_paid(user_id):
        await callback.message.edit_text(
            md2_escape("❌ Доступ запрещён. Ваша подписка неактивна. Пополните подписку."),
            reply_markup=payment_keyboard(),
            parse_mode="MarkdownV2"
        )
        return
    await callback.message.edit_text(
        md2_escape("Главное меню:"),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="MarkdownV2"
    )