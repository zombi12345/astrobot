from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, SuccessfulPayment, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database.db import add_payment, set_subscription
from config import ADMINS
import logging

logger = logging.getLogger(__name__)
router = Router()

# Цены в Stars: 1 Star = 1 цент, 200 Stars = 2 рубля (пример)
PRICES = {
    "7": {"days": 7, "stars": 70},
    "30": {"days": 30, "stars": 300},
    "90": {"days": 90, "stars": 800},
}

@router.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery):
    plan = callback.data.split("_")[1]   # "7", "30" или "90"
    if plan not in PRICES:
        await callback.answer("Неверный тариф", show_alert=True)
        return
    
    days = PRICES[plan]["days"]
    stars = PRICES[plan]["stars"]
    
    # Создаём инвойс
    await callback.message.answer_invoice(
        title=f"Подписка AstroBot на {days} дней",
        description=f"Доступ ко всем функциям бота на {days} дней",
        payload=f"sub_{days}_{stars}",
        provider_token="",           # для Stars не нужен
        currency="XTR",
        prices=[LabeledPrice(label="Подписка", amount=stars)],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить ⭐️", pay=True)]
        ])
    )
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Обязательно подтверждаем
    await pre_checkout_query.answer(ok=True)
    logger.info(f"PreCheckout для пользователя {pre_checkout_query.from_user.id}")

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    stars_paid = payment.total_amount
    payload = payment.invoice_payload   # например "sub_30_300"
    
    try:
        _, days_str, stars_str = payload.split("_")
        days = int(days_str)
        stars_expected = int(stars_str)
        if stars_paid != stars_expected:
            logger.error(f"Сумма не совпадает: {stars_paid} vs {stars_expected}")
            await message.answer("❌ Ошибка оплаты, обратитесь к администратору.")
            return
        
        # Активируем подписку
        await set_subscription(user_id, days)
        await add_payment(user_id, stars_paid, payment.telegram_payment_charge_id)
        
        await message.answer(
            f"✅ **Подписка активирована на {days} дней!**\n\n"
            "Благодарим за использование AstroBot. Теперь вам доступны все функции.",
            parse_mode="Markdown"
        )
        # Можно показать главное меню
        from keyboards.main import main_menu_keyboard
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(user_id))
    except Exception as e:
        logger.error(f"Ошибка активации подписки: {e}")
        await message.answer("❌ Произошла ошибка при активации подписки. Администратор уведомлён.")

@router.message(Command("refund"))
async def cmd_refund(message: Message):
    await message.answer(
        "🔹 Для возврата средств, пожалуйста, свяжитесь с поддержкой: @JanSalProg\n"
        "Или напишите на почту support@astrobot.com"
    )

@router.message(Command("paysupport"))
async def cmd_pay_support(message: Message):
    await message.answer(
        "📞 Если у вас возникли проблемы с оплатой:\n"
        "1. Убедитесь, что на вашем счету достаточно Telegram Stars.\n"
        "2. Попробуйте повторить оплату через /pay\n"
        "3. Если не помогает – обратитесь к @JanSalProg"
    )