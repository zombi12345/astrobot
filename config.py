import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
# Меняем OpenRouter на n1n.ai
N1N_API_KEY = os.getenv('N1N_API_KEY')  # Добавьте в .env
ADMINS = [int(os.getenv('ADMIN_ID', 0))]
DB_PATH = 'astro.db'

# Настройки n1n.ai
N1N_BASE_URL = 'https://api.n1n.ai/v1'
N1N_MODEL = 'gpt-4o-mini'  # или 'claude-3-sonnet', 'gemini-1.5-pro'