import os
import uuid
import logging
import random
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm

logger = logging.getLogger(__name__)

# Пути к ресурсам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
FONT_BOLD_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans-Bold.ttf')
BACKGROUND_PATH = os.path.join(BASE_DIR, 'static', 'nate-rayfield-_WR6tUIAJe8-unsplash.jpg')

# Регистрируем шрифты
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))
    FONT_NAME = 'DejaVuSans'
    logger.info(f"✅ Шрифт загружен: {FONT_PATH}")
else:
    logger.warning(f"❌ Шрифт не найден: {FONT_PATH}")
    FONT_NAME = 'Helvetica'

if os.path.exists(FONT_BOLD_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_BOLD_PATH))
    FONT_BOLD_NAME = 'DejaVuSans-Bold'
    logger.info(f"✅ Жирный шрифт загружен: {FONT_BOLD_PATH}")
else:
    logger.warning(f"❌ Жирный шрифт не найден: {FONT_BOLD_PATH}")
    FONT_BOLD_NAME = 'Helvetica-Bold'

# Цвета для текста
TEXT_WHITE = HexColor('#FFFFFF')
TEXT_GOLD = HexColor('#FFD700')
TEXT_LIGHT = HexColor('#F0F0F0')

class PDFGenerator:
    def _draw_background(self, c, width, height):
        """Рисует фон из изображения"""
        if os.path.exists(BACKGROUND_PATH):
            try:
                bg = ImageReader(BACKGROUND_PATH)
                # Рисуем изображение на весь лист
                c.drawImage(bg, 0, 0, width=width, height=height,
                           preserveAspectRatio=True, mask='auto')
                logger.info(f"✅ Фон загружен: {BACKGROUND_PATH}")
                
                # Добавляем полупрозрачную затемняющую накладку для лучшей читаемости
                c.setFillColor(black)
                c.setFillAlpha(0.3)
                c.rect(0, 0, width, height, fill=1)
                c.setFillAlpha(1.0)
                
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки фона: {e}")
        
        # Если фона нет, рисуем синий фон
        logger.warning("Фон не найден, использую синий фон")
        c.setFillColor(HexColor('#1a2a3a'))
        c.rect(0, 0, width, height, fill=1)
        return False
    
    def _draw_decorative_frame(self, c, width, height):
        """Рисует декоративную рамку"""
        # Внешняя рамка
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(2)
        c.rect(20, 20, width-40, height-40, stroke=1, fill=0)
        
        # Внутренняя рамка
        c.setStrokeColor(TEXT_LIGHT)
        c.setLineWidth(1)
        c.rect(25, 25, width-50, height-50, stroke=1, fill=0)
    
    def _draw_header(self, c, width, height, title, subtitle=None):
        """Рисует заголовок"""
        # Основной заголовок
        c.setFont(FONT_BOLD_NAME, 32)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width/2, height-60, title)
        
        # Подзаголовок
        if subtitle:
            c.setFont(FONT_NAME, 16)
            c.setFillColor(TEXT_LIGHT)
            c.drawCentredString(width/2, height-90, subtitle)
        
        # Декоративная линия под заголовком
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1.5)
        c.line(width/4, height-100, width*3/4, height-100)
    
    def _draw_wrapped_text(self, c, text, x, y, max_width, font_name=FONT_NAME, font_size=11, color=TEXT_WHITE):
        """Рисует текст с переносом строк"""
        c.setFont(font_name, font_size)
        c.setFillColor(color)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        for line in lines:
            if y < 50:  # Если текст выходит за пределы страницы
                break
            c.drawString(x, y, line)
            y -= 15
        
        return y
    
    def create_natal_chart_pdf(self, data):
        """Создает PDF натальной карты"""
        filename = f"natal_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Рисуем фон
        self._draw_background(c, width, height)
        
        # Рисуем рамку
        self._draw_decorative_frame(c, width, height)
        
        # Заголовок
        self._draw_header(c, width, height, "Натальная карта", data.get('name', 'Пользователь'))
        
        # Данные рождения
        y = height - 150
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "* ДАННЫЕ РОЖДЕНИЯ")
        y -= 25
        
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_WHITE)
        c.drawString(70, y, f"Дата: {data.get('birth_date', 'Не указано')}")
        y -= 20
        c.drawString(70, y, f"Время: {data.get('birth_time', 'Не указано')}")
        y -= 20
        c.drawString(70, y, f"Место: {data.get('birth_place', 'Не указано')}")
        y -= 30
        
        # Астрологические данные
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "* АСТРОЛОГИЧЕСКИЕ ДАННЫЕ")
        y -= 25
        
        # Генерируем данные для планет
        signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 
                 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        
        planets = [
            ('☉ Солнце', random.choice(signs), random.randint(1, 30)),
            ('☽ Луна', random.choice(signs), random.randint(1, 30)),
            ('☿ Меркурий', random.choice(signs), random.randint(1, 30)),
            ('♀ Венера', random.choice(signs), random.randint(1, 30)),
            ('♂ Марс', random.choice(signs), random.randint(1, 30)),
            ('♃ Юпитер', random.choice(signs), random.randint(1, 30)),
            ('♄ Сатурн', random.choice(signs), random.randint(1, 30)),
        ]
        
        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_WHITE)
        
        # Левая колонка (первые 4 планеты)
        y_left = y
        for i in range(4):
            planet, sign, degree = planets[i]
            c.drawString(70, y_left, f"{planet} в {sign} {degree}°")
            y_left -= 18
        
        # Правая колонка (остальные планеты)
        y_right = y
        for i in range(4, 7):
            planet, sign, degree = planets[i]
            c.drawString(300, y_right, f"{planet} в {sign} {degree}°")
            y_right -= 18
        
        c.save()
        logger.info(f"✅ PDF натальной карты создан: {filename}")
        return filename
    
    def create_horoscope_pdf(self, data):
        """Создает PDF гороскопа"""
        filename = f"horoscope_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Рисуем фон
        self._draw_background(c, width, height)
        
        # Рисуем рамку
        self._draw_decorative_frame(c, width, height)
        
        # Заголовок
        self._draw_header(c, width, height, "Гороскоп", f"для {data.get('user_name', 'Пользователь')}")
        
        # Дата
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, height-130, data.get('date', ''))
        
        # Разделитель
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1)
        c.line(50, height-140, width-50, height-140)
        
        # Текст гороскопа
        y = height - 170
        left_margin = 50
        right_margin = width - 50
        text_width = right_margin - left_margin
        
        text = data.get('horoscope', '')
        if text:
            y = self._draw_wrapped_text(c, text, left_margin, y, text_width, 
                                        FONT_NAME, 11, TEXT_WHITE)
        
        # Астрологический совет
        if y > 100:
            y -= 30
            c.setFont(FONT_BOLD_NAME, 14)
            c.setFillColor(TEXT_GOLD)
            c.drawString(left_margin, y, "* СОВЕТ ЗВЁЗД")  # Заменили эмодзи на *
            y -= 20
            
            advice = "Прислушайтесь к своей интуиции сегодня. Звёзды благоволят новым начинаниям!"
            self._draw_wrapped_text(c, advice, left_margin+20, y, text_width-20, 
                                   FONT_NAME, 10, TEXT_LIGHT)
        
        c.save()
        logger.info(f"✅ PDF гороскопа создан: {filename}")
        return filename
    
    def create_test_pdf(self):
        """Создает тестовый PDF для проверки"""
        filename = f"test_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Рисуем фон
        self._draw_background(c, width, height)
        
        # Рисуем рамку
        self._draw_decorative_frame(c, width, height)
        
        # Заголовок
        self._draw_header(c, width, height, "Тестовый PDF")
        
        c.setFont(FONT_NAME, 14)
        c.setFillColor(TEXT_WHITE)
        c.drawString(50, height-150, "✅ PDF работает!")
        c.drawString(50, height-180, "✅ Шрифты загружены")
        c.drawString(50, height-210, f"✅ Фон: {os.path.basename(BACKGROUND_PATH) if os.path.exists(BACKGROUND_PATH) else 'Не найден'}")
        
        c.save()
        logger.info(f"✅ Тестовый PDF создан: {filename}")
        return filename

# Создаем экземпляр
pdf_gen = PDFGenerator()