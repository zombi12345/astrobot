import matplotlib
matplotlib.use('Agg')  # Используем без GUI
import matplotlib.pyplot as plt
import uuid
import os
from datetime import datetime, timedelta
import aiosqlite
from config import DB_PATH
import logging

logger = logging.getLogger(__name__)

class StatisticsGenerator:
    async def generate_users_chart(self):
        """Генерирует график регистраций за последние 30 дней"""
        try:
            plt.figure(figsize=(12, 6))
            
            # Получаем данные
            async with aiosqlite.connect(DB_PATH) as db:
                dates = []
                counts = []
                
                for i in range(30, -1, -1):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    next_date = (datetime.now() - timedelta(days=i-1)).strftime('%Y-%m-%d') if i > 0 else datetime.now().strftime('%Y-%m-%d')
                    
                    cur = await db.execute(
                        "SELECT COUNT(*) FROM users WHERE created_at BETWEEN ? AND ?",
                        (date, next_date)
                    )
                    count = (await cur.fetchone())[0]
                    
                    dates.append(date[5:])  # ММ-ДД
                    counts.append(count)
            
            # Строим график
            plt.plot(dates, counts, 'o-', color='#FFD700', linewidth=2, markersize=6)
            plt.fill_between(dates, counts, alpha=0.3, color='#FFD700')
            
            plt.title('Регистрации пользователей', color='white', fontsize=14, pad=20)
            plt.xlabel('Дата', color='white')
            plt.ylabel('Новых пользователей', color='white')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.style.use('dark_background')
            
            filename = f"chart_{uuid.uuid4().hex}.png"
            plt.tight_layout()
            plt.savefig(filename, facecolor='#1a2a3a', dpi=100)
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка генерации графика: {e}")
            return None
    
    async def generate_activity_chart(self):
        """Генерирует график активности за последние 30 дней"""
        try:
            plt.figure(figsize=(12, 6))
            
            async with aiosqlite.connect(DB_PATH) as db:
                dates = []
                counts = []
                
                for i in range(30, -1, -1):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    next_date = (datetime.now() - timedelta(days=i-1)).strftime('%Y-%m-%d') if i > 0 else datetime.now().strftime('%Y-%m-%d')
                    
                    cur = await db.execute(
                        "SELECT COUNT(*) FROM requests WHERE created_at BETWEEN ? AND ?",
                        (date, next_date)
                    )
                    count = (await cur.fetchone())[0]
                    
                    dates.append(date[5:])
                    counts.append(count)
            
            plt.bar(dates, counts, color='#FFD700', alpha=0.7)
            plt.title('Активность пользователей', color='white', fontsize=14, pad=20)
            plt.xlabel('Дата', color='white')
            plt.ylabel('Количество запросов', color='white')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
            plt.style.use('dark_background')
            
            filename = f"chart_{uuid.uuid4().hex}.png"
            plt.tight_layout()
            plt.savefig(filename, facecolor='#1a2a3a', dpi=100)
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка генерации графика активности: {e}")
            return None
    
    async def generate_subscription_chart(self):
        """Генерирует график подписок"""
        try:
            plt.figure(figsize=(10, 6))
            
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_paid = 1")
                paid = (await cur.fetchone())[0]
                
                cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_paid = 0")
                free = (await cur.fetchone())[0]
            
            labels = ['Премиум', 'Бесплатные']
            sizes = [paid, free]
            colors = ['#FFD700', '#4a5568']
            explode = (0.05, 0)
            
            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                    autopct='%1.1f%%', shadow=True, startangle=90)
            plt.title('Распределение пользователей по подпискам', color='white', fontsize=14, pad=20)
            plt.style.use('dark_background')
            
            filename = f"chart_{uuid.uuid4().hex}.png"
            plt.tight_layout()
            plt.savefig(filename, facecolor='#1a2a3a', dpi=100)
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка генерации графика подписок: {e}")
            return None
    
    async def generate_comprehensive_report(self):
        """Создает полный отчет"""
        chart_users = await self.generate_users_chart()
        chart_activity = await self.generate_activity_chart()
        chart_subs = await self.generate_subscription_chart()
        
        return {
            'users_chart': chart_users,
            'activity_chart': chart_activity,
            'subscription_chart': chart_subs
        }

stats_gen = StatisticsGenerator()