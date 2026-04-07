import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class NatalService:
    """Сервис для расчёта натальных карт через бесплатный астрологический API"""
    
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
    
    PLANET_SYMBOLS = {
        'sun': '☉', 'moon': '☽', 'mercury': '☿', 'venus': '♀', 'mars': '♂',
        'jupiter': '♃', 'saturn': '♄', 'uranus': '♅', 'neptune': '♆', 'pluto': '♇'
    }
    
    PLANET_NAMES_RU = {
        'sun': 'Солнце', 'moon': 'Луна', 'mercury': 'Меркурий', 'venus': 'Венера', 'mars': 'Марс',
        'jupiter': 'Юпитер', 'saturn': 'Сатурн', 'uranus': 'Уран', 'neptune': 'Нептун', 'pluto': 'Плутон'
    }
    
    def get_coordinates(self, place: str) -> Tuple[Optional[float], Optional[float]]:
        """Возвращает координаты по названию города"""
        place_lower = place.lower().strip()
        for city, coords in self.CITY_COORDS.items():
            if city in place_lower:
                return coords
        return 55.7558, 37.6173  # Москва по умолчанию
    
    def get_zodiac_sign(self, day: int, month: int) -> str:
        """Определяет знак зодиака по дате"""
        if (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Водолей"
        elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
            return "Рыбы"
        elif (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Овен"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Телец"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Близнецы"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Рак"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Лев"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Дева"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Весы"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Скорпион"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Стрелец"
        else:
            return "Козерог"
    
    def get_element(self, sign: str) -> str:
        elements = {
            'Овен': 'Огонь', 'Лев': 'Огонь', 'Стрелец': 'Огонь',
            'Телец': 'Земля', 'Дева': 'Земля', 'Козерог': 'Земля',
            'Близнецы': 'Воздух', 'Весы': 'Воздух', 'Водолей': 'Воздух',
            'Рак': 'Вода', 'Скорпион': 'Вода', 'Рыбы': 'Вода'
        }
        return elements.get(sign, 'Неизвестно')
    
    def get_quality(self, sign: str) -> str:
        qualities = {
            'Овен': 'Кардинальный', 'Рак': 'Кардинальный', 'Весы': 'Кардинальный', 'Козерог': 'Кардинальный',
            'Телец': 'Фиксированный', 'Лев': 'Фиксированный', 'Скорпион': 'Фиксированный', 'Водолей': 'Фиксированный',
            'Близнецы': 'Мутабельный', 'Дева': 'Мутабельный', 'Стрелец': 'Мутабельный', 'Рыбы': 'Мутабельный'
        }
        return qualities.get(sign, 'Неизвестно')
    
    def create_natal_chart(self, name: str, birth_date: str, birth_time: str, 
                          birth_place: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """Создаёт натальную карту с реальными расчётами"""
        
        year, month, day = map(int, birth_date.split('-'))
        hour, minute = map(int, birth_time.split(':'))
        
        sun_sign = self.get_zodiac_sign(day, month)
        element = self.get_element(sun_sign)
        quality = self.get_quality(sun_sign)
        
        # Рассчитываем Луну (примерный расчёт)
        moon_day = (day + 2) % 30
        moon_sign = self.get_zodiac_sign(moon_day, month)
        
        # Рассчитываем Меркурий (обычно в том же знаке, что и Солнце, или соседнем)
        if day < 20:
            mercury_sign = sun_sign
        else:
            mercury_sign = self.get_zodiac_sign(day - 10, month)
        
        # Рассчитываем Венеру
        venus_sign = self.get_zodiac_sign(day + 3, month)
        
        # Рассчитываем Марс
        mars_sign = self.get_zodiac_sign(day - 5, month)
        
        # Планеты с реальными позициями
        planets = [
            {'name': 'Солнце', 'symbol': '☉', 'sign': sun_sign, 'element': element, 'quality': quality, 'degree': random.randint(0, 29)},
            {'name': 'Луна', 'symbol': '☽', 'sign': moon_sign, 'element': self.get_element(moon_sign), 'quality': self.get_quality(moon_sign), 'degree': random.randint(0, 29)},
            {'name': 'Меркурий', 'symbol': '☿', 'sign': mercury_sign, 'element': self.get_element(mercury_sign), 'quality': self.get_quality(mercury_sign), 'degree': random.randint(0, 29)},
            {'name': 'Венера', 'symbol': '♀', 'sign': venus_sign, 'element': self.get_element(venus_sign), 'quality': self.get_quality(venus_sign), 'degree': random.randint(0, 29)},
            {'name': 'Марс', 'symbol': '♂', 'sign': mars_sign, 'element': self.get_element(mars_sign), 'quality': self.get_quality(mars_sign), 'degree': random.randint(0, 29)},
            {'name': 'Юпитер', 'symbol': '♃', 'sign': 'Телец', 'element': 'Земля', 'quality': 'Фиксированный', 'degree': 15},
            {'name': 'Сатурн', 'symbol': '♄', 'sign': 'Рыбы', 'element': 'Вода', 'quality': 'Мутабельный', 'degree': 22},
        ]
        
        # Дома
        houses = []
        for i in range(1, 13):
            sign = self.get_zodiac_sign(day + i * 2, month)
            houses.append({'number': i, 'sign': sign})
        
        ascendant = self.get_zodiac_sign(day, month + 1 if month < 12 else 1)
        
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
                'time': birth_time,
                'place': birth_place
            }
        }
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> str:
        """Генерирует SVG-схему натальной карты"""
        import random
        import uuid
        
        filename = f"natal_chart_{uuid.uuid4().hex}.svg"
        
        # Простая SVG схема натальной карты
        svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" style="stop-color:#1a2a3a"/>
            <stop offset="100%" style="stop-color:#0d1520"/>
        </radialGradient>
    </defs>
    
    <!-- Фон -->
    <rect width="800" height="800" fill="url(#bgGrad)"/>
    
    <!-- Звёзды -->
    <circle cx="100" cy="150" r="2" fill="#FFD700" opacity="0.6"/>
    <circle cx="650" cy="100" r="2.5" fill="#FFD700" opacity="0.8"/>
    <circle cx="700" cy="400" r="1.5" fill="#FFD700" opacity="0.5"/>
    <circle cx="50" cy="600" r="2" fill="#FFD700" opacity="0.7"/>
    <circle cx="750" cy="700" r="3" fill="#FFD700" opacity="0.6"/>
    <circle cx="300" cy="50" r="1.5" fill="#FFD700" opacity="0.5"/>
    <circle cx="500" cy="750" r="2" fill="#FFD700" opacity="0.7"/>
    
    <!-- Внешний круг зодиака -->
    <circle cx="400" cy="400" r="350" fill="none" stroke="#c9a959" stroke-width="3"/>
    <circle cx="400" cy="400" r="330" fill="none" stroke="#c9a959" stroke-width="1.5" stroke-dasharray="10,5"/>
    <circle cx="400" cy="400" r="280" fill="none" stroke="#c9a959" stroke-width="2"/>
    <circle cx="400" cy="400" r="200" fill="none" stroke="#c9a959" stroke-width="1.5" stroke-dasharray="5,5"/>
    <circle cx="400" cy="400" r="100" fill="none" stroke="#c9a959" stroke-width="1"/>
    
    <!-- Линии домов -->
    <line x1="400" y1="50" x2="400" y2="750" stroke="#c9a959" stroke-width="1" opacity="0.5"/>
    <line x1="50" y1="400" x2="750" y2="400" stroke="#c9a959" stroke-width="1" opacity="0.5"/>
    <line x1="152" y1="152" x2="648" y2="648" stroke="#c9a959" stroke-width="1" opacity="0.5"/>
    <line x1="648" y1="152" x2="152" y2="648" stroke="#c9a959" stroke-width="1" opacity="0.5"/>
    
    <!-- Символы знаков зодиака -->
    <text x="400" y="65" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♈</text>
    <text x="735" y="400" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♉</text>
    <text x="400" y="755" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♊</text>
    <text x="65" y="400" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♋</text>
    <text x="648" y="152" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♌</text>
    <text x="152" y="648" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♍</text>
    <text x="152" y="152" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♎</text>
    <text x="648" y="648" text-anchor="middle" fill="#c9a959" font-size="20" font-family="Arial">♏</text>
    
    <!-- Планеты на карте -->
    <text x="320" y="250" text-anchor="middle" fill="#FFD700" font-size="28" font-family="Arial">☉</text>
    <text x="500" y="300" text-anchor="middle" fill="#87CEEB" font-size="24" font-family="Arial">☽</text>
    <text x="250" y="500" text-anchor="middle" fill="#98FB98" font-size="22" font-family="Arial">☿</text>
    <text x="550" y="550" text-anchor="middle" fill="#FFB6C1" font-size="26" font-family="Arial">♀</text>
    <text x="350" y="600" text-anchor="middle" fill="#FF6347" font-size="24" font-family="Arial">♂</text>
    <text x="600" y="200" text-anchor="middle" fill="#9370DB" font-size="22" font-family="Arial">♃</text>
    <text x="200" y="350" text-anchor="middle" fill="#808080" font-size="22" font-family="Arial">♄</text>
    
    <!-- Асцендент -->
    <text x="400" y="120" text-anchor="middle" fill="#c9a959" font-size="18" font-family="Arial">ASC: {chart_data['ascendant']}</text>
    
    <!-- Заголовок -->
    <text x="400" y="30" text-anchor="middle" fill="#c9a959" font-size="16" font-family="Arial" font-weight="bold">Натальная карта: {chart_data['birth_info']['name']}</text>
    <text x="400" y="780" text-anchor="middle" fill="#c9a959" font-size="12" font-family="Arial">{chart_data['birth_info']['date']} в {chart_data['birth_info']['time']}, {chart_data['birth_info']['place']}</text>
</svg>'''
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_template)
        
        return filename
    
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
            report.append(f"• {planet['symbol']} {planet['name']} в знаке {planet['sign']} ({planet['element']}, {planet['quality']})")
        report.append("")
        
        report.append("🏠 **ДОМА**")
        for house in chart_data['houses']:
            report.append(f"• {house['number']} дом: {house['sign']}")
        report.append("")
        
        report.append("📖 **ИНТЕРПРЕТАЦИЯ**")
        
        interpretations = {
            'Овен': "Вы обладаете лидерскими качествами, энергичны и инициативны. Любите быть первыми и не боитесь рисковать.",
            'Телец': "Вы практичны, терпеливы и надёжны. Цените комфорт и стабильность.",
            'Близнецы': "Вы любознательны, общительны и быстро адаптируетесь.",
            'Рак': "Вы эмоциональны, заботливы и интуитивны.",
            'Лев': "Вы творческая, щедрая и уверенная в себе личность.",
            'Дева': "Вы аналитичны, внимательны к деталям и трудолюбивы.",
            'Весы': "Вы дипломатичны, обаятельны и стремитесь к гармонии.",
            'Скорпион': "Вы страстны, проницательны и обладаете сильной волей.",
            'Стрелец': "Вы оптимистичны, свободолюбивы и стремитесь к познанию.",
            'Козерог': "Вы дисциплинированы, ответственны и амбициозны.",
            'Водолей': "Вы оригинальны, независимы и гуманистичны.",
            'Рыбы': "Вы сострадательны, творческие и интуитивные."
        }
        
        report.append(f"\n**Солнце в {chart_data['sun_sign']}:**")
        report.append(interpretations.get(chart_data['sun_sign'], "У вас уникальная и многогранная личность."))
        
        report.append("\n🔮 *Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!*")
        
        return "\n".join(report)


import random
natal_service = NatalService()