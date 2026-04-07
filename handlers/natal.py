from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from states import NatalChartStates
from services.natal_service import natal_service
from services.pdf_generator import pdf_gen
from keyboards.main import natal_options_keyboard, main_menu_keyboard
from database.db import UserDB
from utils import md2_escape
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "natal_chart")
async def natal_chart_menu(callback: CallbackQuery):
    text = md2_escape("🔮 **Создание натальной карты**\n\n"
                      "Натальная карта — это астрологическая карта рождения, "
                      "которая показывает положение планет в момент вашего рождения.\n\n"
                      "Она помогает понять:\n"
                      "• Ваш характер и таланты\n"
                      "• Сильные и слабые стороны\n"
                      "• Кармические задачи\n"
                      "• Благоприятные сферы жизни")
    await callback.message.edit_text(text, reply_markup=natal_options_keyboard(), parse_mode="MarkdownV2")

@router.callback_query(F.data == "natal_input")
async def natal_input_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NatalChartStates.waiting_name)
    await callback.message.answer("🌟 **Введите ваше имя:**", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_name)
async def natal_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(NatalChartStates.waiting_birth_date)
    await message.answer("📅 **Введите дату рождения в формате ГГГГ-ММ-ДД**\n\n"
                         "Например: 1990-05-15", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_birth_date)
async def natal_date(message: Message, state: FSMContext):
    await state.update_data(birth_date=message.text)
    await state.set_state(NatalChartStates.waiting_birth_time)
    await message.answer("⏰ **Введите время рождения в формате ЧЧ:ММ**\n\n"
                         "Например: 14:30\n"
                         "Если время неизвестно, введите 12:00", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_birth_time)
async def natal_time(message: Message, state: FSMContext):
    await state.update_data(birth_time=message.text)
    await state.set_state(NatalChartStates.waiting_birth_place)
    await message.answer("📍 **Введите место рождения**\n\n"
                         "Например: Москва, Россия\n"
                         "или: Барановичи, Беларусь", parse_mode="Markdown")

@router.message(NatalChartStates.waiting_birth_place)
async def natal_finish(message: Message, state: FSMContext):
    await state.update_data(birth_place=message.text)
    data = await state.get_data()
    await state.clear()

    processing_msg = await message.answer("🔮 **Создаю натальную карту...**\nЭто может занять несколько секунд.", parse_mode="Markdown")

    try:
        # Создаём натальную карту
        chart_data = natal_service.create_natal_chart(
            name=data['name'],
            birth_date=data['birth_date'],
            birth_time=data['birth_time'],
            birth_place=data['birth_place']
        )
        
        # Сохраняем данные в профиль пользователя
        await UserDB.update_birth_data(
            message.from_user.id,
            data['birth_date'],
            data['birth_time'],
            data['birth_place']
        )
        
        await processing_msg.delete()
        
        # Генерируем SVG-схему натальной карты
        svg_path = natal_service.generate_svg_chart(chart_data)
        
        # Отправляем SVG-изображение
        if svg_path and os.path.exists(svg_path):
            with open(svg_path, 'rb') as f:
                await message.answer_photo(
                    f,
                    caption="🔮 **Схема натальной карты**\n\nНа схеме показано расположение планет в момент вашего рождения."
                )
            os.remove(svg_path)
        
        # Генерируем текстовый отчёт
        report_text = natal_service.generate_report_text(chart_data)
        
        # Отправляем текстовый отчёт
        await message.answer(report_text, parse_mode="Markdown")
        
        # Сохраняем данные о планетах для PDF
        await state.update_data(planets=chart_data['planets'])
        await state.update_data(houses=chart_data['houses'])
        await state.update_data(sun_sign=chart_data['sun_sign'])
        await state.update_data(ascendant=chart_data['ascendant'])
        
        # Предлагаем дальнейшие действия
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Скачать PDF-отчёт", callback_data="pdf_natal_from_chart")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(
            "✨ **Натальная карта готова!**\n\n"
            "Вы можете скачать подробный PDF-отчёт с полным анализом.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании натальной карты: {e}")
        await processing_msg.edit_text(f"❌ **Ошибка при создании натальной карты:**\n{str(e)}\n\nПожалуйста, проверьте правильность введённых данных.", parse_mode="Markdown")

# Обработчик для PDF-отчёта из натальной карты
@router.callback_query(F.data == "pdf_natal_from_chart")
async def pdf_natal_from_chart(callback: CallbackQuery, state: FSMContext):
    """Создаёт PDF-отчёт на основе уже рассчитанной натальной карты"""
    user_id = callback.from_user.id
    user_data = await UserDB.get_user(user_id)
    
    if not user_data or not user_data.get('birth_date'):
        await callback.message.edit_text(
            "❌ **Для создания PDF натальной карты нужны данные о рождении.**\n\n"
            "Пожалуйста, сначала создайте натальную карту.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    processing_msg = await callback.message.edit_text("📄 **Создаю PDF-отчёт натальной карты...**\nЭто займёт несколько секунд.", parse_mode="Markdown")
    
    try:
        # Создаём натальную карту (пересчитываем для синхронизации)
        chart_data = natal_service.create_natal_chart(
            name=user_data.get('first_name', 'Пользователь'),
            birth_date=user_data['birth_date'],
            birth_time=user_data.get('birth_time', '12:00'),
            birth_place=user_data.get('birth_place', 'Не указано')
        )
        
        # Подготавливаем данные для PDF
        pdf_data = {
            'user_name': user_data.get('first_name', 'Пользователь'),
            'birth_date': user_data['birth_date'],
            'birth_time': user_data.get('birth_time', '12:00'),
            'birth_place': user_data.get('birth_place', 'Не указано'),
            'sun_sign': chart_data['sun_sign'],
            'element': chart_data['element'],
            'quality': chart_data['quality'],
            'ascendant': chart_data['ascendant'],
            'planets': chart_data['planets'],
            'houses': chart_data['houses']
        }
        
        # Создаём PDF
        pdf_path = pdf_gen.create_natal_chart_report_pdf(pdf_data)
        
        await processing_msg.delete()
        
        # Отправляем PDF
        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(
            pdf_file,
            caption=f"🔮 **Натальная карта {user_data.get('first_name', 'Пользователь')}**\n\n"
                   f"📅 {user_data['birth_date']} в {user_data.get('birth_time', '12:00')}\n"
                   f"📍 {user_data.get('birth_place', 'Не указано')}"
        )
        
        await callback.message.answer(
            "📌 **Выберите дальнейшее действие:**",
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="Markdown"
        )
        
        # Удаляем временный файл
        os.remove(pdf_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {e}")
        await processing_msg.edit_text(f"❌ **Ошибка:** {str(e)}", reply_markup=back_to_menu_keyboard())