# tests/create_dataset.py
from langsmith import Client
from dotenv import load_dotenv
import os
load_dotenv()
# Импортируем данные из test_data.py
from test_data import test_examples

DATASET_NAME = "intent-router-100"

def create_dataset():
    client = Client()

    # Удалим старый датасет (если есть)
    try:
        client.delete_dataset(dataset_name=DATASET_NAME)
        print(f"Удалён существующий датасет: {DATASET_NAME}")
    except Exception as e:
        pass

    # Создаём новый
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="100 тестов для агента-роутера интентов (финансы, русский язык)"
    )
    print(f"✅ Создан датасет: {DATASET_NAME}")

    # Добавляем примеры
    for i, example in enumerate(test_examples):
        client.create_example(
            inputs={"message": example["input"]},
            outputs={"intent": example["intent"]},
            dataset_id=dataset.id
        )
        if (i + 1) % 10 == 0:
            print(f"Добавлено {i + 1} примеров...")

    print(f"🎉 Загружено {len(test_examples)} примеров в LangSmith.")

if __name__ == "__main__":
    create_dataset()