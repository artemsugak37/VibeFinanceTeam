#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы классификатора трат
"""

import os
from dotenv import load_dotenv
from classificator import SpendingClassifierAgent

def test_classifier():
    """Тестирует работу классификатора"""
    print("=== Тест классификатора трат ===")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие учетных данных
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    print(f"GIGACHAT_CREDENTIALS доступны: {bool(credentials)}")
    
    if not credentials:
        print("❌ Ошибка: GIGACHAT_CREDENTIALS не установлены в .env файле")
        return False
    
    try:
        # Создаем экземпляр классификатора
        print("\n🔧 Инициализация классификатора...")
        classifier = SpendingClassifierAgent()
        print("✅ Классификатор успешно инициализирован")
        
        # Тестовые примеры
        test_cases = [
            "Купил кофе и круассан в Starbucks",
            "Оплатил проездной на месяц",
            "Заправил полный бак бензина",
            "Купил лекарства в аптеке"
        ]
        
        print("\n🧪 Тестирование классификации...")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nТест {i}: '{test_case}'")
            try:
                result = classifier.classify(test_case)
                print(f"Результат: '{result}'")
                
                if " | " in result:
                    main_cat, psych_cat = map(str.strip, result.split(" | ", 1))
                    print(f"✅ Основная категория: '{main_cat}'")
                    print(f"✅ Психологическая категория: '{psych_cat}'")
                else:
                    print(f"❌ Неверный формат ответа: отсутствует разделитель ' | '")
                    
            except Exception as e:
                print(f"❌ Ошибка при классификации: {e}")
                return False
        
        print("\n🎉 Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации классификатора: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_classifier()
    exit(0 if success else 1)





