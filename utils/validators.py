import re
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Кастомное исключение для ошибок валидации"""
    pass

class InputValidator:
    """Класс для валидации пользовательского ввода"""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """
        Проверяет корректность имени
        Возвращает (успех, сообщение об ошибке или очищенное имя)
        """
        if not name or not name.strip():
            return False, "Имя не может быть пустым"
        
        # Удаляем лишние пробелы и спецсимволы
        cleaned = ' '.join(name.strip().split())
        
        # Проверяем длину
        if len(cleaned) < 2:
            return False, "Имя должно содержать минимум 2 символа"
        
        if len(cleaned) > 50:
            return False, "Имя слишком длинное (максимум 50 символов)"
        
        # Проверяем, что имя содержит только буквы, пробелы, дефисы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', cleaned):
            return False, "Имя может содержать только буквы, пробелы и дефисы"
        
        return True, cleaned
    
    @staticmethod
    def validate_birth_date(date_str: str) -> Tuple[bool, str]:
        """
        Проверяет корректность даты рождения
        Возвращает (успех, сообщение об ошибке или дату в формате YYYY-MM-DD)
        """
        if not date_str or not date_str.strip():
            return False, "Дата не может быть пустой"
        
        # Удаляем пробелы
        cleaned = date_str.strip()
        
        # Поддерживаемые форматы
        patterns = [
            (r'^\d{4}-\d{2}-\d{2}$', '%Y-%m-%d'),  # 1990-01-01
            (r'^\d{2}\.\d{2}\.\d{4}$', '%d.%m.%Y'),  # 01.01.1990
            (r'^\d{2}/\d{2}/\d{4}$', '%d/%m/%Y'),   # 01/01/1990
            (r'^\d{2}-\d{2}-\d{4}$', '%d-%m-%Y'),   # 01-01-1990
        ]
        
        for pattern, date_format in patterns:
            if re.match(pattern, cleaned):
                try:
                    date_obj = datetime.strptime(cleaned, date_format)
                    
                    # Проверяем, что дата не в будущем
                    if date_obj > datetime.now():
                        return False, "Дата рождения не может быть в будущем"
                    
                    # Проверяем, что человеку не больше 120 лет
                    age = (datetime.now() - date_obj).days / 365.25
                    if age > 120:
                        return False, "Возраст не может быть больше 120 лет"
                    
                    if age < 0:
                        return False, "Некорректная дата"
                    
                    # Возвращаем в стандартном формате
                    return True, date_obj.strftime('%Y-%m-%d')
                    
                except ValueError:
                    continue
        
        return False, "Неверный формат даты. Используйте ГГГГ-ММ-ДД (например, 1990-01-01)"
    
    @staticmethod
    def validate_birth_time(time_str: str) -> Tuple[bool, str]:
        """
        Проверяет корректность времени рождения
        Возвращает (успех, сообщение об ошибке или время в формате HH:MM)
        """
        if not time_str or time_str.lower() == '/skip':
            return True, '12:00'  # Значение по умолчанию
        
        cleaned = time_str.strip()
        
        # Поддерживаемые форматы
        patterns = [
            (r'^\d{1,2}:\d{2}$', '%H:%M'),    # 14:30
            (r'^\d{1,2}\.\d{2}$', '%H.%M'),   # 14.30
            (r'^\d{1,2}$', '%H'),              # 14
        ]
        
        for pattern, time_format in patterns:
            if re.match(pattern, cleaned):
                try:
                    if time_format == '%H':
                        # Только час
                        hour = int(cleaned)
                        if 0 <= hour <= 23:
                            return True, f"{hour:02d}:00"
                    else:
                        time_obj = datetime.strptime(cleaned, time_format)
                        return True, time_obj.strftime('%H:%M')
                except ValueError:
                    continue
        
        return False, "Неверный формат времени. Используйте ЧЧ:ММ (например, 14:30)"
    
    @staticmethod
    def validate_birth_place(place: str) -> Tuple[bool, str]:
        """
        Проверяет корректность места рождения
        Возвращает (успех, сообщение об ошибке или очищенное место)
        """
        if not place or place.lower() == '/skip':
            return True, 'Не указано'
        
        # Удаляем лишние пробелы и спецсимволы
        cleaned = ' '.join(place.strip().split())
        
        # Проверяем длину
        if len(cleaned) < 2:
            return False, "Название места должно содержать минимум 2 символа"
        
        if len(cleaned) > 100:
            return False, "Название места слишком длинное (максимум 100 символов)"
        
        # Разрешаем буквы, пробелы, дефисы, запятые, точки
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z0-9\s\-\.,]+$', cleaned):
            return False, "Название места содержит недопустимые символы"
        
        return True, cleaned
    
    @staticmethod
    def validate_question(question: str) -> Tuple[bool, str]:
        """
        Проверяет корректность вопроса к AI
        Возвращает (успех, сообщение об ошибке или очищенный вопрос)
        """
        if not question or not question.strip():
            return False, "Вопрос не может быть пустым"
        
        # Удаляем лишние пробелы
        cleaned = ' '.join(question.strip().split())
        
        # Проверяем длину
        if len(cleaned) < 5:
            return False, "Вопрос слишком короткий (минимум 5 символов)"
        
        if len(cleaned) > 500:
            return False, "Вопрос слишком длинный (максимум 500 символов)"
        
        # Проверяем на явный спам/ерунду
        spam_patterns = [
            r'(.)\1{4,}',  # Много повторяющихся символов (ааааа)
            r'[а-яА-ЯёЁa-zA-Z]\d{4,}',  # Буква и много цифр
            r'^\d+$',  # Только цифры
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, cleaned):
                return False, "Пожалуйста, задайте осмысленный вопрос"
        
        return True, cleaned
    
    @staticmethod
    def validate_compatibility_data(text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Парсит и валидирует данные для совместимости
        Ожидаемый формат: "Имя, ГГГГ-ММ-ДД, ЧЧ:ММ" или "Имя, ГГГГ-ММ-ДД"
        """
        if not text or not text.strip():
            return False, {"error": "Данные не могут быть пустыми"}
        
        # Разделяем по запятым
        parts = [p.strip() for p in text.split(',')]
        
        if len(parts) < 2:
            return False, {"error": "Укажите имя и дату через запятую"}
        
        name = parts[0]
        # Валидируем имя
        name_valid, name_result = InputValidator.validate_name(name)
        if not name_valid:
            return False, {"error": name_result}
        
        # Ищем дату
        date_str = None
        time_str = None
        
        for part in parts[1:]:
            # Проверяем, похоже ли на дату
            if re.search(r'\d{4}-\d{2}-\d{2}|\d{2}[\.\-/]\d{2}[\.\-/]\d{4}', part):
                date_valid, date_result = InputValidator.validate_birth_date(part)
                if date_valid:
                    date_str = date_result
            # Проверяем, похоже ли на время
            elif re.search(r'\d{1,2}:\d{2}|\d{1,2}\.\d{2}', part):
                time_valid, time_result = InputValidator.validate_birth_time(part)
                if time_valid:
                    time_str = time_result
        
        if not date_str:
            return False, {"error": "Не удалось найти корректную дату рождения"}
        
        return True, {
            'name': name_result,
            'date': date_str,
            'time': time_str or '12:00'
        }

# Создаем экземпляр для удобства
validator = InputValidator()