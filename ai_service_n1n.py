import httpx
import logging
import random
import asyncio
import re
from typing import Optional, Dict, Any
from config import N1N_API_KEY, N1N_BASE_URL, N1N_MODEL
from database.db import UserDB
from datetime import datetime

logger = logging.getLogger(__name__)

class N1NService:
    def __init__(self):
        self.api_key = N1N_API_KEY
        self.base_url = N1N_BASE_URL
        self.model = N1N_MODEL
        
        # Системные промпты для разных типов вопросов
        self.system_prompts = {
            'general': """Ты - профессиональный астролог с 20-летним опытом. 
Отвечай кратко (2-3 предложения), но информативно. 
Используй дружелюбный тон.
НЕ используй эмодзи в ответах.
НЕ упоминай конкретные даты (числа месяца).
Говори обобщенно: 'сегодня', 'на этой неделе', 'в ближайшее время'.""",
            
            'horoscope': """Ты - астролог. Составь краткий гороскоп на сегодня.
НЕ упоминай конкретные числа и даты.
Используй общие формулировки: 'сегодня', 'в этот день'.
Дай совет, связанный со знаком зодиака.
Ответ должен быть 2-3 предложения.
НЕ используй эмодзи.""",
            
            'compatibility': """Ты - астролог. Проанализируй совместимость двух людей.
Укажи их знаки зодиака.
Дай оценку совместимости (отлично/хорошо/средне/сложно).
Объясни почему.
Дай совет для отношений.
Ответ должен быть 3-4 предложения.
НЕ используй эмодзи."""
        }
        
        logger.info(f"N1N Service инициализирован. Модель: {self.model}")
    
    async def process_question(self, user_id: int, question: str) -> Dict[str, Any]:
        """Обрабатывает вопрос пользователя с контекстом"""
        try:
            # Получаем данные пользователя
            user_data = await UserDB.get_user(user_id)
            
            # Определяем тип вопроса
            question_lower = question.lower()
            prompt_type = self._detect_question_type(question_lower)
            
            # Формируем контекст
            context = self._build_context(user_data, question_lower)
            
            # Выбираем системный промпт
            system_prompt = self.system_prompts.get(prompt_type, self.system_prompts['general'])
            
            # Добавляем инструкцию о датах
            date_instruction = "ВАЖНО: НЕ используй конкретные числа и даты в ответе! Говори обобщенно."
            
            full_prompt = f"{context}\n\nВопрос: {question}\n\n{date_instruction}"
            
            # Отправляем запрос к API
            answer = await self._query_api(system_prompt, full_prompt)
            
            # Пост-обработка ответа
            answer = self._clean_response(answer)
            
            return {
                'type': 'ai_answer',
                'message': answer,
                'prompt_type': prompt_type
            }
            
        except Exception as e:
            logger.error(f"Ошибка в process_question: {e}")
            return {
                'type': 'ai_answer',
                'message': self._get_fallback_response(question),
                'prompt_type': 'fallback'
            }
    
    def _detect_question_type(self, question: str) -> str:
        """Определяет тип вопроса"""
        if any(word in question for word in ['гороскоп', 'сегодня', 'завтра', 'неделя']):
            return 'horoscope'
        elif any(word in question for word in ['совместимость', 'отношения', 'любовь', 'пара', 'вместе']):
            return 'compatibility'
        elif any(word in question for word in ['карьера', 'работа', 'деньги', 'бизнес']):
            return 'career'
        elif any(word in question for word in ['здоровье', 'самочувствие']):
            return 'health'
        else:
            return 'general'
    
    def _build_context(self, user_data: Optional[Dict], question: str) -> str:
        """Строит контекст из данных пользователя"""
        if not user_data:
            return ""
        
        context_parts = []
        
        if user_data.get('birth_date'):
            from astrology_calculator import AstrologyCalculator
            try:
                birth_date = datetime.strptime(user_data['birth_date'], '%Y-%m-%d')
                sign = AstrologyCalculator.get_zodiac_sign(birth_date)
                context_parts.append(f"Знак зодиака пользователя: {sign}")
            except:
                pass
        
        if user_data.get('birth_time'):
            context_parts.append(f"Время рождения: {user_data['birth_time']}")
        
        if user_data.get('birth_place'):
            context_parts.append(f"Место рождения: {user_data['birth_place']}")
        
        if context_parts:
            return "Данные пользователя:\n" + "\n".join(context_parts)
        
        return ""
    
    async def _query_api(self, system_prompt: str, user_prompt: str) -> str:
        """Отправляет запрос к API n1n.ai"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"API ошибка {response.status_code}: {response.text}")
                    return self._get_fallback_response(user_prompt)
                    
        except Exception as e:
            logger.error(f"Ошибка запроса к API: {e}")
            return self._get_fallback_response(user_prompt)
    
    def _clean_response(self, text: str) -> str:
        """Очищает ответ от нежелательного контента"""
        if not text:
            return text
        
        # Удаляем эмодзи
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # эмоции
            u"\U0001F300-\U0001F5FF"  # символы
            u"\U0001F680-\U0001F6FF"  # транспорт
            u"\U0001F1E0-\U0001F1FF"  # флаги
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        
        # Удаляем упоминания конкретных дат
        date_patterns = [
            r'\b\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b',
            r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'сегодня\s+\d{1,2}',
        ]
        
        for pattern in date_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _get_fallback_response(self, question: str) -> str:
        """Возвращает запасной ответ при ошибке"""
        responses = [
            "🌟 Звёзды говорят, что сегодня благоприятный день для размышлений.",
            "🔮 Астрологи советуют довериться своей интуиции.",
            "✨ Энергия дня располагает к новым начинаниям.",
            "🌙 Луна в гармоничной фазе - хорошее время для планирования.",
            "💫 Планеты выстраиваются в удачную конфигурацию для ваших дел."
        ]
        return random.choice(responses)

# Создаем экземпляр
ai_service = N1NService()