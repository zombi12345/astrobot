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

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
FONT_BOLD_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans-Bold.ttf')
BACKGROUND_PATH = os.path.join(BASE_DIR, 'static', 'background.jpg')

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))
    FONT_NAME = 'DejaVuSans'
    logger.info(f"✅ Шрифт загружен")
else:
    FONT_NAME = 'Helvetica'

if os.path.exists(FONT_BOLD_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_BOLD_PATH))
    FONT_BOLD_NAME = 'DejaVuSans-Bold'
    logger.info(f"✅ Жирный шрифт загружен")
else:
    FONT_BOLD_NAME = 'Helvetica-Bold'

TEXT_WHITE = HexColor('#FFFFFF')
TEXT_GOLD = HexColor('#FFD700')
TEXT_LIGHT = HexColor('#F0F0F0')

class ProfessionalPDFGenerator:
    def _draw_background(self, c, width, height):
        if os.path.exists(BACKGROUND_PATH):
            try:
                bg = ImageReader(BACKGROUND_PATH)
                c.drawImage(bg, 0, 0, width=width, height=height,
                           preserveAspectRatio=True, mask='auto')
                c.setFillColor(black)
                c.setFillAlpha(0.3)
                c.rect(0, 0, width, height, fill=1)
                c.setFillAlpha(1.0)
                return
            except:
                pass
        c.setFillColor(HexColor('#1a2a3a'))
        c.rect(0, 0, width, height, fill=1)

    def _draw_decorative_frame(self, c, width, height):
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(2)
        c.rect(20, 20, width-40, height-40, stroke=1, fill=0)
        c.setStrokeColor(TEXT_LIGHT)
        c.setLineWidth(1)
        c.rect(25, 25, width-50, height-50, stroke=1, fill=0)

    def _draw_header(self, c, width, height, title, subtitle=None):
        c.setFont(FONT_BOLD_NAME, 28)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width/2, height-60, title)
        if subtitle:
            c.setFont(FONT_NAME, 16)
            c.setFillColor(TEXT_LIGHT)
            c.drawCentredString(width/2, height-90, subtitle)
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1.5)
        c.line(width/4, height-100, width*3/4, height-100)

    def create_natal_chart_report_pdf(self, data):
        filename = f"natal_report_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        self._draw_background(c, width, height)
        self._draw_decorative_frame(c, width, height)
        self._draw_header(c, width, height, "Натальная карта", data.get('user_name', 'Пользователь'))
        y = height - 150
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ДАННЫЕ РОЖДЕНИЯ")
        y -= 25
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_WHITE)
        c.drawString(70, y, f"Дата: {data.get('birth_date', 'N/A')}")
        y -= 20
        c.drawString(70, y, f"Время: {data.get('birth_time', 'N/A')}")
        y -= 20
        c.drawString(70, y, f"Место: {data.get('birth_place', 'N/A')}")
        y -= 40
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ОСНОВНЫЕ ХАРАКТЕРИСТИКИ")
        y -= 25
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_WHITE)
        c.drawString(70, y, f"Солнце в знаке: {data.get('sun_sign', 'N/A')}")
        y -= 20
        c.drawString(70, y, f"Стихия: {data.get('element', 'N/A')}")
        y -= 20
        c.drawString(70, y, f"Качество: {data.get('quality', 'N/A')}")
        y -= 20
        c.drawString(70, y, f"Асцендент: {data.get('ascendant', 'N/A')}")
        y -= 40
        c.setFont(FONT_BOLD_NAME, 14)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ПОЛОЖЕНИЕ ПЛАНЕТ")
        y -= 25
        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_WHITE)
        for planet in data.get('planets', []):
            retro = " (ретроградный)" if planet.get('retrograde') else ""
            c.drawString(70, y, f"{planet['symbol']} {planet['name']}: {planet['sign']} ({planet['house']} дом){retro}")
            y -= 18
        c.save()
        return filename

pdf_gen = ProfessionalPDFGenerator()