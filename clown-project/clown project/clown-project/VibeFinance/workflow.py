# workflow.py

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from classificator import SpendingClassifierAgent
from psychologist_agent import FinancialPsychologistAgent

# Обновлённый State
class SpendingState(TypedDict):
    # Входные данные
    user_id: int
    original_description: str # <-- Вместо message
    # Данные из GigaChat
    amount: float # <-- Теперь извлекается из GigaChat
    main_category: str
    psych_category: str
    parsed_description: str # <-- Новое поле
    parsed_date: str # <-- Новое поле, формат ISO
    confidence: float # <-- Новое поле
    # Результат психолога
    advice: str
    # Для сохранения в БД (опционально, можно и в app.py)
    timestamp: str # <-- Дата сохранения, если parsed_date null

classifier = SpendingClassifierAgent()
psychologist = FinancialPsychologistAgent()

def classify_spending(state: SpendingState) -> dict:
    # Передаём original_description (раньше это был message)
    result = classifier.classify(state["original_description"])

    # Извлекаем данные из JSON-ответа
    amount = result.get("amount")
    if amount is None:
        # Если GigaChat не нашёл сумму, можно бросить ошибку или использовать 0.0
        # Пока бросим ошибку, чтобы app.py мог обработать
        raise ValueError(f"GigaChat не смог извлечь сумму из описания: {state['original_description']}")
    # Проверим, что amount - число
    if not isinstance(amount, (int, float)):
        raise ValueError(f"GigaChat вернул некорректную сумму: {amount}")

    # Извлекаем дату
    parsed_date = result.get("parsed_date")
    if parsed_date is None:
        # Если GigaChat не нашёл дату, используем текущую (как в app.py)
        from datetime import datetime
        parsed_date = datetime.now().isoformat() # Формат ISO для БД

    # Извлекаем остальные поля
    main_category = result.get("main_category")
    psych_category = result.get("psych_category")
    parsed_description = result.get("parsed_description")
    confidence = result.get("confidence")

    # Проверим, что категории не None (на случай сбоя в GigaChat)
    if not main_category or not psych_category:
         raise ValueError(f"GigaChat вернул некорректные категории: main={main_category}, psych={psych_category}")

    # Возвращаем словарь с обновлёнными полями
    return {
        "amount": float(amount),
        "main_category": main_category,
        "psych_category": psych_category,
        "parsed_description": parsed_description,
        "parsed_date": parsed_date,
        "confidence": confidence,
        "original_description": result.get("original_description") # <-- Сохраняем оригинал
    }


def generate_psych_advice(state: SpendingState) -> dict:
    # Используем parsed_description или original_description для совета
    description_for_advice = state.get("parsed_description") or state.get("original_description")
    advice = psychologist.advise(description_for_advice, state["psych_category"])
    return {"advice": advice}

# Строим граф
workflow = StateGraph(SpendingState)

workflow.add_node("classify", classify_spending)
workflow.add_node("advise", generate_psych_advice)

workflow.add_edge(START, "classify")
workflow.add_edge("classify", "advise")
workflow.add_edge("advise", END)

spending_graph = workflow.compile()
