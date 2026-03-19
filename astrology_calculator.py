from datetime import datetime, timedelta
import math
import random

class AstrologyCalculator:
    @staticmethod
    def get_zodiac_sign(birth_date):
        """Определяет знак зодиака по дате"""
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
    
    @staticmethod
    def get_chinese_zodiac(year):
        """Определяет знак китайского гороскопа по году"""
        animals = [
            'Крыса', 'Бык', 'Тигр', 'Кролик', 'Дракон', 'Змея',
            'Лошадь', 'Коза', 'Обезьяна', 'Петух', 'Собака', 'Свинья'
        ]
        return animals[(year - 1900) % 12]
    
    @staticmethod
    def get_element_by_year(year):
        """Определяет стихию по году рождения"""
        elements = ['Дерево', 'Огонь', 'Земля', 'Металл', 'Вода']
        return elements[(year - 1900) % 5]
    
    @staticmethod
    def calculate_moon_phase(birth_date):
        """Определяет фазу Луны в день рождения (упрощенно)"""
        # Базовая дата для расчета (новолуние 2020-01-01)
        base_date = datetime(2020, 1, 1)
        days_diff = (birth_date - base_date).days
        lunar_cycle = 29.53  # дней
        phase_position = (days_diff % lunar_cycle) / lunar_cycle
        
        if phase_position < 0.125:
            return "🌑 Новолуние"
        elif phase_position < 0.25:
            return "🌒 Растущий серп"
        elif phase_position < 0.375:
            return "🌓 Первая четверть"
        elif phase_position < 0.5:
            return "🌔 Растущая луна"
        elif phase_position < 0.625:
            return "🌕 Полнолуние"
        elif phase_position < 0.75:
            return "🌖 Убывающая луна"
        elif phase_position < 0.875:
            return "🌗 Последняя четверть"
        else:
            return "🌘 Убывающий серп"
    
    @staticmethod
    def calculate_time_angle(birth_time):
        """Вычисляет угол на основе времени рождения"""
        if not birth_time:
            return 0
        try:
            time_obj = datetime.strptime(birth_time, "%H:%M")
            minutes = time_obj.hour * 60 + time_obj.minute
            return (minutes / 1440) * 360  # угол от 0 до 360
        except:
            return 0

