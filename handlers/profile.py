from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.db import UserDB
from keyboards.main import profile_keyboard, back_to_menu_keyboard
from states import ProfileEditStates
from utils.validators import validator, ValidationError
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await UserDB.get_user(user_id)
    
    if user_data:
        from astrology_calculator import AstrologyCalculator
        from datetime import datetime
        
        sign = "Не определен"
        if user_data.get('birth_date'):
            try:
                birth_date = datetime.strptime(user_data['birth_date'], '%Y-%m-%d')
                sign = AstrologyCalculator.get_zodiac_sign(birth_date)
            except:
                pass
        
        text = f"""👤 **Ваш профиль**

📝 **Основная информация:**
• Имя: {user_data.get('first_name', 'Не указано')}
• Знак зодиака: {sign}
• Дата рождения: {user_data.get('birth_date', 'Не указано')}
• Время рождения: {user_data.get('birth_time', 'Не указано')}
• Место рождения: {user_data.get('birth_place', 'Не указано')}

💎 **Статус:** {'Премиум' if user_data.get('is_paid') else 'Бесплатный'}

📌 Для обновления данных используйте кнопку "Редактировать"."""
        
        await callback.message.edit_text(text, reply_markup=profile_keyboard())
    else:
        await callback.message.edit_text("❌ Профиль не найден", reply_markup=back_to_menu_keyboard())

@router.callback_query(F.data == "profile_edit")
async def profile_edit_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_birth_date)
    await callback.message.edit_text(
        "📝 **Редактирование профиля**\n\n"
        "Введите дату рождения в формате:\n"
        "`ГГГГ-ММ-ДД` (например: 1990-01-01)\n"
        "или `ДД.ММ.ГГГГ` (например: 01.01.1990)",
        parse_mode="Markdown"
    )

@router.message(ProfileEditStates.waiting_birth_date)
async def profile_birth_date(message: Message, state: FSMContext):
    valid, result = validator.validate_birth_date(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз:")
        return
    
    await state.update_data(birth_date=result)
    await state.set_state(ProfileEditStates.waiting_birth_time)
    await message.answer(
        "⏰ Введите время рождения в формате `ЧЧ:ММ` (например: 14:30)\n"
        "или отправьте /skip, чтобы пропустить",
        parse_mode="Markdown"
    )

@router.message(ProfileEditStates.waiting_birth_time)
async def profile_birth_time(message: Message, state: FSMContext):
    valid, result = validator.validate_birth_time(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз или отправьте /skip:")
        return
    
    await state.update_data(birth_time=result)
    await state.set_state(ProfileEditStates.waiting_birth_place)
    await message.answer(
        "📍 Введите место рождения (город, страна)\n"
        "или отправьте /skip, чтобы пропустить"
    )

@router.message(ProfileEditStates.waiting_birth_place)
async def profile_finish(message: Message, state: FSMContext):
    valid, result = validator.validate_birth_place(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз или отправьте /skip:")
        return
    
    data = await state.get_data()
    await state.clear()
    
    await UserDB.update_birth_data(
        message.from_user.id,
        data.get('birth_date'),
        data.get('birth_time'),
        result
    )
    
    await message.answer(
        "✅ **Профиль успешно обновлён!**\n\n"
        "Теперь астрологические прогнозы будут более точными.",
        parse_mode="Markdown",
        reply_markup=back_to_menu_keyboard()
    )