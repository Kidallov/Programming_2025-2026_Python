# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

def myfoo():
    """Основная функция модуля"""
    author = "Kidalov Aleksandr"  # Это место для указания своего имени (авторство модуля)
    print(f"{author}'s module is imported")
    return author

def add_numbers(a, b):
    """Пример математической операции"""
    return a + b

def get_version():
    """Возвращает версию модуля"""
    return "1.0"

if __name__ == "__main__":
    # Тестовый запуск при прямом выполнении файла
    myfoo()
