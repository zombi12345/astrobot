def md2_escape(text: str) -> str:
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
    return text.replace('*', '').replace('_', '').replace('`', '')