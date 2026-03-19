from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from states import NatalChartStates
from services.pdf_generator import pdf_gen
from keyboards.main import natal_options_keyboard, main_menu_keyboard
from database.db import UserDB
from utils.validators import validator
import logging
import os

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "natal_chart")
async def natal_chart_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔮 **Создание натальной карты**\n\n"
        "Для создания натальной карты нам понадобятся ваши данные.",
        reply_markup=natal_options_keyboard()
    )

@router.callback_query(F.data == "natal_input")
async def natal_input_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NatalChartStates.waiting_name)
    await callback.message.answer(
        "📝 Введите ваше имя:"
    )

@router.message(NatalChartStates.waiting_name)
async def natal_name(message: Message, state: FSMContext):
    valid, result = validator.validate_name(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз:")
        return
    
    await state.update_data(name=result)
    await state.set_state(NatalChartStates.waiting_birth_date)
    await message.answer(
        "📅 Введите дату рождения в формате:\n"
        "`ГГГГ-ММ-ДД` (например: 1990-01-01)",
        parse_mode="Markdown"
    )

@router.message(NatalChartStates.waiting_birth_date)
async def natal_date(message: Message, state: FSMContext):
    valid, result = validator.validate_birth_date(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз:")
        return
    
    await state.update_data(birth_date=result)
    await state.set_state(NatalChartStates.waiting_birth_time)
    await message.answer(
        "⏰ Введите время рождения в формате `ЧЧ:ММ` (например: 14:30)\n"
        "или отправьте /skip, если не знаете",
        parse_mode="Markdown"
    )

@router.message(NatalChartStates.waiting_birth_time)
async def natal_time(message: Message, state: FSMContext):
    valid, result = validator.validate_birth_time(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз или отправьте /skip:")
        return
    
    await state.update_data(birth_time=result)
    await state.set_state(NatalChartStates.waiting_birth_place)
    await message.answer(
        "📍 Введите место рождения (город, страна):"
    )

@router.message(NatalChartStates.waiting_birth_place)
async def natal_finish(message: Message, state: FSMContext):
    valid, result = validator.validate_birth_place(message.text)
    
    if not valid:
        await message.answer(f"❌ {result}\nПопробуйте еще раз:")
        return
    
    data = await state.get_data()
    await state.clear()
    
    processing_msg = await message.answer("🔮 Создаю вашу натальную карту...")

    try:
        # Сохраняем данные
        await UserDB.update_birth_data(
            message.from_user.id,
            data['birth_date'],
            data.get('birth_time', '12:00'),
            result
        )
        
        # Подготавливаем данные для PDF
        pdf_data = {
            'name': data['name'],
            'birth_date': data['birth_date'],
            'birth_time': data.get('birth_time', '12:00'),
            'birth_place': result
        }
        
        # Создаем PDF
        pdf_path = pdf_gen.create_natal_chart_pdf(pdf_data)
        
        await processing_msg.delete()
        
        # Отправляем PDF
        pdf_file = FSInputFile(pdf_path)
        await message.answer_document(
            pdf_file,
            caption="🔮 **Ваша персональная натальная карта**"
        )
        
        await message.answer(
            "Выберите дальнейшее действие:",
            reply_markup=main_menu_keyboard(message.from_user.id)
        )
        
        # Удаляем временный файл
        os.remove(pdf_path)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await processing_msg.edit_text(f"❌ Ошибка при создании натальной карты: {str(e)}")