from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.main import main_menu_keyboard, back_to_menu_keyboard
import random
import hashlib
import json

router = Router()

class CompatibilityStates(StatesGroup):
    waiting_partner1 = State()
    waiting_partner2 = State()

# Кэш для хранения результатов совместимости
compatibility_cache = {}

# База данных знаков зодиака
ZODIAC_SIGNS = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 
                'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']

# Стихии знаков
ELEMENTS = {
    'Овен': 'Огонь', 'Лев': 'Огонь', 'Стрелец': 'Огонь',
    'Телец': 'Земля', 'Дева': 'Земля', 'Козерог': 'Земля',
    'Близнецы': 'Воздух', 'Весы': 'Воздух', 'Водолей': 'Воздух',
    'Рак': 'Вода', 'Скорпион': 'Вода', 'Рыбы': 'Вода'
}

# Планеты-покровители
RULING_PLANETS = {
    'Овен': 'Марс', 'Телец': 'Венера', 'Близнецы': 'Меркурий',
    'Рак': 'Луна', 'Лев': 'Солнце', 'Дева': 'Меркурий',
    'Весы': 'Венера', 'Скорпион': 'Плутон', 'Стрелец': 'Юпитер',
    'Козерог': 'Сатурн', 'Водолей': 'Уран', 'Рыбы': 'Нептун'
}

# Качества знаков (кардинальные, фиксированные, мутабельные)
QUALITIES = {
    'Овен': 'Кардинальный', 'Рак': 'Кардинальный', 'Весы': 'Кардинальный', 'Козерог': 'Кардинальный',
    'Телец': 'Фиксированный', 'Лев': 'Фиксированный', 'Скорпион': 'Фиксированный', 'Водолей': 'Фиксированный',
    'Близнецы': 'Мутабельный', 'Дева': 'Мутабельный', 'Стрелец': 'Мутабельный', 'Рыбы': 'Мутабельный'
}

def get_compatibility_key(sign1, sign2):
    """Создаёт ключ для кэширования совместимости"""
    signs = sorted([sign1.strip().lower(), sign2.strip().lower()])
    return f"{signs[0]}_{signs[1]}"

