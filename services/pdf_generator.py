import os
import uuid
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
FONT_BOLD_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans-Bold.ttf')
BACKGROUND_PATH = os.path.join(BASE_DIR, 'static', 'nate-rayfield-_WR6tUIAJe8-unsplash.jpg')

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))
    FONT_NAME = 'DejaVuSans'
else:
    FONT_NAME = 'Helvetica'

if os.path.exists(FONT_BOLD_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_BOLD_PATH))
    FONT_BOLD_NAME = 'DejaVuSans-Bold'
else:
    FONT_BOLD_NAME = 'Helvetica-Bold'

TEXT_GOLD = HexColor('#FFD700')
TEXT_LIGHT = HexColor('#F0F0F0')
TEXT_WHITE = HexColor('#FFFFFF')
BG_DARK = HexColor('#1a2a3a')
ACCENT_PURPLE = HexColor('#8B5CF6')

class ProfessionalPDFGenerator:
    def _draw_background(self, c, width, height):
        if os.path.exists(BACKGROUND_PATH):
            try:
                img = ImageReader(BACKGROUND_PATH)
                c.drawImage(img, 0, 0, width=width, height=height, preserveAspectRatio=True, mask='auto')
                c.setFillColor(white)
                c.setFillAlpha(0.3)
                c.rect(0, 0, width, height, fill=1)
                c.setFillAlpha(1.0)
                return
            except Exception as e:
                logger.warning(f"Фон не загружен: {e}")
        c.setFillColor(BG_DARK)
        c.rect(0, 0, width, height, fill=1)

    def _draw_decorative_frame(self, c, width, height):
        c.setStrokeColor(ACCENT_PURPLE)
        c.setLineWidth(2)
        c.rect(20, 20, width-40, height-40)
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1)
        c.rect(25, 25, width-50, height-50)

    def create_natal_chart_pdf(self, chart_data: dict) -> str:
        filename = f"natal_report_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        self._draw_background(c, width, height)
        self._draw_decorative_frame(c, width, height)

        c.setFont(FONT_BOLD_NAME, 26)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width/2, height-50, "✨ НАТАЛЬНАЯ КАРТА ✨")

        info = chart_data.get('birth_info', {})
        c.setFont(FONT_BOLD_NAME, 16)
        c.setFillColor(TEXT_WHITE)
        c.drawCentredString(width/2, height-85, info.get('name', 'Пользователь'))
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, height-105, f"{info.get('date', '')} в {info.get('time', '')} | {info.get('place', '')}")

        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1.5)
        c.line(width/4, height-120, width*3/4, height-120)

        y = height - 160

        # Основные характеристики
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ОСНОВНЫЕ ХАРАКТЕРИСТИКИ")
        y -= 25
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_WHITE)
        c.drawString(70, y, f"☉ Солнце в знаке: {chart_data.get('sun_sign', 'Неизвестно')}")
        y -= 20
        c.drawString(70, y, f"🌊 Стихия: {chart_data.get('element', 'Неизвестно')}")
        y -= 20
        c.drawString(70, y, f"⚡ Качество: {chart_data.get('quality', 'Неизвестно')}")
        y -= 20
        c.drawString(70, y, f"⬆ Асцендент (ASC): {chart_data.get('ascendant', 'Неизвестно')}")
        y -= 40

        # Планеты (две колонки)
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ПОЛОЖЕНИЕ ПЛАНЕТ")
        y -= 25
        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_WHITE)
        planets = chart_data.get('planets', [])
        left_x = 70
        right_x = 350
        half = (len(planets) + 1) // 2
        for i, p in enumerate(planets[:half]):
            retro = " (ретроградный)" if p.get('retrograde') else ""
            c.drawString(left_x, y, f"{p.get('symbol', '')} {p.get('name', '')}: {p.get('sign', '')} ({p.get('house', '')} дом){retro}")
            y -= 18
        y2 = height - 160 - 25 - 18 * half
        for i, p in enumerate(planets[half:]):
            retro = " (ретроградный)" if p.get('retrograde') else ""
            c.drawString(right_x, y2, f"{p.get('symbol', '')} {p.get('name', '')}: {p.get('sign', '')} ({p.get('house', '')} дом){retro}")
            y2 -= 18
        # Переходим к следующему блоку после колонок
        y = height - 160 - 25 - 18 * half - 40

        # Дома (4 колонки)
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "АСТРОЛОГИЧЕСКИЕ ДОМА")
        y -= 25
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_WHITE)
        houses = chart_data.get('houses', [])
        col_width = 100
        rows = (len(houses) + 3) // 4
        for i, house in enumerate(houses):
            col = i % 4
            row = i // 4
            x = 50 + col * col_width
            y_pos = y - row * 18
            c.drawString(x, y_pos, f"{house.get('number', '')} дом: {house.get('sign', '')}")
        y = y - rows * 18 - 40

        # Интерпретация
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
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ИНТЕРПРЕТАЦИЯ")
        y -= 25
        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_WHITE)
        sun_sign = chart_data.get('sun_sign', 'Неизвестно')
        interp = interpretations.get(sun_sign, 'у вас уникальная личность.')
        c.drawString(70, y, f"☉ Солнце в {sun_sign}: {interp}")

        # Нижний колонтитул
        c.setFont(FONT_NAME, 9)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, 40, "🔮 Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!")
        c.drawCentredString(width/2, 25, f"Сгенерировано AstroBot • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        c.save()
        return filename

    def create_horoscope_pdf(self, data: dict) -> str:
        """Создаёт PDF гороскопа (для кнопки PDF гороскопа)"""
        filename = f"horoscope_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        self._draw_background(c, width, height)
        self._draw_decorative_frame(c, width, height)

        c.setFont(FONT_BOLD_NAME, 26)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width/2, height-50, "✨ ГОРОСКОП ✨")

        c.setFont(FONT_BOLD_NAME, 16)
        c.setFillColor(TEXT_WHITE)
        c.drawCentredString(width/2, height-85, data.get('user_name', 'Пользователь'))
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, height-105, f"Дата: {data.get('date', datetime.now().strftime('%d.%m.%Y'))}")

        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1.5)
        c.line(width/4, height-120, width*3/4, height-120)

        y = height - 160
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_WHITE)
        horoscope_text = data.get('horoscope', 'Сегодня звёзды благоволят вам.')
        # Умный перенос
        lines = []
        words = horoscope_text.split()
        line = ""
        for word in words:
            if c.stringWidth(line + word, FONT_NAME, 12) < width - 100:
                line += word + " "
            else:
                lines.append(line)
                line = word + " "
        lines.append(line)

        for line in lines:
            if y < 100:
                c.showPage()
                self._draw_background(c, width, height)
                self._draw_decorative_frame(c, width, height)
                y = height - 50
            c.drawString(50, y, line)
            y -= 20

        c.setFont(FONT_NAME, 9)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, 40, "🔮 Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!")
        c.drawCentredString(width/2, 25, f"Сгенерировано AstroBot • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        c.save()
        return filename

pdf_gen = ProfessionalPDFGenerator()