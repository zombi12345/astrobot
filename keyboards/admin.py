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
    
    # Админ-панель для админов
    if user_id in ADMINS:
        kb.button(text="👑 Админ-панель", callback_data="admin_panel")
    
    kb.adjust(2)
    return kb.as_markup()

def natal_options_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Ввести данные", callback_data="natal_input")
    kb.button(text="Назад", callback_data="main_menu")
    return kb.as_markup()

def ai_question_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Новый вопрос", callback_data="ask_ai")
    kb.button(text="Примеры вопросов", callback_data="ai_examples")
    kb.button(text="Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()

def compatibility_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Анализ совместимости", callback_data="compat_analyze")
    kb.button(text="Назад", callback_data="main_menu")
    return kb.as_markup()

def profile_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Редактировать", callback_data="profile_edit")
    kb.button(text="Главное меню", callback_data="main_menu")
    return kb.as_markup()

def pdf_type_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Натальная карта", callback_data="pdf_natal")
    kb.button(text="Личный гороскоп", callback_data="pdf_horoscope")
    kb.button(text="Назад", callback_data="main_menu")
    return kb.as_markup()

def back_to_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Главное меню", callback_data="main_menu")
    return kb.as_markup()

def confirm_keyboard(action: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f"confirm_{action}")
    kb.button(text="Нет", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()