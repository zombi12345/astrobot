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
        
        # Генерируем текстовый отчёт
        report_text = natal_service.generate_report_text(chart_data)
        
        # Отправляем текстовый отчёт
        await message.answer(report_text, parse_mode="Markdown")
        
        # Предлагаем дальнейшие действия
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Скачать PDF-отчёт", callback_data=f"pdf_natal_from_chart")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(
            "✨ **Натальная карта готова!**\n\n"
            "Вы можете скачать подробный PDF-отчёт с полным анализом.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ **Ошибка при создании натальной карты:**\n{str(e)}\n\nПожалуйста, проверьте правильность введённых данных.", parse_mode="Markdown")