from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from services.pdf_generator import pdf_gen
from keyboards.main import pdf_type_keyboard, back_to_menu_keyboard, main_menu_keyboard
from database.db import UserDB
from ai_service_n1n import ai_service
import logging
import os
import traceback
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "generate_pdf") 
async def pdf_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📄 **Генерация PDF отчётов**\n\n"
        "Выберите тип отчёта:\n"
        "🔮 Натальная карта\n"
        "🌙 Личный гороскоп",
        reply_markup=pdf_type_keyboard()
    )

@router.callback_query(F.data == "pdf_natal")
async def pdf_natal(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await UserDB.get_user(user_id)
    
    if not user_data or not user_data.get('birth_date'):
        await callback.message.edit_text(
            "❌ Для создания PDF натальной карты нужны данные о рождении.",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    msg = await callback.message.edit_text("📄 Создаю PDF натальной карты...")
    
    try:
        # Подготавливаем данные
        data = {
            'name': user_data.get('first_name', 'Пользователь'),
            'birth_date': user_data.get('birth_date', ''),
            'birth_time': user_data.get('birth_time', '12:00'),
            'birth_place': user_data.get('birth_place', 'Не указано')
        }
        
        # Создаем PDF
        pdf_path = pdf_gen.create_natal_chart_pdf(data)
        
        await msg.delete()
        
        # Отправляем PDF
        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(
            pdf_file,
            caption="🔮 Ваша натальная карта"
        )
        
        # Возвращаем в главное меню
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(user_id)
        )
        
        # Удаляем временный файл
        os.remove(pdf_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {e}\n{traceback.format_exc()}")
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

@router.callback_query(F.data == "pdf_horoscope")
async def pdf_horoscope(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await UserDB.get_user(user_id)
    
    msg = await callback.message.edit_text("🌙 Создаю PDF гороскопа...")
    
    try:
        # Получаем имя пользователя
        user_name = user_data.get('first_name', 'Пользователь') if user_data else 'Пользователь'
        
        # Получаем гороскоп от AI с правильным промптом
        today = datetime.now().strftime("%d.%m.%Y")
        
        # Исправленный промпт - запрещаем AI упоминать конкретные даты
        response = await ai_service.process_question(
            user_id, 
            f"Составь краткий гороскоп для {user_name} на сегодня. НЕ УПОМИНАЙ конкретные числа и даты в ответе. Просто опиши, что ждет человека сегодня."
        )
        
        # Подготавливаем данные для PDF
        pdf_data = {
            'user_name': user_name,
            'date': today,
            'horoscope': response['message']
        }
        
        # Создаем PDF
        pdf_path = pdf_gen.create_horoscope_pdf(pdf_data)
        
        await msg.delete()
        
        # Отправляем PDF
        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(
            pdf_file,
            caption="🌙 Ваш гороскоп"
        )
        
        # Возвращаем в главное меню
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(user_id)
        )
        
        # Удаляем временный файл
        os.remove(pdf_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании PDF гороскопа: {e}\n{traceback.format_exc()}")
        await msg.edit_text(f"❌ Ошибка: {str(e)}")