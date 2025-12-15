import os
import uuid
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
from classificator import SpendingClassifierAgent

# Загрузка .env
load_dotenv()

# === Тестовые кейсы ===

test_cases = [
    # 1–5: уже были
    {"input": {"spending_text": "Купил кофе и круассан в Starbucks за 180 рублей вчера"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Оплатил абонемент в зал на 3000 рублей"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Билеты в кино на двоих — 1200 рублей"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил новую куртку за 7500"}, "expected": {"main_category": "Одежда", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил интернет за месяц"}, "expected": {"main_category": "Связь", "psych_category": "Необходимость"}},

    # 6–20: Еда
    {"input": {"spending_text": "Сходил в McDonald's на обед"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил продукты в Пятёрочке на неделю"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Заказал пиццу домой вечером"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил бутылку воды в метро"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Побаловал себя десертом в кофейне"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил овощи и фрукты на рынке"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Сходил на бизнес-ланч"}, "expected": {"main_category": "Еда", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Купил перекус в аэропорту"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Заказал роллы на ужин"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил завтрак в буфете на вокзале"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Устроил ужин при свечах в ресторане"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил молоко и хлеб"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Попробовал новый бургер в новом фастфуде"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил еду в столовой на работе"}, "expected": {"main_category": "Еда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Заказал доставку суши"}, "expected": {"main_category": "Еда", "psych_category": "Радость"}},

    # 21–30: Транспорт
    {"input": {"spending_text": "Купил проездной на метро на месяц"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Вызвал такси домой после вечеринки"}, "expected": {"main_category": "Транспорт", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Заправил машину полным баком"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Оплатил парковку в центре"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил билет на автобус до дачи"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Поехал на поезде в другой город"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Взял велосипед напрокат на день"}, "expected": {"main_category": "Транспорт", "psych_category": "Радость"}},
    {"input": {"spending_text": "Оплатил Яндекс.Такси до аэропорта"}, "expected": {"main_category": "Транспорт", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Купил билет на электричку"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Поставил новый аккумулятор в машину"}, "expected": {"main_category": "Транспорт", "psych_category": "Необходимость"}},

    # 31–40: Развлечения
    {"input": {"spending_text": "Купил игру в Steam со скидкой"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Сходил на концерт любимой группы"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Оплатил подписку на онлайн-кинотеатр"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил билеты в театр"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Посетил квест с друзьями"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил настольную игру"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Сходил на выставку современного искусства"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Оплатил вход в аквапарк"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил билет на фестиваль"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},
    {"input": {"spending_text": "Подписался на Twitch-донат любимому стримеру"}, "expected": {"main_category": "Развлечения", "psych_category": "Радость"}},

    # 41–50: Здоровье
    {"input": {"spending_text": "Купил лекарства от простуды"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Оплатил приём у стоматолога"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил витамины в аптеке"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Сделал МРТ по направлению"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил беговую дорожку для дома"}, "expected": {"main_category": "Здоровье", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Оплатил массаж после травмы"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил ортопедическую подушку"}, "expected": {"main_category": "Здоровье", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Сдал анализы в лаборатории"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил спортивное питание"}, "expected": {"main_category": "Здоровье", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Оплатил курс физиотерапии"}, "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}},

    # 51–60: Одежда
    {"input": {"spending_text": "Купил джинсы в магазине"}, "expected": {"main_category": "Одежда", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Заказал футболки с AliExpress"}, "expected": {"main_category": "Одежда", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Купил костюм к свадьбе друга"}, "expected": {"main_category": "Одежда", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Купил зимние ботинки"}, "expected": {"main_category": "Одежда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Заказал спортивную форму"}, "expected": {"main_category": "Одежда", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил шапку и перчатки"}, "expected": {"main_category": "Одежда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил вечернее платье"}, "expected": {"main_category": "Одежда", "psych_category": "Радость"}},
    {"input": {"spending_text": "Обновил гардероб к сезону"}, "expected": {"main_category": "Одежда", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Купил носки и бельё"}, "expected": {"main_category": "Одежда", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Заказал брендовые кроссовки"}, "expected": {"main_category": "Одежда", "psych_category": "Радость"}},

    # 61–70: Жилье
    {"input": {"spending_text": "Оплатил коммунальные за воду и свет"}, "expected": {"main_category": "Жилье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Внёс арендную плату за квартиру"}, "expected": {"main_category": "Жилье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил новую люстру в гостиную"}, "expected": {"main_category": "Жилье", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил ремонт сантехники"}, "expected": {"main_category": "Жилье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил шторы на окна"}, "expected": {"main_category": "Жилье", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил интернет для дома"}, "expected": {"main_category": "Жилье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил пылесос"}, "expected": {"main_category": "Жилье", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил вывоз мусора"}, "expected": {"main_category": "Жилье", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил диван для гостиной"}, "expected": {"main_category": "Жилье", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил капитальный ремонт дома"}, "expected": {"main_category": "Жилье", "psych_category": "Необходимость"}},

    # 71–80: Образование
    {"input": {"spending_text": "Записался на курсы анализа данных"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил учебник по финансовой грамотности"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Оплатил репетитора по математике"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил подписку на Coursera"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Оплатил вебинар по инвестициям"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил канцелярию к началу учебного года"}, "expected": {"main_category": "Образование", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Записал ребёнка на кружок робототехники"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Оплатил экзамен по английскому"}, "expected": {"main_category": "Образование", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил онлайн-курс по программированию"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Оплатил участие в конференции"}, "expected": {"main_category": "Образование", "psych_category": "Развитие"}},

    # 81–85: Связь
    {"input": {"spending_text": "Пополнил баланс телефона"}, "expected": {"main_category": "Связь", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Оплатил тарифный план на год"}, "expected": {"main_category": "Связь", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил новую SIM-карту"}, "expected": {"main_category": "Связь", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Оплатил роуминг за границей"}, "expected": {"main_category": "Связь", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Подключил дополнительный гигабайт трафика"}, "expected": {"main_category": "Связь", "psych_category": "Необходимость"}},

    # 86–100: Другое и неоднозначные кейсы
    {"input": {"spending_text": "Подарил цветы маме"}, "expected": {"main_category": "Другое", "psych_category": "Радость"}},
    {"input": {"spending_text": "Пожертвовал деньги на благотворительность"}, "expected": {"main_category": "Другое", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил подарок другу на день рождения"}, "expected": {"main_category": "Другое", "psych_category": "Радость"}},
    {"input": {"spending_text": "Оплатил штраф ГИБДД"}, "expected": {"main_category": "Другое", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил страховку на телефон"}, "expected": {"main_category": "Другое", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Оплатил госпошлину"}, "expected": {"main_category": "Другое", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Купил сувенир в поездке"}, "expected": {"main_category": "Другое", "psych_category": "Радость"}},
    {"input": {"spending_text": "Заплатил за доставку заказа"}, "expected": {"main_category": "Другое", "psych_category": "Необходимость"}},
    {"input": {"spending_text": "Оплатил подписку на музыку"}, "expected": {"main_category": "Другое", "psych_category": "Радость"}},
    {"input": {"spending_text": "Купил свечи для дома"}, "expected": {"main_category": "Другое", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил домена для сайта"}, "expected": {"main_category": "Другое", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил наушники"}, "expected": {"main_category": "Другое", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Заплатил за хостинг"}, "expected": {"main_category": "Другое", "psych_category": "Развитие"}},
    {"input": {"spending_text": "Купил часы"}, "expected": {"main_category": "Другое", "psych_category": "Комфорт"}},
    {"input": {"spending_text": "Оплатил онлайн-покупку без указания категории"}, "expected": {"main_category": "Другое", "psych_category": "Необходимость"}},

    {
        "input": {"spending_text": "Купил кофе и круассан в Starbucks за 180 рублей вчера"},
        "expected": {"main_category": "Еда", "psych_category": "Радость"}
    },
    {
        "input": {"spending_text": "Оплатил абонемент в зал на 3000 рублей"},
        "expected": {"main_category": "Здоровье", "psych_category": "Необходимость"}
    },
    {
        "input": {"spending_text": "Билеты в кино на двоих — 1200 рублей"},
        "expected": {"main_category": "Развлечения", "psych_category": "Радость"}
    },
    {
        "input": {"spending_text": "Купил новую куртку за 7500"},
        "expected": {"main_category": "Одежда", "psych_category": "Комфорт"}
    },
    {
        "input": {"spending_text": "Оплатил интернет за месяц"},
        "expected": {"main_category": "Связь", "psych_category": "Необходимость"}
    }
]

def predict(inputs: dict) -> dict:
    agent = SpendingClassifierAgent()
    result = agent.classify(inputs["spending_text"])
    return {
        "main_category": result.get("main_category"),
        "psych_category": result.get("psych_category"),
    }

# === Простой локальный прогон без langsmith.evaluate ===
if __name__ == "__main__":
    results = []
    total = len(test_cases)

    for case in test_cases:
        inputs = case["input"]
        expected = case["expected"]

        try:
            output = predict(inputs)
        except Exception as e:
            print(f"❌ Ошибка на входе '{inputs['spending_text']}': {e}")
            output = {"main_category": None, "psych_category": None}

        main_ok = output.get("main_category") == expected["main_category"]
        psych_ok = output.get("psych_category") == expected["psych_category"]

        results.append({
            "main_correct": main_ok,
            "psych_correct": psych_ok,
            "input": inputs["spending_text"],
            "output": output,
            "expected": expected
        })

    # Сводка
    main_passed = sum(1 for r in results if r["main_correct"])
    psych_passed = sum(1 for r in results if r["psych_correct"])

    print("\n" + "=" * 50)
    print(f"Итоги тестирования ({total} кейсов):")
    print(f"✅ Main category:  {main_passed}/{total} ({main_passed / total * 100:.1f}%)")
    print(f"✅ Psych category: {psych_passed}/{total} ({psych_passed / total * 100:.1f}%)")
    print("=" * 50)

    # Опционально: показать неудачные кейсы
    failed = [r for r in results if not r["main_correct"] or not r["psych_correct"]]
    if failed:
        print("\n❌ Неудачные кейсы:")
        for r in failed:
            print(f"  - Вход: {r['input']}")
            print(f"    Ожидалось: {r['expected']}")
            print(f"    Получено:  {r['output']}\n")