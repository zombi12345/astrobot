from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, SuccessfulPayment, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database.postgres_db import add_payment, set_subscription, get_user
from config import ADMINS, BOT_TOKEN
import logging

logger = logging.getLogger(__name__)
router = Router()

PRICES = {
    "7":  {"days": 7,  "stars": 99},
    "30": {"days": 30, "stars": 299},
    "90": {"days": 90, "stars": 699},
}

# Команда для просмотра баланса Stars бота
@router.message(Command("stars_balance"))
async def cmd_stars_balance(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.answer("❌ Доступно только администратору.")
        return
    
    bot = Bot(token=BOT_TOKEN)
    try:
        balance = await bot.get_my_star_balance()
        await message.answer(f"⭐️ **Баланс звёзд бота:** {balance} Stars\n\n"
                             "Эти звёзды поступили от пользователей за подписки.\n"
                             "Потратить их можно на рекламу или подарить другим пользователям.",
                             parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        await message.answer("❌ Не удалось получить баланс. Убедитесь, что бот имеет доступ к API Stars.")
    finally:
        await bot.session.close()

@router.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery):
    plan = callback.data.split("_")[1]
    if plan not in PRICES:
        await callback.answer("Неверный тариф", show_alert=True)
        return
    days = PRICES[plan]["days"]
    stars = PRICES[plan]["stars"]
    await callback.message.answer_invoice(
        title=f"Подписка AstroBot на {days} дней",
        description=f"Доступ ко всем функциям бота на {days} дней",
        payload=f"sub_{days}_{stars}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Подписка", amount=stars)],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить ⭐️", pay=True)]
        ])
    )
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    stars_paid = payment.total_amount
    payload = payment.invoice_payload
    try:
        _, days_str, stars_str = payload.split("_")
        days = int(days_str)
        stars_expected = int(stars_str)
        if stars_paid != stars_expected:
            logger.error(f"Сумма не совпадает: {stars_paid} vs {stars_expected}")
            await message.answer("❌ Ошибка оплаты, обратитесь к администратору.")
            return
        # Активация подписки
        await set_subscription(user_id, days)
        await add_payment(user_id, stars_paid, payment.telegram_payment_charge_id)
        
        # Уведомление администратору
        bot = Bot(token=BOT_TOKEN)
        user_data = await get_user(user_id)
        name = user_data.get('first_name') or user_data.get('username') or str(user_id)
        for admin_id in ADMINS:
            try:
                await bot.send_message(
                    admin_id,
                    f"💎 **Новая подписка!**\n\n"
                    f"👤 Пользователь: {name} (ID: {user_id})\n"
                    f"📅 Срок: {days} дней\n"
                    f"⭐️ Оплачено: {stars_paid} Stars\n"
                    f"🗓️ Действует до: {payment.telegram_payment_charge_id}",
                    parse_mode="Markdown"
                )
            except:
                pass
        await bot.session.close()
        
        await message.answer(
            f"✅ **Подписка активирована на {days} дней!**\n\n"
            "Благодарим за использование AstroBot.",
            parse_mode="Markdown"
        )
        from keyboards.main import main_menu_keyboard
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(user_id))
    except Exception as e:
        logger.error(f"Ошибка активации подписки: {e}")
        await message.answer("❌ Произошла ошибка. Администратор уведомлён.")

@router.message(Command("refund"))
async def cmd_refund(message: Message):
    await message.answer("🔹 Для возврата средств свяжитесь с поддержкой: @SupportBot")

@router.message(Command("paysupport"))
async def cmd_pay_support(message: Message):
    await message.answer("📞 Если у вас проблемы с оплатой:\n1. Проверьте баланс Stars\n2. Повторите оплату через /pay\n3. Напишите @SupportBot")