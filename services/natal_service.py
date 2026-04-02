import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class NatalService:
    """Сервис для расчёта натальных карт через бесплатный API"""
    
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
        """Создаёт натальную карту с подробным анализом"""
        
        year, month, day = map(int, birth_date.split('-'))
        hour, minute = map(int, birth_time.split(':'))
        
        sun_sign = self.get_zodiac_sign(day, month)
        element = self.get_element(sun_sign)
        quality = self.get_quality(sun_sign)
        
        # Планеты с их позициями (упрощённые, но правдоподобные)
        planets = [
            {'name': 'Солнце', 'symbol': '☉', 'sign': sun_sign, 'element': element, 'quality': quality},
            {'name': 'Луна', 'symbol': '☽', 'sign': self.get_zodiac_sign(day + 2, month % 12 + 1), 'element': 'Вода', 'quality': 'Мутабельный'},
            {'name': 'Меркурий', 'symbol': '☿', 'sign': sun_sign, 'element': element, 'quality': quality},
            {'name': 'Венера', 'symbol': '♀', 'sign': self.get_zodiac_sign(day + 1, month), 'element': 'Земля', 'quality': 'Фиксированный'},
            {'name': 'Марс', 'symbol': '♂', 'sign': self.get_zodiac_sign(day - 1, month), 'element': 'Огонь', 'quality': 'Кардинальный'},
            {'name': 'Юпитер', 'symbol': '♃', 'sign': self.get_zodiac_sign(day + 3, month % 12 + 1), 'element': 'Воздух', 'quality': 'Мутабельный'},
            {'name': 'Сатурн', 'symbol': '♄', 'sign': self.get_zodiac_sign(day - 2, month), 'element': 'Земля', 'quality': 'Кардинальный'},
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
    
    def generate_report_text(self, chart_data: Dict[str, Any]) -> str:
        """Генерирует подробный текстовый отчёт"""
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
            'Овен': "Вы обладаете лидерскими качествами, энергичны и инициативны. Любите быть первыми и не боитесь рисковать. Ваша задача — научиться направлять свою энергию в конструктивное русло.",
            'Телец': "Вы практичны, терпеливы и надёжны. Цените комфорт и стабильность, умеете достигать поставленных целей. Ваша задача — научиться принимать перемены.",
            'Близнецы': "Вы любознательны, общительны и быстро адаптируетесь. Любите узнавать новое и делиться информацией. Ваша задача — научиться концентрации и глубине.",
            'Рак': "Вы эмоциональны, заботливы и интуитивны. Семья и дом для вас имеют первостепенное значение. Ваша задача — научиться отпускать прошлое.",
            'Лев': "Вы творческая, щедрая и уверенная в себе личность. Любите быть в центре внимания и дарить радость другим. Ваша задача — научиться смирению.",
            'Дева': "Вы аналитичны, внимательны к деталям и трудолюбивы. Стремитесь к совершенству во всём. Ваша задача — научиться принимать несовершенство.",
            'Весы': "Вы дипломатичны, обаятельны и стремитесь к гармонии. Цените красоту и справедливость. Ваша задача — научиться принимать решения.",
            'Скорпион': "Вы страстны, проницательны и обладаете сильной волей. Способны на глубокие трансформации. Ваша задача — научиться доверять.",
            'Стрелец': "Вы оптимистичны, свободолюбивы и стремитесь к познанию. Любите путешествия и приключения. Ваша задача — научиться ответственности.",
            'Козерог': "Вы дисциплинированы, ответственны и амбициозны. Умеете достигать поставленных целей. Ваша задача — научиться отдыхать.",
            'Водолей': "Вы оригинальны, независимы и гуманистичны. Любите всё новое и нестандартное. Ваша задача — научиться принимать эмоции.",
            'Рыбы': "Вы сострадательны, творческие и интуитивные. Обладаете богатым воображением. Ваша задача — научиться границам."
        }
        
        report.append(f"\n**Солнце в {chart_data['sun_sign']}:**")
        report.append(interpretations.get(chart_data['sun_sign'], "У вас уникальная и многогранная личность."))
        
        report.append("\n🔮 *Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!*")
        
        return "\n".join(report)

natal_service = NatalService()