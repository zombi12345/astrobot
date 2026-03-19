from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import CompatibilityStates
from keyboards.main import main_menu_keyboard, back_to_menu_keyboard
from astrology_calculator import compatibility_calc
from utils.validators import validator
from utils.helpers import md2_escape 
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💕 **АНАЛИЗ СОВМЕСТИМОСТИ**\n\n"
        "Введите данные **первого человека** в формате:\n"
        "`Имя, ГГГГ-ММ-ДД, ЧЧ:ММ`\n\n"
        "📝 **Примеры:**\n"
        "• Анна, 1995-06-15, 14:30\n"
        "• Александр, 1990-03-21\n"
        "• Мария, 1988-12-05\n\n"
        "Если время неизвестно, можно указать только дату.",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CompatibilityStates.waiting_partner1)

@router.message(CompatibilityStates.waiting_partner1)
async def process_partner1(message: Message, state: FSMContext):
    valid, result = validator.validate_compatibility_data(message.text)
    
    if not valid:
        await message.answer(
            f"❌ {result['error']}\n\n"
            "Пожалуйста, введите данные в правильном формате:\n"
            "`Имя, ГГГГ-ММ-ДД, ЧЧ:ММ`",
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(person1=result)
    
    await message.answer(
        f"✅ Данные сохранены: {result['name']}, {result['date']}" + 
        (f", {result['time']}" if result['time'] != '12:00' else "") + "\n\n"
        "Теперь введите данные **второго человека** в том же формате:",
        parse_mode="Markdown"
    )
    await state.set_state(CompatibilityStates.waiting_partner2)

@router.message(CompatibilityStates.waiting_partner2)
async def process_partner2(message: Message, state: FSMContext):
    valid, result = validator.validate_compatibility_data(message.text)
    
    if not valid:
        await message.answer(
            f"❌ {result['error']}\n\n"
            "Пожалуйста, введите данные в правильном формате:",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    person1 = data['person1']
    person2 = result
    
    await state.clear()
    
    # Отправляем сообщение о расчете
    processing_msg = await message.answer("🔮 Рассчитываю совместимость...")
    
    try:
        # Рассчитываем совместимость
        result = compatibility_calc.calculate_compatibility(person1, person2)
        
        # Формируем звездный рейтинг
        stars = "⭐" * (result['total_score'] // 10) + "☆" * (10 - (result['total_score'] // 10))
        
        # Формируем ответ
        response = f"""💕 **АНАЛИЗ СОВМЕСТИМОСТИ**

**{person1['name']}**  и  **{person2['name']}**

{stars} **{result['total_score']}%**

📊 **ОСНОВНЫЕ ДАННЫЕ:**
• Знаки зодиака: {result['signs'][0]} и {result['signs'][1]}
• Китайский гороскоп: {result['chinese'][0]} и {result['chinese'][1]}
• Стихии: {result['elements'][0]} и {result['elements'][1]}

"""
        
        # Добавляем модификаторы
        if result['modifiers']:
            response += "✨ **ДОПОЛНИТЕЛЬНЫЕ ФАКТОРЫ:**\n"
            for factor, score in result['modifiers']:
                sign = "+" if score > 0 else ""
                response += f"• {factor}: {sign}{score}%\n"
            response += "\n"
        
        response += f"""📝 **ОПИСАНИЕ:**
{result['description']}

💫 **СОВЕТ:**
{result['advice']}

🔮 Помните: астрология - это руководство, а не приговор. Любовь и взаимопонимание могут преодолеть любые преграды!"""
        
        await processing_msg.delete()
        await message.answer(
            response,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(message.from_user.id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await processing_msg.edit_text(f"❌ Ошибка при расчете: {str(e)}")
        await message.answer(
            "Попробуйте еще раз с правильными данными",
            reply_markup=back_to_menu_keyboard()
        )