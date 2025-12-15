# tests/create_dataset_spending.py
from langsmith import Client
from dotenv import load_dotenv
import os

load_dotenv()

# Импортируем данные из test_data_spending.py
from test_data_spending import test_examples

DATASET_NAME = "spending-classifier-100"

def create_dataset():
    client = Client()

    # Удалим старый датасет (если есть)
    try:
        client.delete_dataset(dataset_name=DATASET_NAME)
        print(f"Удалён существующий датасет: {DATASET_NAME}")
    except Exception:
        pass  # Игнорируем, если датасета нет

    # Создаём новый датасет
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="100+ тестов для SpendingClassifierAgent: основная и психологическая категоризация русскоязычных трат"
    )
    print(f"✅ Создан датасет: {DATASET_NAME}")

    # Добавляем примеры
    for i, example in enumerate(test_examples):
        client.create_example(
            inputs={"spending_text": example["input"]},
            outputs={
                "main_category": example["main_category"],
                "psych_category": example["psych_category"]
            },
            dataset_id=dataset.id
        )
        if (i + 1) % 10 == 0:
            print(f"Добавлено {i + 1} примеров...")

    print(f"🎉 Загружено {len(test_examples)} примеров в LangSmith.")

if __name__ == "__main__":
    create_dataset()