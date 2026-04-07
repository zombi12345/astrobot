import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from vedastro import *

logger = logging.getLogger(__name__)

class NatalService:
    """Сервис для расчёта натальных карт через VedAstro"""
    
    # Координаты городов
    CITY_COORDS = {
        'минск': (53.9045, 27.5615),
        'гомель': (52.4345, 30.9754),
        'могилёв': (53.8945, 30.3314),
        'витебск': (55.1848, 30.2016),
        'гродно': (53.6694, 23.8131),
        'брест': (52.0976, 23.7341),
        'барановичи': (53.1333, 26.0167),
        'москва': (55.7558, 37.6173),
        'санкт-петербург': (59.9343, 30.3351),
        'киев': (50.4501, 30.5234),
        'варшава': (52.2297, 21.0122),
        'вильнюс': (54.6872, 25.2797),
    }
    
    # Часовые пояса
    TIMEZONES = {
        'минск': '+03:00',
        'москва': '+03:00',
        'санкт-петербург': '+03:00',
        'киев': '+02:00',
        'варшава': '+01:00',
        'вильнюс': '+02:00',
    }
    
    def __init__(self):
        # Устанавливаем бесплатный API ключ для VedAstro
        Calculate.SetAPIKey('FreeAPIUser')
        # Устанавливаем аяншамсу Лахири (по умолчанию для ведической астрологии)
        Calculate.SetAyanamsa(Ayanamsa.Lahiri)
        logger.info("VedAstro инициализирован")
    
    def get_coordinates(self, place: str) -> Tuple[float, float, str]:
        """Возвращает координаты и часовой пояс по названию города"""
        place_lower = place.lower().strip()
        for city, coords in self.CITY_COORDS.items():
            if city in place_lower:
                tz = self.TIMEZONES.get(city, '+03:00')
                return coords[0], coords[1], tz
        return 55.7558, 37.6173, '+03:00'  # Москва по умолчанию
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """Проверяет корректность даты"""
        try:
            year, month, day = map(int, date_str.split('-'))
            birth_date = datetime(year, month, day)
            if birth_date > datetime.now():
                return False, None
            if (datetime.now() - birth_date).days / 365.25 > 120:
                return False, None
            return True, (year, month, day)
        except:
            return False, None
    
    def validate_time(self, time_str: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Проверяет корректность времени"""
        try:
            if time_str == '/skip' or not time_str:
                return True, (12, 0)
            hour, minute = map(int, time_str.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return True, (hour, minute)
            return False, None
        except:
            return False, None
    
    def _create_time_object(self, birth_date: str, birth_time: str, birth_place: str) -> Time:
        """Создаёт объект Time для VedAstro"""
        year, month, day = map(int, birth_date.split('-'))
        hour, minute = map(int, birth_time.split(':'))
        lat, lon, tz = self.get_coordinates(birth_place)
        
        geo = GeoLocation(birth_place, lon, lat)
        return Time(
            hour=hour,
            minute=minute,
            day=day,
            month=month,
            year=year,
            offset=tz,
            geolocation=geo
        )
    
    async def create_natal_chart(self, name: str, birth_date: str, birth_time: str,
                                  birth_place: str) -> Dict[str, Any]:
        """Создаёт натальную карту через VedAstro"""
        
        # Валидация
        valid, date_parts = self.validate_date(birth_date)
        if not valid:
            raise ValueError("Неверная дата рождения")
        
        valid, time_parts = self.validate_time(birth_time)
        if not valid:
            raise ValueError("Неверное время рождения")
        
        hour, minute = time_parts if time_parts else (12, 0)
        birth_time_corrected = f"{hour:02d}:{minute:02d}"
        
        # Создаём объект времени
        birth_time_obj = self._create_time_object(birth_date, birth_time_corrected, birth_place)
        
        # Получаем данные о планетах
        planets = []
        planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
        planet_names_ru = ['Солнце', 'Луна', 'Меркурий', 'Венера', 'Марс', 'Юпитер', 'Сатурн']
        planet_symbols = ['☉', '☽', '☿', '♀', '♂', '♃', '♄']
        
        for i, eng_name in enumerate(planet_names):
            try:
                planet_data = Calculate.AllPlanetData(getattr(PlanetName, eng_name), birth_time_obj)
                planets.append({
                    'name': planet_names_ru[i],
                    'symbol': planet_symbols[i],
                    'sign': planet_data.Sign.Name if hasattr(planet_data, 'Sign') else 'Неизвестно',
                    'house': planet_data.HousePlanetIsIn if hasattr(planet_data, 'HousePlanetIsIn') else '?',
                    'retrograde': planet_data.Retrograde if hasattr(planet_data, 'Retrograde') else False,
                    'longitude': planet_data.Longitude if hasattr(planet_data, 'Longitude') else 0
                })
            except Exception as e:
                logger.error(f"Ошибка получения данных для {eng_name}: {e}")
                planets.append({
                    'name': planet_names_ru[i],
                    'symbol': planet_symbols[i],
                    'sign': 'Неизвестно',
                    'house': '?',
                    'retrograde': False,
                    'longitude': 0
                })
        
        # Получаем данные о домах
        houses = []
        for i in range(1, 13):
            try:
                house_data = Calculate.AllHouseData(i, birth_time_obj)
                houses.append({
                    'number': i,
                    'sign': house_data.SignName if hasattr(house_data, 'SignName') else 'Неизвестно',
                    'lord': house_data.LordName if hasattr(house_data, 'LordName') else '?',
                    'longitude': house_data.Longitude if hasattr(house_data, 'Longitude') else 0
                })
            except Exception as e:
                logger.error(f"Ошибка получения данных для дома {i}: {e}")
                houses.append({
                    'number': i,
                    'sign': 'Неизвестно',
                    'lord': '?',
                    'longitude': 0
                })
        
        # Получаем знак Солнца (для интерпретации)
        sun_sign = planets[0]['sign'] if planets else 'Неизвестно'
        
        # Определяем стихию и качество
        elements = {
            'Овен': 'Огонь', 'Лев': 'Огонь', 'Стрелец': 'Огонь',
            'Телец': 'Земля', 'Дева': 'Земля', 'Козерог': 'Земля',
            'Близнецы': 'Воздух', 'Весы': 'Воздух', 'Водолей': 'Воздух',
            'Рак': 'Вода', 'Скорпион': 'Вода', 'Рыбы': 'Вода'
        }
        
        qualities = {
            'Овен': 'Кардинальный', 'Рак': 'Кардинальный', 'Весы': 'Кардинальный', 'Козерог': 'Кардинальный',
            'Телец': 'Фиксированный', 'Лев': 'Фиксированный', 'Скорпион': 'Фиксированный', 'Водолей': 'Фиксированный',
            'Близнецы': 'Мутабельный', 'Дева': 'Мутабельный', 'Стрелец': 'Мутабельный', 'Рыбы': 'Мутабельный'
        }
        
        element = elements.get(sun_sign, 'Неизвестно')
        quality = qualities.get(sun_sign, 'Неизвестно')
        
        # Асцендент (1-й дом)
        ascendant = houses[0]['sign'] if houses else 'Неизвестно'
        
        return {
            'sun_sign': sun_sign,
            'element': element,
            'quality': quality,
            'ascendant': ascendant,
            'planets': planets,
            'houses': houses,
            'birth_info': {
                'name': name,
                'date': birth_date,
                'time': birth_time_corrected,
                'place': birth_place
            }
        }
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Генерирует SVG-схему натальной карты (упрощённая версия)"""
        try:
            import random
            filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            
            svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" style="stop-color:#1a2a3a"/>
            <stop offset="100%" style="stop-color:#0d1520"/>
        </radialGradient>
    </defs>
    <rect width="800" height="800" fill="url(#bgGrad)"/>
    <circle cx="400" cy="400" r="350" fill="none" stroke="#c9a959" stroke-width="3"/>
    <circle cx="400" cy="400" r="280" fill="none" stroke="#c9a959" stroke-width="2"/>
    <circle cx="400" cy="400" r="200" fill="none" stroke="#c9a959" stroke-width="1.5"/>
    <circle cx="400" cy="400" r="100" fill="none" stroke="#c9a959" stroke-width="1"/>
    <line x1="400" y1="50" x2="400" y2="750" stroke="#c9a959" stroke-width="1" opacity="0.5"/>
    <line x1="50" y1="400" x2="750" y2="400" stroke="#c9a959" stroke-width="1" opacity="0.5"/>
    <text x="400" y="65" text-anchor="middle" fill="#c9a959" font-size="22">♈</text>
    <text x="735" y="400" text-anchor="middle" fill="#c9a959" font-size="22">♉</text>
    <text x="400" y="755" text-anchor="middle" fill="#c9a959" font-size="22">♊</text>
    <text x="65" y="400" text-anchor="middle" fill="#c9a959" font-size="22">♋</text>
    <text x="648" y="152" text-anchor="middle" fill="#c9a959" font-size="22">♌</text>
    <text x="152" y="648" text-anchor="middle" fill="#c9a959" font-size="22">♍</text>
    <text x="152" y="152" text-anchor="middle" fill="#c9a959" font-size="22">♎</text>
    <text x="648" y="648" text-anchor="middle" fill="#c9a959" font-size="22">♏</text>
    
    <text x="400" y="120" text-anchor="middle" fill="#c9a959" font-size="18" font-weight="bold">ASC: {chart_data['ascendant']}</text>
    <text x="400" y="30" text-anchor="middle" fill="#c9a959" font-size="16" font-weight="bold">Натальная карта: {chart_data['birth_info']['name']}</text>
    <text x="400" y="780" text-anchor="middle" fill="#c9a959" font-size="12">{chart_data['birth_info']['date']} в {chart_data['birth_info']['time']}, {chart_data['birth_info']['place']}</text>
</svg>'''
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(svg_template)
            return filename
        except Exception as e:
            logger.error(f"Ошибка генерации SVG: {e}")
            return None
    
    def generate_report_text(self, chart_data: Dict[str, Any]) -> str:
        """Генерирует текстовый отчёт по натальной карте"""
        report = []
        
        report.append("🌟 **НАТАЛЬНАЯ КАРТА**")
        report.append(f"👤 {chart_data['birth_info']['name']}")
        report.append(f"📅 {chart_data['birth_info']['date']} в {chart_data['birth_info']['time']}")
        report.append(f"📍 {chart_data['birth_info']['place']}")
        report.append("")
        
        report.append("✨ **ОСНОВНЫЕ ХАРАКТЕРИСТИКИ**")
        report.append(f"• Солнце в знаке: {chart_data['sun_sign']}")
        report.append(f"• Стихия: {chart_data['element']}")
        report.append(f"• Качество: {chart_data['quality']}")
        report.append(f"• Асцендент (ASC): {chart_data['ascendant']}")
        report.append("")
        
        report.append("🔮 **ПОЛОЖЕНИЕ ПЛАНЕТ**")
        for planet in chart_data['planets']:
            retro = " (ретроградный)" if planet.get('retrograde') else ""
            report.append(f"• {planet['symbol']} {planet['name']} в знаке {planet['sign']} ({planet['house']} дом){retro}")
        report.append("")
        
        report.append("🏠 **ДОМА**")
        for house in chart_data['houses']:
            report.append(f"• {house['number']} дом: {house['sign']} (упр. {house['lord']})")
        report.append("")
        
        report.append("📖 **ИНТЕРПРЕТАЦИЯ**")
        
        interpretations = {
            'Овен': "Вы обладаете лидерскими качествами, энергичны и инициативны. Любите быть первыми и не боитесь рисковать.",
            'Телец': "Вы практичны, терпеливы и надёжны. Цените комфорт и стабильность, умеете достигать поставленных целей.",
            'Близнецы': "Вы любознательны, общительны и быстро адаптируетесь. Любите узнавать новое и делиться информацией.",
            'Рак': "Вы эмоциональны, заботливы и интуитивны. Семья и дом для вас имеют первостепенное значение.",
            'Лев': "Вы творческая, щедрая и уверенная в себе личность. Любите быть в центре внимания и дарить радость другим.",
            'Дева': "Вы аналитичны, внимательны к деталям и трудолюбивы. Стремитесь к совершенству во всём.",
            'Весы': "Вы дипломатичны, обаятельны и стремитесь к гармонии. Цените красоту и справедливость.",
            'Скорпион': "Вы страстны, проницательны и обладаете сильной волей. Способны на глубокие трансформации.",
            'Стрелец': "Вы оптимистичны, свободолюбивы и стремитесь к познанию. Любите путешествия и приключения.",
            'Козерог': "Вы дисциплинированы, ответственны и амбициозны. Умеете достигать поставленных целей.",
            'Водолей': "Вы оригинальны, независимы и гуманистичны. Любите всё новое и нестандартное.",
            'Рыбы': "Вы сострадательны, творческие и интуитивные. Обладаете богатым воображением."
        }
        
        report.append(f"\n**Солнце в {chart_data['sun_sign']}:**")
        report.append(interpretations.get(chart_data['sun_sign'], "У вас уникальная и многогранная личность."))
        
        report.append("\n🔮 *Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!*")
        
        return "\n".join(report)


natal_service = NatalService()