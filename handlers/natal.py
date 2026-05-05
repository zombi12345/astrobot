import logging
import uuid
import os
import httpx
import math
import random
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from astrology_calculator import AstrologyCalculator

logger = logging.getLogger(__name__)

class NatalService:
    CITY_COORDS = {
        'минск': (53.9045, 27.5615, '+03:00'),
        'москва': (55.7558, 37.6173, '+03:00'),
        'киев': (50.4501, 30.5234, '+02:00'),
        'санкт-петербург': (59.9343, 30.3351, '+03:00'),
        'новосибирск': (55.0084, 82.9357, '+07:00'),
        'екатеринбург': (56.8389, 60.6057, '+05:00'),
        'казань': (55.7887, 49.1221, '+03:00'),
        'самара': (53.1959, 50.1002, '+04:00'),
        'омск': (54.9885, 73.3242, '+06:00'),
        'челябинск': (55.1644, 61.4368, '+05:00'),
        'ростов-на-дону': (47.2357, 39.7015, '+03:00'),
        'уфа': (54.7388, 55.9721, '+05:00'),
        'волгоград': (48.708, 44.5133, '+03:00'),
        'пермь': (58.0105, 56.2294, '+05:00'),
        'красноярск': (56.0097, 92.7917, '+07:00'),
        'воронеж': (51.6605, 39.2003, '+03:00'),
        'варшава': (52.2297, 21.0122, '+01:00'),
        'вильнюс': (54.6872, 25.2797, '+02:00'),
        'рига': (56.9496, 24.1052, '+02:00'),
        'таллин': (59.437, 24.7536, '+02:00'),
        'берлин': (52.52, 13.405, '+01:00'),
        'париж': (48.8566, 2.3522, '+01:00'),
        'лондон': (51.5074, -0.1278, '+00:00'),
    }
    
    VEDASTRO_API_KEY = "sk_live_0YZ5mUocBiDoQ7vXVmgZM5mlBtEnO8Dwov11Ytvc"
    VEDASTRO_BASE_URL = "https://vedastro.org/api/Calculate"
    
    def __init__(self):
        logger.info("✅ VedAstro сервис инициализирован (HTTP-версия)")
    
    def get_coordinates(self, place: str) -> Tuple[float, float, str]:
        place_lower = place.lower().strip()
        for city, (lat, lon, tz) in self.CITY_COORDS.items():
            if city in place_lower or place_lower in city:
                return lat, lon, tz
        words = place_lower.split()
        for word in words:
            for city, (lat, lon, tz) in self.CITY_COORDS.items():
                if city in word or word in city:
                    return lat, lon, tz
        return 55.7558, 37.6173, '+03:00'
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[Tuple[int, int, int]], str]:
        try:
            year, month, day = map(int, date_str.split('-'))
            birth_date = datetime(year, month, day)
            if birth_date > datetime.now():
                return False, None, "Дата рождения не может быть в будущем"
            age = (datetime.now() - birth_date).days / 365.25
            if age > 120:
                return False, None, "Возраст не может быть больше 120 лет"
            return True, (year, month, day), ""
        except:
            return False, None, "Неверный формат даты. Используйте ГГГГ-ММ-ДД"
    
    def validate_time(self, time_str: str) -> Tuple[bool, Optional[Tuple[int, int]], str]:
        try:
            if not time_str or time_str.lower() == '/skip':
                return True, (12, 0), ""
            hour, minute = map(int, time_str.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return True, (hour, minute), ""
            return False, None, "Часы от 0 до 23, минуты от 0 до 59"
        except:
            return False, None, "Неверный формат времени. Используйте ЧЧ:ММ"
    
    def validate_place(self, place: str) -> Tuple[bool, str, str]:
        if not place or not place.strip():
            return False, "", "Место рождения не может быть пустым"
        cleaned = place.strip()
        if len(cleaned) < 2:
            return False, "", "Название места слишком короткое"
        return True, cleaned, ""
    
    async def _fetch_planet_data(self, planet_name: str, lat: float, lon: float,
                                   year: int, month: int, day: int,
                                   hour: int, minute: int, tz: str) -> Optional[Dict]:
        try:
            url = f"{self.VEDASTRO_BASE_URL}/PlanetName/{planet_name}/Location/UserCity/Time/{hour:02d}:{minute:02d}/{day:02d}/{month:02d}/{year}/{tz}"
            headers = {"X-API-Key": self.VEDASTRO_API_KEY}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'sign': data.get('Sign', {}).get('Name', 'Неизвестно'),
                        'house': data.get('House', '?'),
                        'retrograde': data.get('Retrograde', False),
                    }
                else:
                    return None
        except Exception as e:
            logger.error(f"Ошибка {planet_name}: {e}")
            return None
    
    async def create_natal_chart(self, name: str, birth_date: str, birth_time: str, birth_place: str) -> Dict[str, Any]:
        logger.info(f"🔮 Создание натальной карты для {name}")
        valid_date, date_parts, date_err = self.validate_date(birth_date)
        if not valid_date:
            raise ValueError(date_err)
        valid_time, time_parts, time_err = self.validate_time(birth_time)
        if not valid_time:
            raise ValueError(time_err)
        valid_place, place_clean, place_err = self.validate_place(birth_place)
        if not valid_place:
            raise ValueError(place_err)
        year, month, day = date_parts
        hour, minute = time_parts if time_parts else (12, 0)
        lat, lon, tz = self.get_coordinates(place_clean)
        
        planets_to_fetch = [
            ("Sun", "Солнце", "☉"), ("Moon", "Луна", "☽"), ("Mercury", "Меркурий", "☿"),
            ("Venus", "Венера", "♀"), ("Mars", "Марс", "♂"), ("Jupiter", "Юпитер", "♃"),
            ("Saturn", "Сатурн", "♄"), ("Uranus", "Уран", "⛢"), ("Neptune", "Нептун", "♆"),
            ("Pluto", "Плутон", "♇")
        ]
        planets_data = []
        for eng_name, rus_name, symbol in planets_to_fetch:
            data = await self._fetch_planet_data(eng_name, lat, lon, year, month, day, hour, minute, tz)
            if data:
                planets_data.append({
                    'name': rus_name, 'symbol': symbol, 'sign': data['sign'],
                    'house': str(data['house']), 'retrograde': data['retrograde'],
                })
            else:
                planets_data.append({
                    'name': rus_name, 'symbol': symbol, 'sign': "Неизвестно",
                    'house': "?", 'retrograde': False,
                })
        
        # Исправление знака Солнца по локальному алгоритму (тропический зодиак)
        birth_date_obj = datetime(year, month, day)
        local_sun_sign = AstrologyCalculator.get_zodiac_sign(birth_date_obj)
        if planets_data and planets_data[0]['sign'] != local_sun_sign:
            planets_data[0]['sign'] = local_sun_sign
        
        sun_sign = planets_data[0]['sign']
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
        signs_order = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        sun_index = signs_order.index(sun_sign) if sun_sign in signs_order else 0
        houses = [{'number': i+1, 'sign': signs_order[(sun_index + i) % 12]} for i in range(12)]
        
        return {
            'sun_sign': sun_sign,
            'element': elements.get(sun_sign, 'Неизвестно'),
            'quality': qualities.get(sun_sign, 'Неизвестно'),
            'ascendant': houses[0]['sign'],
            'planets': planets_data,
            'houses': houses,
            'birth_info': {'name': name, 'date': birth_date, 'time': f"{hour:02d}:{minute:02d}", 'place': place_clean}
        }
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Красивая SVG-схема натальной карты (исправленная версия)"""
        try:
            filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            info = chart_data['birth_info']
            asc = chart_data['ascendant']
            sun_sign = chart_data['sun_sign']
            planets = chart_data['planets']
            houses = chart_data['houses']
            
            signs_ru = ['Овен','Телец','Близнецы','Рак','Лев','Дева','Весы','Скорпион','Стрелец','Козерог','Водолей','Рыбы']
            signs_sym = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
            
            # Позиции планет
            planet_positions = []
            for p in planets:
                try:
                    sign_idx = signs_ru.index(p['sign'])
                except:
                    sign_idx = 0
                angle = (sign_idx * 30 + int(p['house']) * 5) % 360 if p['house'].isdigit() else sign_idx * 30
                rad = math.radians(angle - 90)
                radius = 240
                x = 400 + radius * math.cos(rad)
                y = 400 + radius * math.sin(rad)
                planet_positions.append((x, y, p['symbol'], p['name']))
            
            # Построение SVG
            svg = []
            svg.append('<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">')
            svg.append('<defs>')
            svg.append('<radialGradient id="bgGrad" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#1F2937"/><stop offset="100%" stop-color="#0D1117"/></radialGradient>')
            svg.append('<filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
            svg.append('</defs>')
            svg.append('<rect width="800" height="800" fill="url(#bgGrad)"/>')
            
            # Звёзды
            random.seed(hash(info['name']))
            for _ in range(80):
                x = random.randint(20, 780)
                y = random.randint(20, 780)
                svg.append(f'<circle cx="{x}" cy="{y}" r="1.5" fill="#FFFFFF" opacity="0.4"/>')
            random.seed()
            
            # Круги
            for r, sw in [(350,3), (280,2), (200,1.5), (100,1)]:
                svg.append(f'<circle cx="400" cy="400" r="{r}" fill="none" stroke="#8B5CF6" stroke-width="{sw}" opacity="0.8"/>')
            
            # Линии домов
            for angle in range(0, 360, 30):
                rad = math.radians(angle - 90)
                x2 = 400 + 350 * math.cos(rad)
                y2 = 400 + 350 * math.sin(rad)
                svg.append(f'<line x1="400" y1="400" x2="{x2}" y2="{y2}" stroke="#8B5CF6" stroke-width="1" opacity="0.3"/>')
            
            # Знаки зодиака
            for i, sym in enumerate(signs_sym):
                angle = (i * 30) - 90
                rad = math.radians(angle)
                r = 310
                x = 400 + r * math.cos(rad)
                y = 400 + r * math.sin(rad) + 8
                svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="#F59E0B" font-size="24" font-family="Arial, sans-serif">{sym}</text>')
            
            # Номера домов
            for i in range(1, 13):
                angle = (i * 30) - 90 + 15
                rad = math.radians(angle)
                r = 370
                x = 400 + r * math.cos(rad)
                y = 400 + r * math.sin(rad) + 5
                svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="#E5E7EB" font-size="14" font-weight="bold">{i}</text>')
            
            # Планеты
            for x, y, sym, name in planet_positions:
                svg.append(f'<circle cx="{x}" cy="{y}" r="18" fill="#0D1117" stroke="#FBBF24" stroke-width="2" filter="url(#glow)"/>')
                svg.append(f'<text x="{x}" y="{y+6}" text-anchor="middle" fill="#FBBF24" font-size="20" font-family="Arial, sans-serif">{sym}</text>')
                svg.append(f'<text x="{x}" y="{y-14}" text-anchor="middle" fill="#E5E7EB" font-size="9">{name[0]}</text>')
            
            # Заголовки
            svg.append(f'<text x="400" y="45" text-anchor="middle" fill="#F59E0B" font-size="24" font-weight="bold" font-family="Georgia, serif">✨ Натальная карта ✨</text>')
            svg.append(f'<text x="400" y="75" text-anchor="middle" fill="#E5E7EB" font-size="16" font-family="Arial, sans-serif">{info["name"]}</text>')
            svg.append(f'<text x="400" y="100" text-anchor="middle" fill="#8B5CF6" font-size="12" font-family="Arial, sans-serif">{info["date"]} {info["time"]} | {info["place"]}</text>')
            svg.append(f'<text x="400" y="760" text-anchor="middle" fill="#F59E0B" font-size="14" font-family="Arial, sans-serif">⬆ ASC {asc}</text>')
            
            # Легенда
            svg.append('<g transform="translate(620, 580)">')
            svg.append('<rect x="0" y="0" width="150" height="150" rx="8" fill="#1F2937" opacity="0.9" stroke="#8B5CF6" stroke-width="1"/>')
            svg.append('<text x="75" y="20" text-anchor="middle" fill="#F59E0B" font-size="12" font-weight="bold">Солнце</text>')
            svg.append(f'<text x="75" y="45" text-anchor="middle" fill="#E5E7EB" font-size="11">{sun_sign}</text>')
            svg.append('<text x="75" y="70" text-anchor="middle" fill="#F59E0B" font-size="12" font-weight="bold">Асцендент</text>')
            svg.append(f'<text x="75" y="95" text-anchor="middle" fill="#E5E7EB" font-size="11">{asc}</text>')
            svg.append('</g>')
            
            svg.append('</svg>')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(''.join(svg))
            return filename
        except Exception as e:
            logger.error(f"Ошибка SVG: {e}")
            return None
    
    def generate_report_text(self, chart_data: Dict[str, Any]) -> str:
        report = []
        report.append("🌟 **НАТАЛЬНАЯ КАРТА**")
        report.append(f"👤 {chart_data['birth_info']['name']}")
        report.append(f"📅 {chart_data['birth_info']['date']} в {chart_data['birth_info']['time']}")
        report.append(f"📍 {chart_data['birth_info']['place']}\n")
        report.append("✨ **ОСНОВНЫЕ ХАРАКТЕРИСТИКИ**")
        report.append(f"• Солнце в знаке: {chart_data['sun_sign']}")
        report.append(f"• Стихия: {chart_data['element']}")
        report.append(f"• Качество: {chart_data['quality']}")
        report.append(f"• Асцендент (ASC): {chart_data['ascendant']}\n")
        report.append("🔮 **ПОЛОЖЕНИЕ ПЛАНЕТ**")
        for p in chart_data['planets']:
            retro = " (ретроградный)" if p.get('retrograde') else ""
            report.append(f"• {p['symbol']} {p['name']} в знаке {p['sign']} ({p['house']} дом){retro}")
        report.append("\n🏠 **АСТРОЛОГИЧЕСКИЕ ДОМА**")
        for h in chart_data['houses']:
            report.append(f"• {h['number']} дом: {h['sign']}")
        interpretations = {
            'Овен': 'Вы обладаете лидерскими качествами, энергичны и инициативны.',
            'Телец': 'Вы практичны, терпеливы и надёжны.',
            'Близнецы': 'Вы любознательны, общительны и быстро адаптируетесь.',
            'Рак': 'Вы эмоциональны, заботливы и интуитивны.',
            'Лев': 'Вы творческая, щедрая и уверенная в себе личность.',
            'Дева': 'Вы аналитичны, внимательны к деталям и трудолюбивы.',
            'Весы': 'Вы дипломатичны, обаятельны и стремитесь к гармонии.',
            'Скорпион': 'Вы страстны, проницательны и обладаете сильной волей.',
            'Стрелец': 'Вы оптимистичны, свободолюбивы и стремитесь к познанию.',
            'Козерог': 'Вы дисциплинированы, ответственны и амбициозны.',
            'Водолей': 'Вы оригинальны, независимы и гуманистичны.',
            'Рыбы': 'Вы сострадательны, творческие и интуитивные.'
        }
        report.append(f"\n**☉ Солнце в {chart_data['sun_sign']}:** {interpretations.get(chart_data['sun_sign'], 'у вас уникальная личность.')}")
        report.append("\n🔮 *Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!*")
        return "\n".join(report)

natal_service = NatalService()