import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
ADMINS = [int(os.getenv('ADMIN_ID', 0))]
DB_PATH = 'astro.db'

OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
OPENROUTER_MODEL = 'gpt-4o-mini'

# Веб-хук URL — будет установлен автоматически на Render
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://astrobot-spui.onrender.com')