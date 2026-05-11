import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
ADMINS = [int(os.getenv('ADMIN_ID', 1079935212))]

# PostgreSQL параметры (для Supabase)
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'postgres')
# Настройки n1n.ai
N1N_API_KEY = os.getenv('N1N_API_KEY', OPENROUTER_API_KEY)
N1N_BASE_URL = 'https://api.n1n.ai/v1'
N1N_MODEL = 'gpt-4o-mini'

# Для обратной совместимости
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
OPENROUTER_MODEL = 'google/gemini-2.0-flash-exp:free'