from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.db import UserDB
from keyboards.main import profile_keyboard, back_to_menu_keyboard
from states import ProfileEditStates
from datetime import datetime

router = Router()

@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await UserDB.get_user(user_id)
    
    if not user_data:
        await callback.message.edit_text(
            "❌ Профиль не найден. Нажмите /start для регистрации.",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    # Определяем знак зодиака
    zodiac = "Не определён"
    if user_data.get('birth_date'):
        try:
            from core.ai_engine import astro_ai
            birth_date = datetime.strptime(user_data['birth_date'], '%Y-%m-%d')
            zodiac = astro_ai.get_zodiac_sign(birth_date)
        except:
            pass
    
    status = "💎 Премиум" if user_data.get('is_paid') else "🆓 Бесплатный"
    
    text = f"""👤 **Ваш профиль**

🌟 **Основная информация:**
• Имя: {user_data.get('first_name', 'Не указано')}
• Знак зодиака: {zodiac}
• Дата рождения: {user_data.get('birth_date', 'Не указано')}
• Время рождения: {user_data.get('birth_time', 'Не указано')}
• Место рождения: {user_data.get('birth_place', 'Не указано')}

⭐ **Статус:** {status}
📅 **Подписка до:** {user_data.get('subscription_end', 'Нет активной')}

📌 **Для обновления данных используйте кнопку ниже.**"""
    
    await callback.message.edit_text(
        text,
        reply_markup=profile_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "profile_edit")
async def profile_edit_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_birth_date)
    await callback.message.edit_text(
        "📝 **Редактирование профиля**\n\nВведите дату рождения (ГГГГ-ММ-ДД):",
        parse_mode="Markdown"
    )

@router.message(ProfileEditStates.waiting_birth_date)
async def profile_birth_date(message: Message, state: FSMContext):
    await state.update_data(birth_date=message.text)
    await state.set_state(ProfileEditStates.waiting_birth_time)
    await message.answer("⏰ Введите время рождения (ЧЧ:ММ) или /skip:")

@router.message(ProfileEditStates.waiting_birth_time)
async def profile_birth_time(message: Message, state: FSMContext):
    await state.update_data(birth_time=message.text if message.text != '/skip' else '12:00')
    await state.set_state(ProfileEditStates.waiting_birth_place)
    await message.answer("📍 Введите место рождения или /skip:")

@router.message(ProfileEditStates.waiting_birth_place)
async def profile_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    birth_place = message.text if message.text != '/skip' else 'Не указано'
    
    await UserDB.update_birth_data(
        message.from_user.id,
        data.get('birth_date'),
        data.get('birth_time'),
        birth_place
    )
    
    await message.answer(
        "✅ **Профиль успешно обновлён!**\n\nТеперь астрологические прогнозы будут более точными.",
        parse_mode="Markdown",
        reply_markup=back_to_menu_keyboard()
    )