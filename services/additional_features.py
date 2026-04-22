import logging
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .natal_service import natal_service

logger = logging.getLogger(__name__)

class AdditionalFeatures:
    def __init__(self):
        self.api_key = natal_service.VEDASTRO_API_KEY
        self.base_url = natal_service.VEDASTRO_BASE_URL
        logger.info("✅ AdditionalFeatures инициализирован")
    
    async def get_lunar_calendar(self, year: int, month: int) -> Dict[str, Any]:
        """Лунный календарь на месяц"""
        try:
            url = f"{self.base_url}/LunarCalendar/{year}/{month}"
            headers = {"X-API-Key": self.api_key}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
            return {"error": "Не удалось получить лунный календарь"}
        except Exception as e:
            logger.error(f"Ошибка лунного календаря: {e}")
            return {"error": str(e)}
    
    async def get_transits(self, birth_date: str, birth_time: str, birth_place: str, target_date: str) -> Dict[str, Any]:
        """Транзиты планет на указанную дату (использует уже созданную натальную карту)"""
        try:
            # Создаём натальную карту
            chart = await natal_service.create_natal_chart("User", birth_date, birth_time, birth_place)
            year, month, day = map(int, target_date.split('-'))
            hour, minute = 12, 0
            lat, lon, tz = natal_service.get_coordinates(birth_place)
            
            transits = []
            for planet in chart['planets'][:7]:  # Основные планеты
                eng_name = {"Солнце":"Sun","Луна":"Moon","Меркурий":"Mercury","Венера":"Venus",
                           "Марс":"Mars","Юпитер":"Jupiter","Сатурн":"Saturn"}.get(planet['name'], "Sun")
                url = f"{self.base_url}/PlanetName/{eng_name}/Location/UserCity/Time/{hour:02d}:{minute:02d}/{day:02d}/{month:02d}/{year}/{tz}"
                headers = {"X-API-Key": self.api_key}
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        transit_sign = data.get('Sign', {}).get('Name', '?')
                        # Вычисляем аспект между натальной и транзитной позицией
                        aspect = self._get_aspect_description(planet['sign'], transit_sign)
                        transits.append({
                            'planet': planet['name'],
                            'symbol': planet['symbol'],
                            'natal_sign': planet['sign'],
                            'transit_sign': transit_sign,
                            'aspect': aspect
                        })
                    await asyncio.sleep(0.2)
            return {'transits': transits, 'date': target_date}
        except Exception as e:
            logger.error(f"Ошибка транзитов: {e}")
            return {"error": str(e)}
    
    async def get_auspicious_dates(self, birth_date: str, purpose: str = "general") -> List[str]:
        """Благоприятные даты для важных дел"""
        try:
            today = datetime.now()
            dates = []
            for i in range(1, 31):
                check_date = today + timedelta(days=i)
                url = f"{self.base_url}/AuspiciousDay/{check_date.year}/{check_date.month}/{check_date.day}"
                headers = {"X-API-Key": self.api_key}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('is_auspicious', False):
                            dates.append(check_date.strftime('%Y-%m-%d'))
                    await asyncio.sleep(0.2)
            return dates[:10]
        except Exception as e:
            logger.error(f"Ошибка благоприятных дат: {e}")
            return []
    
    async def get_extended_compatibility(self, person1: Dict, person2: Dict) -> Dict[str, Any]:
        """Расширенная совместимость (синастрия) с использованием реальных долгот"""
        try:
            chart1 = await natal_service.create_natal_chart("Person1", person1['date'], person1['time'], person1['place'])
            chart2 = await natal_service.create_natal_chart("Person2", person2['date'], person2['time'], person2['place'])
            
            synastry = []
            for p1 in chart1['planets'][:7]:
                for p2 in chart2['planets'][:7]:
                    # Проверяем аспекты по долготе
                    diff = abs(p1.get('longitude', 0) - p2.get('longitude', 0))
                    diff = min(diff, 360 - diff)
                    if diff < 10:
                        synastry.append({
                            'planet1': f"{p1['symbol']}{p1['name']}",
                            'planet2': f"{p2['symbol']}{p2['name']}",
                            'sign1': p1['sign'],
                            'sign2': p2['sign'],
                            'house1': p1['house'],
                            'house2': p2['house'],
                            'orbis': round(diff, 1)
                        })
            
            total_score = 50 + len(synastry) * 5
            if chart1['element'] == chart2['element']:
                total_score += 15
            if chart1['quality'] == chart2['quality']:
                total_score += 10
            
            return {
                'total_score': min(100, total_score),
                'synastry_aspects': synastry,
                'sign1': chart1['sun_sign'],
                'sign2': chart2['sun_sign'],
                'element1': chart1['element'],
                'element2': chart2['element'],
                'quality1': chart1['quality'],
                'quality2': chart2['quality'],
                'recommendation': self._get_recommendation(total_score)
            }
        except Exception as e:
            logger.error(f"Ошибка расширенной совместимости: {e}")
            return {"error": str(e)}
    
    def _get_aspect_description(self, sign1: str, sign2: str) -> str:
        aspects = {
            ('Овен','Лев'): 'трин', ('Телец','Дева'): 'секстиль',
            ('Близнецы','Стрелец'): 'оппозиция', ('Рак','Козерог'): 'оппозиция'
        }
        return aspects.get((sign1, sign2), aspects.get((sign2, sign1), 'нейтральный'))
    
    def _get_recommendation(self, score: int) -> str:
        if score >= 80:
            return "Отличная совместимость! Поддерживайте друг друга и развивайте общие интересы."
        elif score >= 60:
            return "Хорошая совместимость. Учитесь слушать друг друга и находить компромиссы."
        else:
            return "Сложная совместимость. Работайте над взаимопониманием и уважением различий."

additional_features = AdditionalFeatures()