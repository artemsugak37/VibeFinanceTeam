# tests/test_router.py
from dotenv import load_dotenv
load_dotenv()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from langsmith.evaluation import evaluate
from intent_router import IntentRouterAgent

DATASET_NAME = "intent-router-100"

# Глобальный список для сбора результатов (не идеально, но просто)
test_results = []

def predict(inputs: dict) -> dict:
    agent = IntentRouterAgent()
    intent = agent.route(inputs["message"])
    time.sleep(0.12)  # избегаем 429
    test_results.append((inputs["message"], intent))
    return {"intent": intent}

def exact_match(run, example) -> dict:
    predicted = run.outputs.get("intent", "").strip().lower()
    expected = example.outputs.get("intent", "").strip().lower()
    score = int(predicted == expected)
    return {"score": score, "key": "exact_match"}

def run_evaluation():
    print("🚀 Запуск тестов через LangSmith (с паузой)...")
    global test_results
    test_results.clear()  # очищаем перед запуском

    # Запускаем evaluate — данные пойдут в LangSmith
    list(evaluate(
        predict,
        data=DATASET_NAME,
        evaluators=[exact_match],
        description="Тестирование агента-роутера (100 примеров)"
    ))

    # Теперь получим ожидаемые значения из LangSmith Dataset
    from langsmith import Client
    client = Client()
    examples = list(client.list_examples(dataset_name=DATASET_NAME))
    
    if len(test_results) != len(examples):
        print("⚠️ Предупреждение: несовпадение количества примеров")
        return

    # Сравниваем
    passed = 0
    errors = []
    for i, ((message, predicted), example) in enumerate(zip(test_results, examples)):
        expected = example.outputs["intent"]
        if predicted == expected:
            passed += 1
        else:
            errors.append(f"{i+1}. '{message}' → ожидалось: '{expected}', получено: '{predicted}'")

    total = len(test_results)
    print(f"\n{'='*60}")
    print(f"✅ Успешно:  {passed}")
    print(f"❌ Ошибок:   {total - passed}")
    print(f"📈 Точность: {passed / total:.1%}")
    print(f"{'='*60}")

    if errors:
        print("\n🔍 Первые 5 ошибок:")
        for err in errors[:5]:
            print(f"  {err}")

if __name__ == "__main__":
    run_evaluation()