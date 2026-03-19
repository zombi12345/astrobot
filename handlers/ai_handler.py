from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from states import AIQuestionStates
from ai_service_n1n import ai_service
from keyboards.main import ai_question_keyboard, back_to_menu_keyboard
from utils.validators import validator
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "ai_question")
async def ai_question_menu(callback: CallbackQuery):
    text = (
        "🤖 **Астролог ИИ**\n\n"
        "Задайте любой вопрос о гороскопах, знаках зодиака, "
        "совместимости или влиянии планет!\n\n"
        "📝 **Примеры:**\n"
        "• Что ждёт Овна на этой неделе?\n"
        "• Какая совместимость у Льва и Скорпиона?\n"
        "• Как ретроградный Меркурий влияет на меня?"
    )
    await callback.message.edit_text(text, reply_markup=ai_question_keyboard())

@router.callback_query(F.data == "ask_ai")
async def start_ai_question(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AIQuestionStates.waiting_question)
    await callback.message.answer(
        "🔮 **Задайте ваш вопрос**\n\n"
        "Напишите любой астрологический вопрос, и я дам вам ответ."
    )

@router.message(AIQuestionStates.waiting_question)
async def process_ai_question(message: Message, state: FSMContext):
    await state.clear()
    
    # Валидируем вопрос
    valid, result = validator.validate_question(message.text)
    
    if not valid:
        await message.answer(
            f"❌ {result}\n\n"
            "Пожалуйста, задайте осмысленный вопрос.",
            reply_markup=ai_question_keyboard()
        )
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer("🔮 Астролог анализирует ваш вопрос...")
    
    # Получаем ответ от AI
    response = await ai_service.process_question(
        message.from_user.id, 
        result
    )
    
    # Удаляем сообщение о обработке
    await processing_msg.delete()
    
    # Отправляем ответ
    await message.answer(
        f"🤖 **Ответ астролога:**\n\n{response['message']}",
        reply_markup=ai_question_keyboard()
    )

@router.callback_query(F.data == "ai_examples")
async def ai_examples(callback: CallbackQuery):
    examples = (
        "📝 **Примеры вопросов:**\n\n"
        "🔮 **О гороскопе:**\n"
        "• Что ждёт меня на этой неделе?\n"
        "• Какой день самый удачный для Тельца?\n\n"
        "💕 **О любви:**\n"
        "• Подходит ли мне партнёр-Скорпион?\n"
        "• Как улучшить отношения?\n\n"
        "💼 **О карьере:**\n"
        "• Стоит ли менять работу?\n"
        "• Какая профессия подходит моему знаку?\n\n"
        "✨ **Задавайте свои вопросы!**"
    )
    await callback.message.answer(examples)