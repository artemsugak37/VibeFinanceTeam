# workflow.py
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from classificator import SpendingClassifierAgent
from psychologist_agent import FinancialPsychologistAgent
from intent_router import IntentRouterAgent
import sqlite3
from datetime import datetime

class SpendingState(TypedDict):
    user_id: int
    original_description: str
    intent: str
    amount: float | None
    main_category: str | None
    psych_category: str | None
    parsed_description: str | None
    parsed_date: str | None
    confidence: float | None
    advice: str

classifier = SpendingClassifierAgent()
psychologist = FinancialPsychologistAgent()
router = IntentRouterAgent()

def route_intent(state: SpendingState) -> dict:
    intent = router.route(state["original_description"])
    return {"intent": intent}

def should_suggest_goal(message: str, user_id: int) -> bool:
    goal_keywords = [
        "накопить", "цель", "мечта", "собрать на", "хочу", "хотел бы",
        "машина", "отпуск", "путешествие", "чёрный день", "подушка",
        "бюджет на", "финансовая цель", "план накоплений"
    ]
    has_keywords = any(kw in message.lower() for kw in goal_keywords)
    if not has_keywords:
        return False

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM goals WHERE user_id = ? AND is_active = 1', (user_id,))
    active_count = cursor.fetchone()[0]
    conn.close()

    return active_count < 5

def classify_spending(state: SpendingState) -> dict:
    # Вызывается ТОЛЬКО если intent == "spending"
    try:
        result = classifier.classify(state["original_description"])
        amount = result.get("amount")
        if amount is None:
            # Если сумма не найдена — всё равно не ошибка, просто не трата
            return {
                "amount": None,
                "main_category": None,
                "psych_category": None,
                "parsed_description": None,
                "parsed_date": None,
                "confidence": None
            }

        parsed_date = result.get("parsed_date") or datetime.now().isoformat()
        return {
            "amount": float(amount),
            "main_category": result.get("main_category"),
            "psych_category": result.get("psych_category"),
            "parsed_description": result.get("parsed_description"),
            "parsed_date": parsed_date,
            "confidence": result.get("confidence", 0.0)
        }
    except Exception as e:
        print(f"Classification error: {e}")
        return {
            "amount": None,
            "main_category": None,
            "psych_category": None,
            "parsed_description": None,
            "parsed_date": None,
            "confidence": None
        }

def generate_advice(state: SpendingState) -> dict:
    message = state["original_description"]
    user_id = state["user_id"]
    intent = state["intent"]

    # Определяем базовое сообщение
    if intent == "spending" and state.get("psych_category"):
        desc = state.get("parsed_description") or message
        base_advice = psychologist.advise(desc, state["psych_category"])
    else:
        base_advice = psychologist.respond_to_general_query(message)

    # Решаем, предлагать ли помощь с целью
    if intent in ("goal", "question") and should_suggest_goal(message, user_id):
        base_advice += "\n\n💡 Кстати, я могу помочь тебе составить пошаговый план, как накопить на это — просто скажи «да»!"

    return {"advice": base_advice}

def should_classify(state: SpendingState) -> str:
    return "classify" if state["intent"] == "spending" else "advise"

workflow = StateGraph(SpendingState)
workflow.add_node("route", route_intent)
workflow.add_node("classify", classify_spending)
workflow.add_node("advise", generate_advice)

workflow.add_edge(START, "route")
workflow.add_conditional_edges("route", should_classify, {"classify": "classify", "advise": "advise"})
workflow.add_edge("classify", "advise")
workflow.add_edge("advise", END)

spending_graph = workflow.compile()