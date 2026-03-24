def md2_escape(text: str) -> str:
    """Экранирование для MarkdownV2"""
    replacements = {
        '_': '\\_', '*': '\\*', '[': '\\[', ']': '\\]',
        '(': '\\(', ')': '\\)', '~': '\\~', '`': '\\`',
        '>': '\\>', '#': '\\#', '+': '\\+', '-': '\\-',
        '=': '\\=', '|': '\\|', '{': '\\{', '}': '\\}',
        '.': '\\.', '!': '\\!'
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text

def safe_text(text: str) -> str:
    """Безопасный текст без markdown"""
    return text.replace('*', '').replace('_', '').replace('`', '')