def get_detailed_compatibility(sign1, sign2):
    """Возвращает детальный анализ совместимости двух знаков"""
    
    # Проверяем кэш
    cache_key = get_compatibility_key(sign1, sign2)
    if cache_key in compatibility_cache:
        return compatibility_cache[cache_key]
    
    # Используем seed на основе знаков для стабильности (но разные для разных пар)
    seed = int(hashlib.md5(f"{sign1}_{sign2}".encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    element1 = ELEMENTS.get(sign1, 'Неизвестно')
    element2 = ELEMENTS.get(sign2, 'Неизвестно')
    planet1 = RULING_PLANETS.get(sign1, 'Неизвестно')
    planet2 = RULING_PLANETS.get(sign2, 'Неизвестно')
    quality1 = QUALITIES.get(sign1, 'Неизвестно')
    quality2 = QUALITIES.get(sign2, 'Неизвестно')
    
    # Совместимость стихий
    element_compatibility = {
        ('Огонь', 'Огонь'): "Огонь с Огнём - страстный, но взрывной союз. Много энергии, но нужен баланс.",
        ('Огонь', 'Земля'): "Огонь и Земля - разные стихии, но могут дополнять друг друга. Огонь вдохновляет, Земля стабилизирует.",
        ('Огонь', 'Воздух'): "Огонь и Воздух - отличная пара! Воздух раздувает пламя, делая союз ярким и динамичным.",
        ('Огонь', 'Вода'): "Огонь и Вода - сложное сочетание. Возможны как страсть, так и конфликты. Нужен компромисс.",
        ('Земля', 'Земля'): "Земля с Землёй - стабильный, надёжный союз. Оба ценят практичность и комфорт.",
        ('Земля', 'Воздух'): "Земля и Воздух - нейтральное сочетание. Воздух приносит идеи, Земля их реализует.",
        ('Земля', 'Вода'): "Земля и Вода - гармоничный союз. Вода питает Землю, создавая плодородную почву для отношений.",
        ('Воздух', 'Воздух'): "Воздух с Воздухом - интеллектуальный союз. Много общения, но не хватает глубины.",
        ('Воздух', 'Вода'): "Воздух и Вода - переменчивое сочетание. Нужно учиться понимать друг друга.",
        ('Вода', 'Вода'): "Вода с Водой - глубокий, эмоциональный союз. Вы чувствуете друг друга без слов."
    }
    
    element_key = (element1, element2)
    element_desc = element_compatibility.get(element_key, element_compatibility.get((element2, element1), "Средняя совместимость стихий."))
    
    # Совместимость планет
    planet_desc = f"{planet1} и {planet2} создают уникальную динамику в ваших отношениях."
    
    # Общая оценка (0-100)
    base_scores = {
        ('Овен', 'Лев'): 95, ('Овен', 'Стрелец'): 98, ('Овен', 'Близнецы'): 75,
        ('Телец', 'Дева'): 90, ('Телец', 'Козерог'): 95, ('Телец', 'Рак'): 70,
        ('Близнецы', 'Весы'): 92, ('Близнецы', 'Водолей'): 88,
        ('Рак', 'Скорпион'): 96, ('Рак', 'Рыбы'): 94,
        ('Лев', 'Стрелец'): 97, ('Лев', 'Овен'): 93,
        ('Дева', 'Козерог'): 92, ('Дева', 'Телец'): 88,
        ('Весы', 'Водолей'): 91, ('Весы', 'Близнецы'): 85,
        ('Скорпион', 'Рыбы'): 95, ('Скорпион', 'Рак'): 92,
        ('Стрелец', 'Овен'): 96, ('Стрелец', 'Лев'): 94,
        ('Козерог', 'Телец'): 90, ('Козерог', 'Дева'): 88,
        ('Водолей', 'Весы'): 90, ('Водолей', 'Близнецы'): 86,
        ('Рыбы', 'Рак'): 94, ('Рыбы', 'Скорпион'): 92
    }
    
    key = (sign1, sign2)
    score = base_scores.get(key, base_scores.get((sign2, sign1), random.randint(55, 90)))
    
    # Определяем уровень совместимости
    if score >= 90:
        level = "Идеальная совместимость! 🌟"
    elif score >= 80:
        level = "Отличная совместимость! ✨"
    elif score >= 70:
        level = "Хорошая совместимость 💫"
    elif score >= 60:
        level = "Средняя совместимость ⚡"
    else:
        level = "Сложная совместимость, но возможная 🌊"
    
    # Сильные стороны
    strengths_list = [
        "Взаимное уважение и понимание",
        "Общие ценности и цели",
        "Способность поддерживать друг друга",
        "Хорошая сексуальная совместимость",
        "Интеллектуальная близость",
        "Эмоциональная глубина",
        "Умение весело проводить время вместе",
        "Взаимодополняющие качества"
    ]
    random.shuffle(strengths_list)
    strengths = ", ".join(strengths_list[:3])
    
    # Слабые стороны
    weaknesses_list = [
        "Возможны конфликты из-за разного темперамента",
        "Разные подходы к финансам",
        "Несовпадение в бытовых привычках",
        "Разный темп принятия решений",
        "Эмоциональная несовместимость в стрессовых ситуациях",
        "Разные социальные потребности",
        "Конкуренция за лидерство"
    ]
    random.shuffle(weaknesses_list)
    weaknesses = ", ".join(weaknesses_list[:3])
    
    # Рекомендации
    recommendations_list = [
        "Учитесь слушать и слышать друг друга",
        "Проводите время на природе вместе",
        "Найдите общее хобби",
        "Чаще говорите о своих чувствах",
        "Планируйте совместные путешествия",
        "Создайте общие традиции",
        "Уважайте личное пространство партнёра",
        "Работайте над конфликтами конструктивно"
    ]
    random.shuffle(recommendations_list)
    recommendation = random.choice(recommendations_list)
    
    # Символическое число
    lucky_numbers = [2, 3, 5, 7, 8, 9, 11, 13, 17, 21]
    lucky_number = random.choice(lucky_numbers)
    
    # Цвет отношений
    colors = ["Красный", "Розовый", "Золотой", "Синий", "Зелёный", "Фиолетовый"]
    color = random.choice(colors)
    
    result = {
        'score': score,
        'level': level,
        'element1': element1,
        'element2': element2,
        'element_desc': element_desc,
        'planet1': planet1,
        'planet2': planet2,
        'planet_desc': planet_desc,
        'quality1': quality1,
        'quality2': quality2,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'recommendation': recommendation,
        'lucky_number': lucky_number,
        'color': color
    }
    
    # Сохраняем в кэш
    compatibility_cache[cache_key] = result
    
    # Сброс random
    random.seed()
    
    return result

def parse_zodiac_input(text):
    """Пытается извлечь знак зодиака из текста"""
    text_lower = text.lower()
    for sign in ZODIAC_SIGNS:
        if sign.lower() in text_lower:
            return sign
    return None

@router.callback_query(F.data == "compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💕 **АНАЛИЗ СОВМЕСТИМОСТИ**\n\n"
        "Введите знак зодиака **первого партнёра**\n"
        "Например: Овен, Телец, Лев, Скорпион и т.д.\n\n"
        "Или отправьте дату рождения в формате ГГГГ-ММ-ДД",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CompatibilityStates.waiting_partner1)

@router.message(CompatibilityStates.waiting_partner1)
async def process_partner1(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Пробуем определить знак
    sign1 = parse_zodiac_input(text)
    
    if not sign1:
        await message.answer(
            "❌ Не удалось определить знак зодиака.\n\n"
            "Пожалуйста, введите название знака (например: Овен, Телец, Лев)\n"
            "или дату рождения в формате ГГГГ-ММ-ДД",
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(sign1=sign1)
    await state.set_state(CompatibilityStates.waiting_partner2)
    
    await message.answer(
        f"✅ Первый знак: **{sign1}**\n\n"
        "Теперь введите знак зодиака **второго партнёра**\n"
        "или дату рождения:",
        parse_mode="Markdown"
    )

@router.message(CompatibilityStates.waiting_partner2)
async def process_partner2(message: Message, state: FSMContext):
    text = message.text.strip()
    
    sign2 = parse_zodiac_input(text)
    
    if not sign2:
        await message.answer(
            "❌ Не удалось определить знак зодиака.\n\n"
            "Пожалуйста, введите название знака (например: Овен, Телец, Лев)",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    sign1 = data['sign1']
    
    await state.clear()
    
    processing_msg = await message.answer("🔮 Рассчитываю совместимость...")
    
    # Получаем детальный анализ
    result = get_detailed_compatibility(sign1, sign2)
    
    stars = "⭐" * (result['score'] // 10) + "☆" * (10 - (result['score'] // 10))
    
    response = f"""💕 **АНАЛИЗ СОВМЕСТИМОСТИ**

**{sign1}** 💞 **{sign2}**

{stars} **{result['score']}%** - {result['level']}

━━━━━━━━━━━━━━━━━━━━━━━━

✨ **АСТРОЛОГИЧЕСКИЕ ДАННЫЕ:**

• Стихии: {result['element1']} и {result['element2']}
• Планеты: {result['planet1']} и {result['planet2']}
• Качества: {result['quality1']} и {result['quality2']}

🌊 **ГАРМОНИЯ СТИХИЙ:**
{result['element_desc']}

🪐 **ПЛАНЕТАРНОЕ ВЛИЯНИЕ:**
{result['planet_desc']}

✅ **СИЛЬНЫЕ СТОРОНЫ:**
{result['strengths']}

⚠️ **СЛАБЫЕ СТОРОНЫ:**
{result['weaknesses']}

💫 **РЕКОМЕНДАЦИЯ:**
{result['recommendation']}

🍀 **СИМВОЛИЧЕСКОЕ ЧИСЛО:** {result['lucky_number']}
🌈 **ЦВЕТ ОТНОШЕНИЙ:** {result['color']}

━━━━━━━━━━━━━━━━━━━━━━━━

🔮 Помните: астрология - это руководство, а не приговор. Любовь и взаимопонимание могут преодолеть любые преграды!"""

    await processing_msg.delete()
    await message.answer(response, parse_mode="Markdown", reply_markup=main_menu_keyboard(message.from_user.id))