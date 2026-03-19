from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_panel_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Статистика', callback_data='admin_stats')
    kb.button(text='Графики', callback_data='admin_charts')
    kb.button(text='Пользователи', callback_data='admin_users')
    kb.button(text='Главное меню', callback_data='main_menu')
    kb.adjust(2)
    return kb.as_markup()
