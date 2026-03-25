import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
ADMINS = [int(os.getenv('ADMIN_ID', 0))]
DB_PATH = 'astro.db'

# Настройки n1n.ai
N1N_API_KEY = os.getenv('N1N_API_KEY', OPENROUTER_API_KEY)
N1N_BASE_URL = 'https://api.n1n.ai/v1'
N1N_MODEL = 'gpt-4o-mini'

# Для обратной совместимости
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
OPENROUTER_MODEL = 'google/gemini-2.0-flash-exp:free'

# Веб-хук URL
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://astrobot-spui.onrender.com')