#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сбора кода проекта astrobot в один файл.
Запустите эту программу в корневой папке проекта.
"""

import os
import sys
from pathlib import Path

# Папки и файлы, которые нужно исключить
EXCLUDE_DIRS = {
    '__pycache__', 'venv', 'env', '.venv', '.env', 
    'node_modules', '.git', '.idea', '.vscode',
    'fonts', 'static', 'database'  # статические и бинарные данные
}

EXCLUDE_FILES = {
    '.gitignore', 'восстоновлене баззы данных.txt',
    '2.3.0', '26.0.1', 'Build', 'Checking', 'Cloning', 'Common',
    'Docs', 'Downloaded', 'Downloading', 'Exited', 'Installing',
    'Running', 'Setting', 'Uploaded', 'Uploading', 'Using',
    '*.pyc', '*.pyo', '*.so', '*.dll', '*.exe', '*.db', '*.sqlite'
}

# Ключевые файлы, которые нужно собрать в первую очередь (основная логика)
PRIORITY_FILES = [
    'webhook_bot.py',
    'astrology_calculator.py', 
    'states.py',
    'config.py',
    'scheduler.py',
    'loader.py',
    'backup_db.py',
    'ai_service_fixed.py',
    'requirements.txt',
    'render.yaml'
]

# Папки с кодом для рекурсивного сбора
CODE_DIRS = ['handlers', 'keyboards', 'services', 'utils']

def should_include_file(filepath):
    """Проверяет, нужно ли включать файл"""
    name = os.path.basename(filepath)
    
    # Исключаем бинарные файлы и служебные
    if name.startswith('.') or name.endswith('.pyc') or name.endswith('.pyo'):
        return False
    if name in EXCLUDE_FILES:
        return False
    
    # Включаем только .py и .txt, .yaml файлы
    return name.endswith(('.py', '.txt', '.yaml', '.yml'))

def collect_file_content(filepath, root_dir):
    """Читает содержимое файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Относительный путь для вывода
        rel_path = os.path.relpath(filepath, root_dir)
        return f"\n{'='*80}\n# ФАЙЛ: {rel_path}\n{'='*80}\n{content}\n"
    except Exception as e:
        return f"\n# ОШИБКА при чтении {filepath}: {e}\n"

def main():
    # Определяем корневую папку (там, откуда запущен скрипт)
    root_dir = os.getcwd()
    print(f"🔍 Сканирую проект в: {root_dir}")
    
    output_content = []
    output_content.append("#" * 80)
    output_content.append("# АРХИВ КОДА ПРОЕКТА ASTROBOT")
    output_content.append("#" * 80)
    output_content.append(f"# Корневая папка: {root_dir}")
    output_content.append("#" * 80)
    
    # 1. Собираем приоритетные файлы из корня
    print("\n📁 Собираю основные файлы...")
    for filename in PRIORITY_FILES:
        filepath = os.path.join(root_dir, filename)
        if os.path.isfile(filepath):
            output_content.append(collect_file_content(filepath, root_dir))
            print(f"   ✅ {filename}")
        else:
            print(f"   ⚠️ {filename} (не найден)")
    
    # 2. Собираем файлы из папок с кодом
    for code_dir in CODE_DIRS:
        dirpath = os.path.join(root_dir, code_dir)
        if not os.path.isdir(dirpath):
            print(f"   ⚠️ Папка {code_dir} не найдена")
            continue
        
        print(f"\n📁 Сканирую папку {code_dir}/...")
        for root, dirs, files in os.walk(dirpath):
            # Исключаем ненужные папки
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                filepath = os.path.join(root, file)
                if should_include_file(filepath):
                    output_content.append(collect_file_content(filepath, root_dir))
                    print(f"   ✅ {os.path.relpath(filepath, root_dir)}")
    
    # 3. Дополнительно собираем все .py файлы из корня (кроме уже собранных)
    print("\n📁 Собираю остальные .py файлы из корня...")
    for file in os.listdir(root_dir):
        filepath = os.path.join(root_dir, file)
        if os.path.isfile(filepath) and file.endswith('.py'):
            if file not in PRIORITY_FILES:
                output_content.append(collect_file_content(filepath, root_dir))
                print(f"   ✅ {file}")
    
    # Записываем результат
    output_file = os.path.join(root_dir, 'PROJECT_CODE.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(output_content))
    
    # Статистика
    total_size = os.path.getsize(output_file)
    print("\n" + "="*80)
    print(f"✅ ГОТОВО! Файл создан: {output_file}")
    print(f"📊 Размер файла: {total_size:,} байт ({total_size/1024:.1f} КБ)")
    print(f"📄 Скопируйте содержимое этого файла и вставьте в чат с ассистентом.")
    print("="*80)

if __name__ == "__main__":
    main()