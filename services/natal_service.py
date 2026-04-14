import logging
import uuid
import os
import httpx
import math
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

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
    
    VEDASTRO_API_KEY = os.environ.get('VEDASTRO_API_KEY', '')
    VEDASTRO_BASE_URL = "https://vedastro.org/api/Calculate"
    
    def __init__(self):
        logger.info("✅ VedAstro сервис инициализирован")
    
    def get_coordinates(self, place: str) -> Tuple[float, float, str]:
        place_lower = place.lower().strip()
        for city, (lat, lon, tz) in self.CITY_COORDS.items():
            if city in place_lower or place_lower in city:
                logger.info(f"📍 Найден город: {city}, координаты: {lat}, {lon}, tz: {tz}")
                return lat, lon, tz
        logger.warning(f"⚠️ Город '{place}' не найден, использую Москву")
        return 55.7558, 37.6173, '+03:00'
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
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
        try:
            if not time_str or time_str == '/skip':
                return True, (12, 0)
            hour, minute = map(int, time_str.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return True, (hour, minute)
            return False, None
        except:
            return False, None
    
    async def _fetch_planet_data(self, planet_name: str, lat: float, lon: float, 
                                   year: int, month: int, day: int, 
                                   hour: int, minute: int, tz: str) -> Optional[Dict]:
        try:
            url = f"{self.VEDASTRO_BASE_URL}/PlanetName/{planet_name}/Location/UserCity/Time/{hour:02d}:{minute:02d}/{day:02d}/{month:02d}/{year}/{tz}"
            headers = {"X-API-Key": self.VEDASTRO_API_KEY}
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"❌ Ошибка {response.status_code} для {planet_name}")
                    return None
        except Exception as e:
            logger.error(f"❌ Исключение для {planet_name}: {e}")
            return None
    
    async def create_natal_chart(self, name: str, birth_date: str, birth_time: str, birth_place: str) -> Dict[str, Any]:
        logger.info(f"🔮 Создание натальной карты для {name}")
        
        valid, date_parts = self.validate_date(birth_date)
        if not valid:
            raise ValueError("Неверная дата рождения")
        valid, time_parts = self.validate_time(birth_time)
        if not valid:
            raise ValueError("Неверное время рождения")
        
        year, month, day = date_parts
        hour, minute = time_parts if time_parts else (12, 0)
        lat, lon, tz = self.get_coordinates(birth_place)
        
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
                sign = data.get('Sign', {}).get('Name', 'Неизвестно')
                house = str(data.get('House', '?'))
                retrograde = data.get('Retrograde', False)
                degree = data.get('Degree', 0)
                minute_deg = data.get('Minute', 0)
            else:
                sign = self._get_demo_sign(eng_name, year, month, day)
                house = str((hash(f"{eng_name}{birth_date}") % 12) + 1)
                retrograde = False
                degree = 0
                minute_deg = 0
            
            planets_data.append({
                'name': rus_name, 'symbol': symbol, 'sign': sign, 'house': house,
                'retrograde': retrograde, 'degree': degree, 'minute': minute_deg
            })
        
        sun_sign = planets_data[0]['sign']
        elements = {'Овен': 'Огонь', 'Лев': 'Огонь', 'Стрелец': 'Огонь', 'Телец': 'Земля',
                    'Дева': 'Земля', 'Козерог': 'Земля', 'Близнецы': 'Воздух', 'Весы': 'Воздух',
                    'Водолей': 'Воздух', 'Рак': 'Вода', 'Скорпион': 'Вода', 'Рыбы': 'Вода'}
        qualities = {'Овен': 'Кардинальный', 'Рак': 'Кардинальный', 'Весы': 'Кардинальный',
                     'Козерог': 'Кардинальный', 'Телец': 'Фиксированный', 'Лев': 'Фиксированный',
                     'Скорпион': 'Фиксированный', 'Водолей': 'Фиксированный', 'Близнецы': 'Мутабельный',
                     'Дева': 'Мутабельный', 'Стрелец': 'Мутабельный', 'Рыбы': 'Мутабельный'}
        
        signs_order = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        sun_index = signs_order.index(sun_sign) if sun_sign in signs_order else 0
        houses = [{'number': i+1, 'sign': signs_order[(sun_index + i) % 12]} for i in range(12)]
        
        # Аспекты между планетами
        aspects = self._calculate_aspects(planets_data)
        
        return {
            'sun_sign': sun_sign, 'element': elements.get(sun_sign, 'Неизвестно'),
            'quality': qualities.get(sun_sign, 'Неизвестно'), 'ascendant': houses[0]['sign'],
            'planets': planets_data, 'houses': houses, 'aspects': aspects,
            'birth_info': {'name': name, 'date': birth_date, 'time': f"{hour:02d}:{minute:02d}", 'place': birth_place}
        }
    
    def _calculate_aspects(self, planets: List[Dict]) -> List[Dict]:
        """Рассчитывает аспекты между планетами"""
        aspects = []
        aspect_types = {
            0: ("☌", "соединение", "#FFD700"),
            60: ("⚹", "секстиль", "#34D399"),
            90: ("□", "квадратура", "#EF4444"),
            120: ("△", "трин", "#60A5FA"),
            180: ("☍", "оппозиция", "#F472B6")
        }
        
        for i in range(len(planets)):
            for j in range(i+1, len(planets)):
                diff = abs(planets[i].get('degree', 0) - planets[j].get('degree', 0))
                for angle, (symbol, name, color) in aspect_types.items():
                    if abs(diff - angle) < 6 or abs(diff - 360 + angle) < 6:
                        aspects.append({
                            'planet1': planets[i]['symbol'], 'planet2': planets[j]['symbol'],
                            'aspect': symbol, 'name': name, 'color': color, 'angle': angle
                        })
                        break
        return aspects
    
    def _get_demo_sign(self, planet: str, year: int, month: int, day: int) -> str:
        signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        import hashlib
        seed = int(hashlib.md5(f"{planet}{year}{month}{day}".encode()).hexdigest()[:8], 16)
        return signs[seed % 12]
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Генерирует красивое SVG-изображение натальной карты"""
        try:
            filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            info = chart_data['birth_info']
            bg_color, circle_color, text_color, accent_color = "#0D1117", "#8B5CF6", "#E5E7EB", "#F59E0B"
            planet_colors = {"☉": "#FBBF24", "☽": "#E5E7EB", "☿": "#34D399", "♀": "#F472B6",
                            "♂": "#EF4444", "♃": "#60A5FA", "♄": "#A78BFA", "⛢": "#2DD4BF", "♆": "#3B82F6", "♇": "#EC4899"}
            
            planet_positions = []
            for i, planet in enumerate(chart_data['planets']):
                sign_index = self._get_sign_index(planet['sign'])
                house_num = int(planet['house']) if planet['house'].isdigit() else 1
                angle = (sign_index * 30 + house_num * 5) % 360
                rad = math.radians(angle - 90)
                radius = 240
                x = 500 + radius * math.cos(rad)
                y = 500 + radius * math.sin(rad)
                planet_positions.append((x, y, planet['symbol'], planet['name'], planet['sign'], planet['house']))
            
            svg = f'''<svg width="1000" height="1000" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#1F2937"/><stop offset="100%" stop-color="#0D1117"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
    </defs>
    <rect width="1000" height="1000" fill="url(#bgGrad)"/>
    <g fill="#FFFFFF" opacity="0.3">
        <circle cx="100" cy="150" r="1.5"/><circle cx="850" cy="80" r="1"/>
        <circle cx="920" cy="450" r="1.5"/><circle cx="50" cy="700" r="1"/>
        <circle cx="200" cy="900" r="1.5"/><circle cx="800" cy="850" r="1"/>
        <circle cx="750" cy="200" r="1.5"/><circle cx="150" cy="400" r="1"/>
    </g>
    <text x="500" y="45" text-anchor="middle" fill="{accent_color}" font-size="28" font-weight="bold" font-family="Georgia, serif">✨ НАТАЛЬНАЯ КАРТА ✨</text>
    <text x="500" y="75" text-anchor="middle" fill="{text_color}" font-size="16" font-family="Arial, sans-serif">{info['name']}</text>
    <text x="500" y="100" text-anchor="middle" fill="{circle_color}" font-size="12" font-family="Arial, sans-serif">{info['date']} в {info['time']}, {info['place']}</text>
    <circle cx="500" cy="500" r="420" fill="none" stroke="{circle_color}" stroke-width="3" opacity="0.8"/>
    <circle cx="500" cy="500" r="340" fill="none" stroke="{circle_color}" stroke-width="2" opacity="0.6"/>
    <circle cx="500" cy="500" r="260" fill="none" stroke="{circle_color}" stroke-width="1.5" opacity="0.4"/>
    <circle cx="500" cy="500" r="180" fill="none" stroke="{circle_color}" stroke-width="1" opacity="0.3"/>
    <circle cx="500" cy="500" r="100" fill="none" stroke="{circle_color}" stroke-width="1" opacity="0.2"/>
    <line x1="500" y1="80" x2="500" y2="920" stroke="{circle_color}" stroke-width="1" opacity="0.3"/>
    <line x1="80" y1="500" x2="920" y2="500" stroke="{circle_color}" stroke-width="1" opacity="0.3"/>
    <line x1="205" y1="205" x2="795" y2="795" stroke="{circle_color}" stroke-width="1" opacity="0.3"/>
    <line x1="795" y1="205" x2="205" y2="795" stroke="{circle_color}" stroke-width="1" opacity="0.3"/>
    <text x="500" y="115" text-anchor="middle" fill="{accent_color}" font-size="28">♈</text>
    <text x="885" y="515" text-anchor="middle" fill="{accent_color}" font-size="28">♉</text>
    <text x="500" y="915" text-anchor="middle" fill="{accent_color}" font-size="28">♊</text>
    <text x="115" y="515" text-anchor="middle" fill="{accent_color}" font-size="28">♋</text>
    <text x="775" y="225" text-anchor="middle" fill="{accent_color}" font-size="28">♌</text>
    <text x="225" y="775" text-anchor="middle" fill="{accent_color}" font-size="28">♍</text>
    <text x="225" y="225" text-anchor="middle" fill="{accent_color}" font-size="28">♎</text>
    <text x="775" y="775" text-anchor="middle" fill="{accent_color}" font-size="28">♏</text>
    <g fill="{text_color}" font-size="14" font-weight="bold">
        <text x="500" y="145" text-anchor="middle">10</text><text x="860" y="500" text-anchor="middle">11</text>
        <text x="500" y="895" text-anchor="middle">12</text><text x="140" y="500" text-anchor="middle">9</text>
        <text x="755" y="250" text-anchor="middle">8</text><text x="245" y="750" text-anchor="middle">7</text>
        <text x="245" y="250" text-anchor="middle">6</text><text x="755" y="750" text-anchor="middle">5</text>
        <text x="500" y="170" text-anchor="middle">1</text><text x="835" y="500" text-anchor="middle">2</text>
        <text x="500" y="870" text-anchor="middle">3</text><text x="165" y="500" text-anchor="middle">4</text>
    </g>
    <text x="500" y="210" text-anchor="middle" fill="{accent_color}" font-size="18" font-weight="bold">ASC {chart_data['ascendant']}</text>
    <g filter="url(#glow)">'''
            
            for x, y, symbol, name, sign, house in planet_positions:
                color = planet_colors.get(symbol, text_color)
                svg += f'''
        <circle cx="{x}" cy="{y}" r="18" fill="{bg_color}" stroke="{color}" stroke-width="2"/>
        <text x="{x}" y="{y+6}" text-anchor="middle" fill="{color}" font-size="20">{symbol}</text>
        <text x="{x}" y="{y-12}" text-anchor="middle" fill="{text_color}" font-size="10">{sign}</text>'''
            
            svg += f'''
    </g>
    <g transform="translate(30, 600)">
        <rect x="0" y="0" width="180" height="280" rx="10" fill="#1F2937" opacity="0.9" stroke="#8B5CF6" stroke-width="1"/>
        <text x="90" y="25" text-anchor="middle" fill="{accent_color}" font-size="14" font-weight="bold">Планеты</text>'''
            
            for i, (symbol, name, color) in enumerate([("☉", "Солнце", "#FBBF24"), ("☽", "Луна", "#E5E7EB"),
                ("☿", "Меркурий", "#34D399"), ("♀", "Венера", "#F472B6"), ("♂", "Марс", "#EF4444"),
                ("♃", "Юпитер", "#60A5FA"), ("♄", "Сатурн", "#A78BFA"), ("⛢", "Уран", "#2DD4BF"),
                ("♆", "Нептун", "#3B82F6"), ("♇", "Плутон", "#EC4899")]):
                svg += f'''
        <text x="15" y="{45 + i*22}" fill="{color}" font-size="18">{symbol}</text>
        <text x="40" y="{50 + i*22}" fill="{text_color}" font-size="12">{name}</text>'''
            
            svg += f'''
        <text x="90" y="270" text-anchor="middle" fill="{text_color}" font-size="10">☉ в {chart_data['sun_sign']}</text>
    </g>
    <g transform="translate(790, 600)">
        <rect x="0" y="0" width="180" height="280" rx="10" fill="#1F2937" opacity="0.9" stroke="#8B5CF6" stroke-width="1"/>
        <text x="90" y="25" text-anchor="middle" fill="{accent_color}" font-size="14" font-weight="bold">Характеристики</text>
        <text x="15" y="55" fill="{text_color}" font-size="12">Стихия: {chart_data['element']}</text>
        <text x="15" y="80" fill="{text_color}" font-size="12">Качество: {chart_data['quality']}</text>
        <text x="15" y="105" fill="{text_color}" font-size="12">Асцендент: {chart_data['ascendant']}</text>'''
            
            retro_planets = [p['name'] for p in chart_data['planets'] if p.get('retrograde')]
            if retro_planets:
                svg += f'''
        <text x="15" y="140" fill="#EF4444" font-size="12">Ретроградные:</text>
        <text x="15" y="160" fill="{text_color}" font-size="11">{', '.join(retro_planets[:4])}</text>'''
            
            if chart_data.get('aspects'):
                svg += f'''
        <text x="15" y="200" fill="{accent_color}" font-size="12">Аспекты:</text>'''
                for i, asp in enumerate(chart_data['aspects'][:3]):
                    svg += f'''
        <text x="15" y="{220 + i*15}" fill="{asp['color']}" font-size="11">{asp['planet1']}{asp['aspect']}{asp['planet2']} ({asp['name']})</text>'''
            
            svg += f'''
        <text x="90" y="275" text-anchor="middle" fill="{accent_color}" font-size="10">✨ AstroBot ✨</text>
    </g>
</svg>'''
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(svg)
            return filename
        except Exception as e:
            logger.error(f"❌ Ошибка SVG: {e}")
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
        
        if chart_data.get('aspects'):
            report.append("\n⚡ **АСПЕКТЫ МЕЖДУ ПЛАНЕТАМИ**")
            for asp in chart_data['aspects'][:10]:
                report.append(f"• {asp['planet1']} {asp['aspect']} {asp['planet2']} — {asp['name']} ({asp['angle']}°)")
        
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
    
    def _get_sign_index(self, sign: str) -> int:
        signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        try:
            return signs.index(sign)
        except ValueError:
            return 0

natal_service = NatalService()