class CompatibilityCalculator:
    def __init__(self):
        self.astro = AstrologyCalculator()
    
    def calculate_compatibility(self, person1_data, person2_data):
        """Рассчитывает совместимость на основе всех данных"""
        
        # Парсим данные
        try:
            date1 = datetime.strptime(person1_data.get('date', '2000-01-01'), '%Y-%m-%d')
            date2 = datetime.strptime(person2_data.get('date', '2000-01-01'), '%Y-%m-%d')
        except:
            date1 = datetime(2000, 1, 1)
            date2 = datetime(2000, 1, 1)
        
        # Получаем знаки зодиака
        sign1 = self.astro.get_zodiac_sign(date1)
        sign2 = self.astro.get_zodiac_sign(date2)
        
        # Получаем китайские знаки
        chinese1 = self.astro.get_chinese_zodiac(date1.year)
        chinese2 = self.astro.get_chinese_zodiac(date2.year)
        
        # Получаем стихии
        element1 = self.astro.get_element_by_year(date1.year)
        element2 = self.astro.get_element_by_year(date2.year)
        
        # Фазы луны
        moon1 = self.astro.calculate_moon_phase(date1)
        moon2 = self.astro.calculate_moon_phase(date2)
        
        # Углы времени
        time_angle1 = self.astro.calculate_time_angle(person1_data.get('time'))
        time_angle2 = self.astro.calculate_time_angle(person2_data.get('time'))
        
        # Рассчитываем базовую совместимость знаков
        base_score = self._get_zodiac_compatibility(sign1, sign2)
        
        # Модификаторы
        modifiers = []
        
        # Китайский гороскоп
        chinese_score = self._get_chinese_compatibility(chinese1, chinese2)
        if chinese_score > 0:
            modifiers.append(("Китайский гороскоп", chinese_score))
        
        # Стихии
        element_score = self._get_element_compatibility(element1, element2)
        if element_score != 0:
            modifiers.append(("Стихии", element_score))
        
        # Фазы луны
        moon_score = self._get_moon_compatibility(moon1, moon2)
        if moon_score != 0:
            modifiers.append(("Фазы луны", moon_score))
        
        # Временной угол (если есть время рождения)
        if person1_data.get('time') and person2_data.get('time'):
            time_score = self._get_time_compatibility(time_angle1, time_angle2)
            modifiers.append(("Время рождения", time_score))
        
        # Итоговый счет
        total_score = base_score
        for _, score in modifiers:
            total_score += score
        
        # Ограничиваем от 0 до 100
        total_score = max(0, min(100, total_score))
        
        return {
            'total_score': total_score,
            'base_score': base_score,
            'signs': (sign1, sign2),
            'chinese': (chinese1, chinese2),
            'elements': (element1, element2),
            'moons': (moon1, moon2),
            'modifiers': modifiers,
            'description': self._get_description(total_score, sign1, sign2),
            'advice': self._get_advice(total_score)
        }
    
    def _get_zodiac_compatibility(self, sign1, sign2):
        """База совместимости знаков зодиака"""
        compatibility = {
            ('Овен', 'Лев'): 90, ('Овен', 'Стрелец'): 95,
            ('Овен', 'Близнецы'): 75, ('Овен', 'Водолей'): 70,
            ('Телец', 'Дева'): 90, ('Телец', 'Козерог'): 85,
            ('Телец', 'Рак'): 75, ('Телец', 'Рыбы'): 70,
            ('Близнецы', 'Весы'): 90, ('Близнецы', 'Водолей'): 85,
            ('Близнецы', 'Овен'): 75, ('Близнецы', 'Лев'): 70,
            ('Рак', 'Скорпион'): 95, ('Рак', 'Рыбы'): 90,
            ('Рак', 'Дева'): 70, ('Рак', 'Козерог'): 60,
            ('Лев', 'Стрелец'): 95, ('Лев', 'Овен'): 90,
            ('Лев', 'Близнецы'): 75, ('Лев', 'Весы'): 65,
            ('Дева', 'Козерог'): 90, ('Дева', 'Телец'): 85,
            ('Дева', 'Рак'): 70, ('Дева', 'Скорпион'): 65,
            ('Весы', 'Водолей'): 90, ('Весы', 'Близнецы'): 85,
            ('Весы', 'Лев'): 75, ('Весы', 'Стрелец'): 70,
            ('Скорпион', 'Рыбы'): 95, ('Скорпион', 'Рак'): 90,
            ('Скорпион', 'Дева'): 70, ('Скорпион', 'Козерог'): 65,
            ('Стрелец', 'Овен'): 95, ('Стрелец', 'Лев'): 90,
            ('Стрелец', 'Весы'): 70, ('Стрелец', 'Водолей'): 65,
            ('Козерог', 'Телец'): 90, ('Козерог', 'Дева'): 85,
            ('Козерог', 'Скорпион'): 70, ('Козерог', 'Рыбы'): 60,
            ('Водолей', 'Весы'): 90, ('Водолей', 'Близнецы'): 85,
            ('Водолей', 'Овен'): 70, ('Водолей', 'Стрелец'): 65,
            ('Рыбы', 'Рак'): 95, ('Рыбы', 'Скорпион'): 90,
            ('Рыбы', 'Телец'): 70, ('Рыбы', 'Козерог'): 60,
        }
        
        # Проверяем оба порядка
        if (sign1, sign2) in compatibility:
            return compatibility[(sign1, sign2)]
        elif (sign2, sign1) in compatibility:
            return compatibility[(sign2, sign1)]
        else:
            return 75  # Базовая совместимость
    
    def _get_chinese_compatibility(self, chinese1, chinese2):
        """Совместимость по китайскому гороскопу"""
        pairs = {
            ('Крыса', 'Дракон'): 5, ('Крыса', 'Обезьяна'): 5,
            ('Бык', 'Змея'): 5, ('Бык', 'Петух'): 5,
            ('Тигр', 'Лошадь'): 5, ('Тигр', 'Собака'): 5,
            ('Кролик', 'Коза'): 5, ('Кролик', 'Свинья'): 5,
            ('Дракон', 'Обезьяна'): 5, ('Дракон', 'Крыса'): 5,
            ('Змея', 'Петух'): 5, ('Змея', 'Бык'): 5,
            ('Лошадь', 'Собака'): 5, ('Лошадь', 'Тигр'): 5,
            ('Коза', 'Свинья'): 5, ('Коза', 'Кролик'): 5,
            ('Обезьяна', 'Крыса'): 5, ('Обезьяна', 'Дракон'): 5,
            ('Петух', 'Бык'): 5, ('Петух', 'Змея'): 5,
            ('Собака', 'Тигр'): 5, ('Собака', 'Лошадь'): 5,
            ('Свинья', 'Кролик'): 5, ('Свинья', 'Коза'): 5,
        }
        
        if (chinese1, chinese2) in pairs:
            return pairs[(chinese1, chinese2)]
        elif (chinese2, chinese1) in pairs:
            return pairs[(chinese2, chinese1)]
        return 0
    
    def _get_element_compatibility(self, element1, element2):
        """Совместимость стихий"""
        elements_order = ['Дерево', 'Огонь', 'Земля', 'Металл', 'Вода']
        
        try:
            idx1 = elements_order.index(element1)
            idx2 = elements_order.index(element2)
            
            # Порождающие циклы
            if (idx2 - idx1) % 5 == 1:
                return 3  # Один порождает другой
            elif (idx1 - idx2) % 5 == 1:
                return 2  # Второй порождает первый
            elif abs(idx1 - idx2) == 2 or abs(idx1 - idx2) == 3:
                return -2  # Конфликтующие стихии
            else:
                return 1  # Нейтральные
        except:
            return 0
    
    def _get_moon_compatibility(self, moon1, moon2):
        """Совместимость по фазам луны"""
        if moon1 == moon2:
            return 3
        elif 'луна' in moon1 and 'луна' in moon2:
            return 1
        return 0
    
    def _get_time_compatibility(self, angle1, angle2):
        """Совместимость по времени рождения"""
        diff = abs(angle1 - angle2)
        if diff < 30 or diff > 330:
            return 5  # Гармоничный аспект
        elif abs(diff - 180) < 30:
            return 3  # Оппозиция
        elif abs(diff - 90) < 30 or abs(diff - 270) < 30:
            return 2  # Квадратура
        else:
            return 1  # Нейтрально
    
    def _get_description(self, score, sign1, sign2):
        """Описание совместимости"""
        if score >= 90:
            return f"✨ Идеальная совместимость! {sign1} и {sign2} созданы друг для друга. Ваши энергии идеально дополняют друг друга."
        elif score >= 80:
            return f"🌟 Отличная совместимость! У вас много общего и вы хорошо понимаете друг друга."
        elif score >= 70:
            return f"💫 Хорошая совместимость. Есть над чем работать, но у вас большой потенциал."
        elif score >= 60:
            return f"⭐ Неплохая совместимость. При взаимных усилиях отношения могут быть гармоничными."
        elif score >= 50:
            return f"⚡ Средняя совместимость. Вам нужно учиться понимать друг друга."
        else:
            return f"🌊 Сложная совместимость. Разные характеры, но это не приговор - любовь может преодолеть всё!"
    
    def _get_advice(self, score):
        """Совет на основе совместимости"""
        if score >= 80:
            return "Доверяйте друг другу и поддерживайте в начинаниях. Ваш союз - это сила!"
        elif score >= 60:
            return "Больше общайтесь и делитесь чувствами. Учитесь находить компромиссы."
        else:
            return "Работайте над взаимопониманием. Цените различия - они делают вас уникальными."

compatibility_calc = CompatibilityCalculator()