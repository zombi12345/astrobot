from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import NatalChartStates
from services.natal_service import natal_service
from services.pdf_generator import pdf_gen
from keyboards.main import natal_options_keyboard, main_menu_keyboard, back_to_menu_keyboard
from database.db import UserDB
from utils import md2_escape
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

# Кэш последней созданной карты
last_chart_cache = {}

@router.callback_query(F.data == "natal_chart")
async def natal_chart_menu(callback: CallbackQuery):
    text = md2_escape("🔮 **Создание натальной карты**\n\nНатальная карта — это астрологическая карта рождения.")
    await callback.message.edit_text(text, reply_markup=natal_options_keyboard(), parse_mode="MarkdownV2")

@router.callback_query(F.data == "natal_input")
async def natal_input_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NatalChartStates.waiting_name)
    await callback.message.answer("🌟 **Введите ваше имя:**", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_name)
async def natal_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите хотя бы 2 символа.")
        return
    await state.update_data(name=name)
    await state.set_state(NatalChartStates.waiting_birth_date)
    await message.answer("📅 **Введите дату рождения (ГГГГ-ММ-ДД)**\nНапример: 1990-05-15", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_birth_date)
async def natal_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    valid, _, error = natal_service.validate_date(date_str)
    if not valid:
        await message.answer(f"❌ {error}\nПопробуйте снова в формате ГГГГ-ММ-ДД")
        return
    await state.update_data(birth_date=date_str)
    await state.set_state(NatalChartStates.waiting_birth_time)
    await message.answer("⏰ **Введите время рождения (ЧЧ:ММ)**\nЕсли неизвестно, введите 12:00", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_birth_time)
async def natal_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    valid, _, error = natal_service.validate_time(time_str)
    if not valid:
        await message.answer(f"❌ {error}\nПопробуйте снова в формате ЧЧ:ММ")
        return
    await state.update_data(birth_time=time_str)
    await state.set_state(NatalChartStates.waiting_birth_place)
    await message.answer("📍 **Введите место рождения**\nНапример: Москва, Россия", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_birth_place)
async def natal_finish(message: Message, state: FSMContext):
    place = message.text.strip()
    valid, cleaned, error = natal_service.validate_place(place)
    if not valid:
        await message.answer(f"❌ {error}\nПопробуйте снова")
        return
    
    data = await state.get_data()
    data['birth_place'] = cleaned
    await state.clear()
    
    processing_msg = await message.answer("🔮 **Создаю натальную карту...**\nЭто может занять до 30 секунд", parse_mode="Markdown")
    
    try:
        chart_data = await natal_service.create_natal_chart(
            data['name'], data['birth_date'], data['birth_time'], data['birth_place']
        )
        user_id = message.from_user.id
        last_chart_cache[user_id] = chart_data
        await UserDB.update_birth_data(user_id, data['birth_date'], data['birth_time'], data['birth_place'])
        await processing_msg.delete()
        
        # SVG карта
        svg_path = natal_service.generate_svg_chart(chart_data)
        if svg_path and os.path.exists(svg_path):
            svg_file = FSInputFile(svg_path)
            await message.answer_document(svg_file, caption="🔮 **Схема натальной карты**")
            os.remove(svg_path)
        
        # Текстовый отчёт
        report_text = natal_service.generate_report_text(chart_data)
        if len(report_text) > 4000:
            for i in range(0, len(report_text), 4000):
                await message.answer(report_text[i:i+4000], parse_mode="Markdown")
        else:
            await message.answer(report_text, parse_mode="Markdown")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Скачать PDF-отчёт", callback_data="pdf_natal_from_chart")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        await message.answer("✨ **Натальная карта готова!**", reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка создания карты: {e}")
        await processing_msg.edit_text(f"❌ **Ошибка:** {str(e)}", parse_mode="Markdown")

@router.callback_query(F.data == "pdf_natal_from_chart")
async def pdf_natal_from_chart(callback: CallbackQuery):
    user_id = callback.from_user.id
    chart_data = last_chart_cache.get(user_id)
    if not chart_data:
        user_data = await UserDB.get_user(user_id)
        if not user_data or not user_data.get('birth_date'):
            await callback.message.edit_text("❌ Нужны данные о рождении. Сначала создайте натальную карту.", reply_markup=back_to_menu_keyboard())
            return
        try:
            chart_data = await natal_service.create_natal_chart(
                user_data.get('first_name', 'Пользователь'),
                user_data['birth_date'],
                user_data.get('birth_time', '12:00'),
                user_data.get('birth_place', 'Не указано')
            )
            last_chart_cache[user_id] = chart_data
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка при создании карты: {e}", reply_markup=back_to_menu_keyboard())
            return
    
    processing_msg = await callback.message.edit_text("📄 **Создаю PDF...**", parse_mode="Markdown")
    try:
        pdf_path = pdf_gen.create_natal_chart_pdf(chart_data)
        await processing_msg.delete()
        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(pdf_file, caption=f"🔮 Натальная карта {chart_data['birth_info']['name']}")
        await callback.message.answer("📌 **Выберите действие:**", reply_markup=main_menu_keyboard(user_id))
        os.remove(pdf_path)
    except Exception as e:
        logger.error(f"Ошибка PDF: {e}")
        await processing_msg.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=back_to_menu_keyboard()