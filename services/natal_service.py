import logging
import uuid
import os
import httpx
import math
import json
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
                    
                    # ========== ДИАГНОСТИКА ==========
                    print(f"\n🔍 ОТВЕТ ДЛЯ {planet_name}:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    # =================================
                    
                    # Пробуем извлечь долготу (координату планеты)
                    longitude = None
                    # Возможные названия поля в ответе VedAstro
                    for key in ['Longitude', 'EclipticLongitude', 'Position', 'Degrees', 'longitude', 'lon']:
                        if key in data:
                            longitude = data[key]
                            break
                    # Если нет прямого поля, ищем во вложенных объектах
                    if longitude is None:
                        if 'Position' in data and isinstance(data['Position'], dict):
                            longitude = data['Position'].get('Longitude')
                        elif 'Ecliptic' in data and isinstance(data['Ecliptic'], dict):
                            longitude = data['Ecliptic'].get('Longitude')
                    
                    if longitude is None:
                        print(f"⚠️ Не найдена долгота для {planet_name}, ответ: {data}")
                        longitude = 0.0
                    
                    # Преобразуем в градусы и минуты
                    if isinstance(longitude, (int, float)):
                        degree = int(longitude)
                        minute_deg = int((longitude % 1) * 60)
                    else:
                        degree = 0
                        minute_deg = 0
                    
                    # Знак и дом
                    sign = data.get('Sign', {}).get('Name', 'Неизвестно')
                    house = data.get('House', '?')
                    retrograde = data.get('Retrograde', False)
                    
                    return {
                        'sign': sign,
                        'house': str(house),
                        'retrograde': retrograde,
                        'degree': degree,
                        'minute': minute_deg,
                        'longitude': longitude,
                    }
                else:
                    print(f"❌ Ошибка {response.status_code} для {planet_name}")
                    return None
        except Exception as e:
            print(f"❌ Исключение для {planet_name}: {e}")
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
                    'name': rus_name,
                    'symbol': symbol,
                    'sign': data['sign'],
                    'house': data['house'],
                    'retrograde': data['retrograde'],
                    'degree': data['degree'],
                    'minute': data['minute'],
                    'longitude': data['longitude']
                })
            else:
                # fallback
                demo_sign = self._get_demo_sign(eng_name, year, month, day)
                planets_data.append({
                    'name': rus_name,
                    'symbol': symbol,
                    'sign': demo_sign,
                    'house': str((hash(f"{eng_name}{birth_date}") % 12) + 1),
                    'retrograde': False,
                    'degree': 0,
                    'minute': 0,
                    'longitude': 0.0
                })
        
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
        
        aspects = self._calculate_aspects(planets_data)
        
        return {
            'sun_sign': sun_sign,
            'element': elements.get(sun_sign, 'Неизвестно'),
            'quality': qualities.get(sun_sign, 'Неизвестно'),
            'ascendant': houses[0]['sign'],
            'planets': planets_data,
            'houses': houses,
            'aspects': aspects,
            'birth_info': {
                'name': name,
                'date': birth_date,
                'time': f"{hour:02d}:{minute:02d}",
                'place': place_clean
            }
        }
    
    def _calculate_aspects(self, planets: List[Dict]) -> List[Dict]:
        aspects = []
        aspect_types = {
            0:   ("☌", "соединение", "#FFD700", 8),
            60:  ("⚹", "секстиль", "#34D399", 6),
            90:  ("□", "квадратура", "#EF4444", 7),
            120: ("△", "трин", "#60A5FA", 8),
            180: ("☍", "оппозиция", "#F472B6", 10)
        }
        for i in range(len(planets)):
            for j in range(i+1, len(planets)):
                lon1 = planets[i].get('longitude', 0.0)
                lon2 = planets[j].get('longitude', 0.0)
                diff = abs(lon1 - lon2)
                diff = min(diff, 360 - diff)
                for angle, (symbol, name, color, orbis) in aspect_types.items():
                    if abs(diff - angle) <= orbis:
                        aspects.append({
                            'planet1': planets[i]['symbol'],
                            'planet2': planets[j]['symbol'],
                            'aspect': symbol,
                            'name': name,
                            'color': color,
                            'angle': angle,
                            'orbis': round(abs(diff - angle), 1)
                        })
                        break
        return aspects
    
    def _get_demo_sign(self, planet: str, year: int, month: int, day: int) -> str:
        signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        import hashlib
        seed = int(hashlib.md5(f"{planet}{year}{month}{day}".encode()).hexdigest()[:8], 16)
        return signs[seed % 12]
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        # Упрощённая версия, можно оставить как есть
        try:
            filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            info = chart_data['birth_info']
            svg = f'''<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
<rect width="800" height="800" fill="#1a2a3a"/>
<circle cx="400" cy="400" r="350" fill="none" stroke="#c9a959" stroke-width="3"/>
<text x="400" y="65" text-anchor="middle" fill="#c9a959" font-size="22">Натальная карта</text>
<text x="400" y="100" text-anchor="middle" fill="#c9a959" font-size="16">{info['name']}</text>
<text x="400" y="750" text-anchor="middle" fill="#c9a959" font-size="12">{info['date']} {info['time']} {info['place']}</text>
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
        if chart_data.get('aspects'):
            report.append("\n⚡ **АСПЕКТЫ МЕЖДУ ПЛАНЕТАМИ**")
            for asp in chart_data['aspects'][:15]:
                report.append(f"• {asp['planet1']} {asp['aspect']} {asp['planet2']} — {asp['name']} ({asp['angle']}°, орбис {asp['orbis']}°)")
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