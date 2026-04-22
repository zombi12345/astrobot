import logging
import uuid
import os
import math
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

from vedastro import *

logger = logging.getLogger(__name__)

class NatalService:
    CITY_COORDS = {
        'минск': (53.9045, 27.5615, '+03:00'),
        'москва': (55.7558, 37.6173, '+03:00'),
        'киев': (50.4501, 30.5234, '+02:00'),
        'санкт-петербург': (59.9343, 30.3351, '+03:00'),
        # ... остальные города (можно оставить как было)
    }
    
    VEDASTRO_API_KEY = os.environ.get('VEDASTRO_API_KEY', '')
    
    def __init__(self):
        Calculate.SetAPIKey(self.VEDASTRO_API_KEY)
        Calculate.SetAyanamsa(Ayanamsa.Lahiri)
        logger.info("✅ VedAstro сервис инициализирован (библиотека vedastro)")
    
    def get_coordinates(self, place: str):
        # ... (без изменений, как в предыдущем коде)
    
    def validate_date(self, date_str: str):
        # ... (без изменений)
    
    def validate_time(self, time_str: str):
        # ... (без изменений)
    
    def validate_place(self, place: str):
        # ... (без изменений)
    
    def create_natal_chart(self, name: str, birth_date: str, birth_time: str, birth_place: str) -> Dict[str, Any]:
        logger.info(f"🔮 Создание натальной карты для {name}")
        # валидация...
        year, month, day = date_parts
        hour, minute = time_parts if time_parts else (12, 0)
        lat, lon, tz = self.get_coordinates(place_clean)
        
        geo = GeoLocation(place_clean, lon, lat)
        time_obj = Time(hour=hour, minute=minute, day=day, month=month, year=year, offset=tz, geolocation=geo)
        
        # Список планет с правильными именами для vedastro
        planets_map = [
            ("Sun", "Солнце", "☉"),
            ("Moon", "Луна", "☽"),
            ("Mercury", "Меркурий", "☿"),
            ("Venus", "Венера", "♀"),
            ("Mars", "Марс", "♂"),
            ("Jupiter", "Юпитер", "♃"),
            ("Saturn", "Сатурн", "♄"),
            ("Uranus", "Уран", "⛢"),
            ("Neptune", "Нептун", "♆"),
            ("Pluto", "Плутон", "♇")
        ]
        
        planets_data = []
        for eng, rus, sym in planets_map:
            try:
                # Получаем объект планеты
                planet_enum = getattr(PlanetName, eng)
                planet_data = Calculate.AllPlanetData(planet_enum, time_obj)
                sign = planet_data.Sign.Name if hasattr(planet_data, 'Sign') else "Неизвестно"
                house = planet_data.HousePlanetIsIn if hasattr(planet_data, 'HousePlanetIsIn') else "?"
                retrograde = planet_data.Retrograde if hasattr(planet_data, 'Retrograde') else False
                longitude = float(planet_data.Longitude) if hasattr(planet_data, 'Longitude') else 0.0
                degree = int(longitude)
                minute_deg = int((longitude % 1) * 60)
                logger.info(f"{rus}: знак {sign}, дом {house}, долгота {longitude}°")
                planets_data.append({
                    'name': rus, 'symbol': sym, 'sign': sign, 'house': str(house),
                    'retrograde': retrograde, 'degree': degree, 'minute': minute_deg, 'longitude': longitude
                })
            except Exception as e:
                logger.error(f"Ошибка получения данных для {eng}: {e}")
                planets_data.append({
                    'name': rus, 'symbol': sym, 'sign': "Неизвестно", 'house': "?",
                    'retrograde': False, 'degree': 0, 'minute': 0, 'longitude': 0.0
                })
        
        # ... расчёт sun_sign, элементов, домов, аспектов (как в предыдущем коде)
        # (код аспектов и отчётов оставляем без изменений)
        
        return { ... }