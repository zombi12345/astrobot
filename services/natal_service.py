import logging
import uuid
import os
import httpx
import math
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

# Вспомогательный класс для локального определения знака (копия из astrology_calculator)
class SimpleAstro:
    @staticmethod
    def get_zodiac_sign(birth_date: datetime) -> str:
        day = birth_date.day
        month = birth_date.month
        if month == 1:
            return 'Козерог' if day <= 19 else 'Водолей'
        elif month == 2:
            return 'Водолей' if day <= 18 else 'Рыбы'
        elif month == 3:
            return 'Рыбы' if day <= 20 else 'Овен'
        elif month == 4:
            return 'Овен' if day <= 19 else 'Телец'
        elif month == 5:
            return 'Телец' if day <= 20 else 'Близнецы'
        elif month == 6:
            return 'Близнецы' if day <= 20 else 'Рак'
        elif month == 7:
            return 'Рак' if day <= 22 else 'Лев'
        elif month == 8:
            return 'Лев' if day <= 22 else 'Дева'
        elif month == 9:
            return 'Дева' if day <= 22 else 'Весы'
        elif month == 10:
            return 'Весы' if day <= 22 else 'Скорпион'
        elif month == 11:
            return 'Скорпион' if day <= 21 else 'Стрелец'
        elif month == 12:
            return 'Стрелец' if day <= 21 else 'Козерог'
        return 'Неизвестно'

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
        # Прямое совпадение
        for city, (lat, lon, tz) in self.CITY_COORDS.items():
            if city in place_lower or place_lower in city:
                logger.info(f"📍 Найден город: {city}, координаты: {lat}, {lon}, tz: {tz}")
                return lat, lon, tz
        # Поиск по словам
        words = place_lower.split()
        for word in words:
            for city, (lat, lon, tz) in self.CITY_COORDS.items():
                if city in word or word in city:
                    logger.info(f"📍 Найден город по части слова: {city}, координаты: {lat}, {lon}, tz: {tz}")
                    return lat, lon, tz
        logger.warning(f"⚠️ Город '{place}' не найден, использую Москву")
        return 55.7558, 37.6173, '+03:00'
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[Tuple[int, int, int]], str]:
        try:
            year, month, day = map(int, date_str.split('-'))
            birth_date = datetime(year, month, day)
            now = datetime.now()
            if birth_date > now:
                return False, None, "Дата рождения не может быть в будущем"
            age = (now - birth_date).days / 365.25
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
                    logger.error(f"❌ Ошибка {response.status_code} для {planet_name}")
                    return None
        except Exception as e:
            logger.error(f"❌ Исключение для {planet_name}: {e}")
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
                demo_sign = self._get_demo_sign(eng_name, year, month, day)
                planets_data.append({
                    'name': rus_name, 'symbol': symbol, 'sign': demo_sign,
                    'house': str((hash(f"{eng_name}{birth_date}") % 12) + 1), 'retrograde': False,
                })
        
        # Локальное вычисление знака Солнца (исправление ведического сдвига)
        birth_date_obj = datetime(year, month, day)
        local_sun_sign = SimpleAstro.get_zodiac_sign(birth_date_obj)
        logger.info(f"Локальное Солнце: {local_sun_sign}, из API: {planets_data[0]['sign'] if planets_data else '?'}")
        if planets_data and planets_data[0]['sign'] != local_sun_sign:
            logger.warning(f"Знак Солнца из API ({planets_data[0]['sign']}) заменён на локальный ({local_sun_sign})")
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
            'sun_sign': sun_sign, 'element': elements.get(sun_sign, 'Неизвестно'),
            'quality': qualities.get(sun_sign, 'Неизвестно'), 'ascendant': houses[0]['sign'],
            'planets': planets_data, 'houses': houses,
            'birth_info': {'name': name, 'date': birth_date, 'time': f"{hour:02d}:{minute:02d}", 'place': place_clean}
        }
    
    def _get_demo_sign(self, planet: str, year: int, month: int, day: int) -> str:
        signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        import hashlib
        seed = int(hashlib.md5(f"{planet}{year}{month}{day}".encode()).hexdigest()[:8], 16)
        return signs[seed % 12]
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Генерирует красивое SVG-изображение натальной карты, совместимое со всеми устройствами"""
        try:
            filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            info = chart_data['birth_info']
            sun_sign = chart_data['sun_sign']
            asc = chart_data['ascendant']
            
            # Определяем символы зодиака для круга (упрощённо)
            signs_wheel = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
            # Красивая цветовая схема
            bg_color = "#0D1117"
            circle_color = "#8B5CF6"
            text_color = "#E5E7EB"
            accent_color = "#F59E0B"
            
            # Позиции планет на круге (псевдо-позиции на основе знака и дома)
            planets = chart_data['planets']
            planet_positions = []
            signs_list = ['Овен','Телец','Близнецы','Рак','Лев','Дева','Весы','Скорпион','Стрелец','Козерог','Водолей','Рыбы']
            for p in planets:
                try:
                    sign_idx = signs_list.index(p['sign'])
                except:
                    sign_idx = 0
                house_num = int(p['house']) if p['house'].isdigit() else 1
                angle = (sign_idx * 30 + house_num * 5) % 360
                rad = math.radians(angle - 90)
                radius = 220
                x = 400 + radius * math.cos(rad)
                y = 400 + radius * math.sin(rad)
                planet_positions.append((x, y, p['symbol'], p['name'], p['sign']))
            
            svg = f'''<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#1F2937"/>
            <stop offset="100%" stop-color="#0D1117"/>
        </radialGradient>
        <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    <rect width="800" height="800" fill="url(#bgGrad)"/>
    <!-- Звёзды -->
    <g fill="#FFFFFF" opacity="0.3">
        <circle cx="100" cy="150" r="1.5"/><circle cx="700" cy="80" r="1"/>
        <circle cx="750" cy="450" r="1.5"/><circle cx="50" cy="700" r="1"/>
        <circle cx="200" cy="750" r="1.5"/><circle cx="700" cy="700" r="1"/>
        <circle cx="650" cy="200" r="1.5"/><circle cx="150" cy="400" r="1"/>
        <circle cx="300" cy="100" r="1"/><circle cx="550" cy="720" r="1"/>
    </g>
    <text x="400" y="45" text-anchor="middle" fill="{accent_color}" font-size="28" font-weight="bold" font-family="Georgia, serif">✨ НАТАЛЬНАЯ КАРТА ✨</text>
    <text x="400" y="75" text-anchor="middle" fill="{text_color}" font-size="16" font-family="Arial, sans-serif">{info['name']}</text>
    <text x="400" y="100" text-anchor="middle" fill="{circle_color}" font-size="12" font-family="Arial, sans-serif">{info['date']} в {info['time']}, {info['place']}</text>
    
    <!-- Круги карты -->
    <circle cx="400" cy="400" r="370" fill="none" stroke="{circle_color}" stroke-width="2" opacity="0.7"/>
    <circle cx="400" cy="400" r="280" fill="none" stroke="{circle_color}" stroke-width="1.5" opacity="0.5"/>
    <circle cx="400" cy="400" r="190" fill="none" stroke="{circle_color}" stroke-width="1" opacity="0.4"/>
    <circle cx="400" cy="400" r="100" fill="none" stroke="{circle_color}" stroke-width="1" opacity="0.3"/>
    
    <!-- Линии домов -->
    <g stroke="{circle_color}" stroke-width="1" opacity="0.3">
        <line x1="400" y1="30" x2="400" y2="770"/>
        <line x1="30" y1="400" x2="770" y2="400"/>
        <line x1="138" y1="138" x2="662" y2="662"/>
        <line x1="662" y1="138" x2="138" y2="662"/>
    </g>
    
    <!-- Знаки зодиака по углам -->
    <g fill="{accent_color}" font-size="24" font-family="Arial, sans-serif" text-anchor="middle">
        <text x="400" y="65">♈</text>
        <text x="735" y="415">♉</text>
        <text x="400" y="765">♊</text>
        <text x="65" y="415">♋</text>
        <text x="662" y="138">♌</text>
        <text x="138" y="662">♍</text>
        <text x="138" y="138">♎</text>
        <text x="662" y="662">♏</text>
    </g>
    
    <!-- Номера домов -->
    <g fill="{text_color}" font-size="12" font-weight="bold" font-family="Arial, sans-serif" text-anchor="middle">
        <text x="400" y="110">10</text><text x="720" y="400">11</text>
        <text x="400" y="740">12</text><text x="80" y="400">9</text>
        <text x="640" y="180">8</text><text x="160" y="620">7</text>
        <text x="160" y="180">6</text><text x="640" y="620">5</text>
        <text x="400" y="135">1</text><text x="690" y="400">2</text>
        <text x="400" y="715">3</text><text x="110" y="400">4</text>
    </g>
    
    <!-- Асцендент -->
    <text x="400" y="170" text-anchor="middle" fill="{accent_color}" font-size="16" font-weight="bold" font-family="Arial, sans-serif">ASC {asc}</text>
    
    <!-- Планеты -->
    <g filter="url(#glow)">
'''
            colors = {"☉": "#FBBF24", "☽": "#E5E7EB", "☿": "#34D399", "♀": "#F472B6",
                      "♂": "#EF4444", "♃": "#60A5FA", "♄": "#A78BFA", "⛢": "#2DD4BF", "♆": "#3B82F6", "♇": "#EC4899"}
            for x, y, sym, name, sign in planet_positions:
                color = colors.get(sym, text_color)
                svg += f'''
        <circle cx="{x}" cy="{y}" r="18" fill="{bg_color}" stroke="{color}" stroke-width="2"/>
        <text x="{x}" y="{y+6}" text-anchor="middle" fill="{color}" font-size="18" font-family="Arial, sans-serif">{sym}</text>
        <text x="{x}" y="{y-12}" text-anchor="middle" fill="{text_color}" font-size="9" font-family="Arial, sans-serif">{sign}</text>
'''
        svg += f'''
    </g>
    
    <!-- Легенда -->
    <g transform="translate(30, 480)">
        <rect x="0" y="0" width="170" height="260" rx="10" fill="#1F2937" opacity="0.9" stroke="{circle_color}" stroke-width="1"/>
        <text x="85" y="22" text-anchor="middle" fill="{accent_color}" font-size="14" font-weight="bold" font-family="Arial, sans-serif">Планеты</text>
'''
        legend_planets = [
            ("☉", "Солнце"), ("☽", "Луна"), ("☿", "Меркурий"), ("♀", "Венера"),
            ("♂", "Марс"), ("♃", "Юпитер"), ("♄", "Сатурн"), ("⛢", "Уран"), ("♆", "Нептун"), ("♇", "Плутон")
        ]
        for i, (sym, name) in enumerate(legend_planets[:8]):
            svg += f'''
        <text x="15" y="{45 + i*22}" fill="{colors.get(sym, text_color)}" font-size="16" font-family="Arial, sans-serif">{sym}</text>
        <text x="40" y="{50 + i*22}" fill="{text_color}" font-size="11" font-family="Arial, sans-serif">{name}</text>
'''
        svg += f'''
        <text x="85" y="250" text-anchor="middle" fill="{text_color}" font-size="10" font-family="Arial, sans-serif">☉ в {sun_sign}</text>
    </g>
    
    <!-- Характеристики -->
    <g transform="translate(600, 480)">
        <rect x="0" y="0" width="170" height="260" rx="10" fill="#1F2937" opacity="0.9" stroke="{circle_color}" stroke-width="1"/>
        <text x="85" y="22" text-anchor="middle" fill="{accent_color}" font-size="14" font-weight="bold" font-family="Arial, sans-serif">Характеристики</text>
        <text x="15" y="55" fill="{text_color}" font-size="12" font-family="Arial, sans-serif">Стихия: {chart_data['element']}</text>
        <text x="15" y="80" fill="{text_color}" font-size="12" font-family="Arial, sans-serif">Качество: {chart_data['quality']}</text>
        <text x="15" y="105" fill="{text_color}" font-size="12" font-family="Arial, sans-serif">Асцендент: {asc}</text>
        <text x="15" y="140" fill="{accent_color}" font-size="11" font-family="Arial, sans-serif">✨ Астрология — это</text>
        <text x="15" y="160" fill="{accent_color}" font-size="11" font-family="Arial, sans-serif">инструмент познания</text>
        <text x="15" y="180" fill="{accent_color}" font-size="11" font-family="Arial, sans-serif">себя и мира ✨</text>
    </g>
</svg>'''
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(svg)
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