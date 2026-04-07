def create_natal_chart_report_pdf(self, data):
    """Создаёт PDF-отчёт натальной карты"""
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
# ... весь ваш код класса ProfessionalPDFGenerator ...

    def _draw_frame(self, c, width, height):
        # ... код метода ...

# Создаём глобальный экземпляр класса
pdf_gen = ProfessionalPDFGenerator()  # <--- ЭТА СТРОКА НУЖНА!