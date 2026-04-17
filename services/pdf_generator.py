import os
import uuid
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
FONT_BOLD_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans-Bold.ttf')

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
    def create_natal_chart_pdf(self, chart_data: dict) -> str:
        """Создаёт PDF-отчёт на основе уже рассчитанных данных натальной карты"""
        filename = f"natal_report_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Фон
        c.setFillColor(BG_DARK)
        c.rect(0, 0, width, height, fill=1)
        
        # Декоративная рамка
        c.setStrokeColor(ACCENT_PURPLE)
        c.setLineWidth(2)
        c.rect(20, 20, width-40, height-40)
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1)
        c.rect(25, 25, width-50, height-50)
        
        # Заголовок
        c.setFont(FONT_BOLD_NAME, 26)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width/2, height-50, "✨ НАТАЛЬНАЯ КАРТА ✨")
        
        # Данные пользователя
        info = chart_data['birth_info']
        c.setFont(FONT_BOLD_NAME, 16)
        c.setFillColor(TEXT_WHITE)
        c.drawCentredString(width/2, height-85, info['name'])
        
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, height-105, f"{info['date']} в {info['time']} | {info['place']}")
        
        # Линия
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
        c.drawString(70, y, f"☉ Солнце в знаке: {chart_data['sun_sign']}")
        y -= 20
        c.drawString(70, y, f"🌊 Стихия: {chart_data['element']}")
        y -= 20
        c.drawString(70, y, f"⚡ Качество: {chart_data['quality']}")
        y -= 20
        c.drawString(70, y, f"⬆ Асцендент (ASC): {chart_data['ascendant']}")
        y -= 40
        
        # Планеты
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ПОЛОЖЕНИЕ ПЛАНЕТ")
        y -= 25
        
        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_WHITE)
        
        left_x = 70
        right_x = 350
        planets = chart_data['planets']
        half = len(planets) // 2 + len(planets) % 2
        
        for i, planet in enumerate(planets[:half]):
            retro = " (ретроградный)" if planet.get('retrograde') else ""
            c.drawString(left_x, y, f"{planet['symbol']} {planet['name']}: {planet['sign']} ({planet['house']} дом){retro}")
            y -= 18
        
        y_temp = height - 160 - 25 - 18 * half
        for i, planet in enumerate(planets[half:]):
            retro = " (ретроградный)" if planet.get('retrograde') else ""
            c.drawString(right_x, y_temp, f"{planet['symbol']} {planet['name']}: {planet['sign']} ({planet['house']} дом){retro}")
            y_temp -= 18
        
        y = height - 160 - 25 - 18 * half - 40
        
        # Аспекты
        if chart_data.get('aspects'):
            c.setFont(FONT_BOLD_NAME, 14)
            c.setFillColor(TEXT_GOLD)
            c.drawString(50, y, "АСПЕКТЫ ПЛАНЕТ")
            y -= 25
            c.setFont(FONT_NAME, 10)
            c.setFillColor(TEXT_WHITE)
            for asp in chart_data['aspects'][:10]:
                c.drawString(70, y, f"{asp['planet1']} {asp['aspect']} {asp['planet2']} — {asp['name']} ({asp['angle']}°, орбис {asp['orbis']}°)")
                y -= 15
            y -= 15
        
        # Дома
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "АСТРОЛОГИЧЕСКИЕ ДОМА")
        y -= 25
        
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_WHITE)
        houses = chart_data['houses']
        col_width = 100
        for i, house in enumerate(houses):
            col = i % 4
            row = i // 4
            x = 50 + col * col_width
            y_pos = y - row * 18
            c.drawString(x, y_pos, f"{house['number']} дом: {house['sign']}")
        
        y = y - 8 * 18 - 40
        
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
        interp = interpretations.get(chart_data['sun_sign'], 'у вас уникальная личность.')
        c.drawString(70, y, f"☉ Солнце в {chart_data['sun_sign']}: {interp}")
        
        # Нижний колонтитул
        c.setFont(FONT_NAME, 9)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(width/2, 40, "🔮 Астрология — это инструмент самопознания. Звёзды указывают путь, но выбор всегда за вами!")
        c.drawCentredString(width/2, 25, f"Сгенерировано AstroBot • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        c.save()
        return filename

pdf_gen = ProfessionalPDFGenerator()