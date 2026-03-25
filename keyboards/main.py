from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMINS

def welcome_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Продолжить", callback_data="check_status")
    return kb.as_markup()

def payment_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="7 дней - 299 руб", callback_data="pay_7")
    kb.button(text="30 дней - 999 руб", callback_data="pay_30")
    kb.button(text="90 дней - 2499 руб", callback_data="pay_90")
    kb.adjust(1)
    return kb.as_markup()

def main_menu_keyboard(user_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔮 Натальная карта", callback_data="natal_chart")
    kb.button(text="✨ Личный вопрос", callback_data="ai_question")
    kb.button(text="🌙 Гороскоп дня", callback_data="daily_horoscope")
    kb.button(text="💕 Совместимость", callback_data="compatibility")
    kb.button(text="👤 Профиль", callback_data="profile")
    kb.button(text="📄 PDF отчёт", callback_data="generate_pdf")

    if user_id in ADMINS:
        kb.button(text="👑 Админ-панель", callback_data="admin_panel")

    kb.adjust(2)
    return kb.as_markup()

def back_to_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Главное меню", callback_data="main_menu")
    return kb.as_markup()