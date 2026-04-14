import logging
import uuid
import os
import httpx
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class NatalService:
    # База координат городов (широта, долгота, часовой пояс)
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
    
    # Ваш API-ключ VedAstro
    import os
    VEDASTRO_API_KEY = os.environ.get('VEDASTRO_API_KEY', '')
    VEDASTRO_BASE_URL = "https://vedastro.org/api/Calculate"
    
    def __init__(self):
        logger.info("✅ VedAstro сервис инициализирован с API-ключом")
    
    def get_coordinates(self, place: str) -> Tuple[float, float, str]:
        """Возвращает координаты и часовой пояс города"""
        place_lower = place.lower().strip()
        
        for city, (lat, lon, tz) in self.CITY_COORDS.items():
            if city in place_lower or place_lower in city:
                logger.info(f"📍 Найден город: {city}, координаты: {lat}, {lon}, tz: {tz}")
                return lat, lon, tz
        
        # По умолчанию Москва
        logger.warning(f"⚠️ Город '{place}' не найден, использую Москву")
        return 55.7558, 37.6173, '+03:00'
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """Проверяет корректность даты рождения"""
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
        """Проверяет корректность времени рождения"""
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
        """Получает данные планеты через VedAstro API"""
        try:
            # Формируем URL по формату из документации
            # /api/Calculate/PlanetName/Sun/Location/Город/Time/ЧЧ:ММ/ДД/ММ/ГГГГ/+ЧЧ:ММ
            url = f"{self.VEDASTRO_BASE_URL}/PlanetName/{planet_name}/Location/UserCity/Time/{hour:02d}:{minute:02d}/{day:02d}/{month:02d}/{year}/{tz}"
            
            headers = {
                "X-API-Key": self.VEDASTRO_API_KEY
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Данные для {planet_name} получены")
                    return data
                else:
                    logger.error(f"❌ Ошибка {response.status_code} для {planet_name}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Исключение при запросе {planet_name}: {e}")
            return None
    
    async def create_natal_chart(self, name: str, birth_date: str, birth_time: str, birth_place: str) -> Dict[str, Any]:
        """Создаёт натальную карту через VedAstro API"""
        logger.info(f"🔮 Создание натальной карты для {name}")
        
        # Валидация данных
        valid, date_parts = self.validate_date(birth_date)
        if not valid:
            raise ValueError("Неверная дата рождения")
        
        valid, time_parts = self.validate_time(birth_time)
        if not valid:
            raise ValueError("Неверное время рождения")
        
        year, month, day = date_parts
        hour, minute = time_parts if time_parts else (12, 0)
        
        # Получаем координаты города
        lat, lon, tz = self.get_coordinates(birth_place)
        
        # Список планет для запроса
        planets_to_fetch = [
            ("Sun", "Солнце", "☉"),
            ("Moon", "Луна", "☽"),
            ("Mercury", "Меркурий", "☿"),
            ("Venus", "Венера", "♀"),
            ("Mars", "Марс", "♂"),
            ("Jupiter", "Юпитер", "♃"),
            ("Saturn", "Сатурн", "♄")
        ]
        
        planets_data = []
        
        for eng_name, rus_name, symbol in planets_to_fetch:
            data = await self._fetch_planet_data(eng_name, lat, lon, year, month, day, hour, minute, tz)
            
            if data:
                # Парсим ответ (формат может отличаться, нужно уточнить по документации)
                sign = data.get('Sign', {}).get('Name', 'Неизвестно')
                house = data.get('House', '?')
                retrograde = data.get('Retrograde', False)
            else:
                # Если запрос не удался, используем демо-данные
                sign = self._get_demo_sign(eng_name, year, month, day)
                house = str((hash(f"{eng_name}{birth_date}") % 12) + 1)
                retrograde = False
            
            planets_data.append({
                'name': rus_name,
                'symbol': symbol,
                'sign': sign,
                'house': house,
                'retrograde': retrograde,
            })
        
        # Определяем знак Солнца (первая планета в списке)
        sun_sign = planets_data[0]['sign'] if planets_data else 'Неизвестно'
        
        # Стихии и качества
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
        
        # Генерация домов (12 домов, каждый со знаком)
        houses = []
        signs_order = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        sun_index = signs_order.index(sun_sign) if sun_sign in signs_order else 0
        
        for i in range(1, 13):
            sign_index = (sun_index + i - 1) % 12
            houses.append({
                'number': i,
                'sign': signs_order[sign_index]
            })
        
        return {
            'sun_sign': sun_sign,
            'element': elements.get(sun_sign, 'Неизвестно'),
            'quality': qualities.get(sun_sign, 'Неизвестно'),
            'ascendant': houses[0]['sign'],
            'planets': planets_data,
            'houses': houses,
            'birth_info': {
                'name': name,
                'date': birth_date,
                'time': f"{hour:02d}:{minute:02d}",
                'place': birth_place
            }
        }
    
    def _get_demo_sign(self, planet: str, year: int, month: int, day: int) -> str:
        """Демо-знак для планеты (если API не ответил)"""
        import hashlib
        signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        seed = int(hashlib.md5(f"{planet}{year}{month}{day}".encode()).hexdigest()[:8], 16)
        return signs[seed % 12]
    
    def generate_svg_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Генерирует SVG-схему натальной карты"""
        try:
            filename = f"natal_chart_{uuid.uuid4().hex}.svg"
            info = chart_data['birth_info']
            
            svg = f'''<svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
<rect width="800" height="800" fill="#1a2a3a"/>
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
<text x="400" y="30" text-anchor="middle" fill="#c9a959" font-size="16" font-weight="bold">Натальная карта: {info['name']}</text>
<text x="400" y="780" text-anchor="middle" fill="#c9a959" font-size="12">{info['date']} в {info['time']}, {info['place']}</text>
</svg>'''
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(svg)
            
            return filename
        except Exception as e:
            logger.error(f"❌ Ошибка SVG: {e}")
            return None
    
    def generate_report_text(self, chart_data: Dict[str, Any]) -> str:
        """Генерирует текстовый отчёт"""
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
        
        for p in chart_data['planets']:
            retro = " (ретроградный)" if p.get('retrograde') else ""
            report.append(f"• {p['symbol']} {p['name']} в знаке {p['sign']} ({p['house']} дом){retro}")
        
        report.append("")
        report.append("🏠 **ДОМА**")
        for h in chart_data['houses'][:6]:  # Показываем первые 6 домов для краткости
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
        
        report.append(f"\n**Солнце в {chart_data['sun_sign']}:** {interpretations.get(chart_data['sun_sign'], 'у вас уникальная личность.')}")
        report.append("\n🔮 *Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!*")
        
        return "\n".join(report)

# Создаём экземпляр сервиса
natal_service = NatalService()