import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / 'astro.db'
BACKUP_DIR = BASE_DIR / 'backups'

def create_backup():
    """Создает бэкап базы данных"""
    try:
        if not DB_PATH.exists():
            logger.warning(f"База данных не найдена: {DB_PATH}")
            return False
        
        BACKUP_DIR.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = BACKUP_DIR / f'astro_backup_{timestamp}.db'
        
        shutil.copy2(DB_PATH, backup_file)
        logger.info(f"✅ Бэкап создан: {backup_file.name}")
        
        # Удаляем старые бэкапы (оставляем последние 10)
        backups = sorted(BACKUP_DIR.glob('astro_backup_*.db'))
        if len(backups) > 10:
            for old in backups[:-10]:
                old.unlink()
                logger.info(f"🗑️ Удален старый бэкап: {old.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return False