from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.main import back_to_menu_keyboard
import random

router = Router()

HOROSCOPES = [
    "Сегодня звёзды благоволят новым начинаниям!",
    "День благоприятен для общения и новых знакомств.",
    "Энергия дня поможет в решении старых проблем.",
    "Прислушайтесь к интуиции - она подскажет верный путь.",
    "Хороший день для творчества и самовыражения."
]

@router.callback_query(F.data == "daily_horoscope")
async def horoscope_handler(callback: CallbackQuery):
    horoscope = random.choice(HOROSCOPES)
    await callback.message.edit_text(
        f"🌟 Гороскоп на сегодня:\n\n{horoscope}",
        reply_markup=back_to_menu_keyboard()
    )