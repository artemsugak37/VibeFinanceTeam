# workflow.py
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from classificator import SpendingClassifierAgent
from psychologist_agent import FinancialPsychologistAgent
from intent_router import IntentRouterAgent
from llm_visualizer_agent import SpendingVisualizerAgent  
from savings_planner_agent import SavingsPlannerAgent

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

# Инициализация агентов
classifier = SpendingClassifierAgent()
psychologist = FinancialPsychologistAgent()
router = IntentRouterAgent()
visualizer = SpendingVisualizerAgent()
savings_planner = SavingsPlannerAgent()  # ← глобальный экземпляр

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

    try:
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM goals WHERE user_id = ? AND is_active = 1', (user_id,))
            active_count = cursor.fetchone()[0]
        return active_count < 5
    except Exception as e:
        print(f"Goal suggestion DB error: {e}")
        return False

def classify_spending(state: SpendingState) -> dict:
    """Вызывается ТОЛЬКО если intent == "spending"."""
    try:
        result = classifier.classify(state["original_description"])
        amount = result.get("amount")
        if amount is None:
            return {
                "amount": None,
                "main_category": None,
                "psych_category": None,
                "parsed_description": None,
                "parsed_date": None,
                "confidence": None
            }

        VALID_MAIN = {"Еда", "Транспорт", "Развлечения", "Здоровье", "Одежда", "Жилье", "Образование", "Связь", "Другое"}
        VALID_PSYCH = {"Радость", "Комфорт", "Развитие", "Необходимость"}

        main_cat = result.get("main_category")
        psych_cat = result.get("psych_category")

        if main_cat not in VALID_MAIN:
            main_cat = "Другое"
        if psych_cat not in VALID_PSYCH:
            psych_cat = "Необходимость"

        parsed_date = result.get("parsed_date") or datetime.now().isoformat()
        return {
            "amount": float(amount),
            "main_category": main_cat,
            "psych_category": psych_cat,
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

    try:
        if intent == "spending" and state.get("psych_category"):
            desc = state.get("parsed_description") or message
            advice = psychologist.advise(desc, state["psych_category"])
        elif intent == "goal":
            advice = savings_planner.generate_plan(message, user_id)
        elif intent == "goals":  # ← НОВОЕ: просмотр целей
            advice = savings_planner.get_user_goals(user_id)
        else:
            advice = psychologist.respond_to_general_query(message)
    except Exception as e:
        print(f"Advice generation error: {e}")
        import traceback
        traceback.print_exc()
        advice = "Спасибо за сообщение! Продолжай следить за своими финансами — ты на правильном пути."

    if intent == "question" and should_suggest_goal(message, user_id):
        advice += "\n\n💡 Кстати, я могу помочь тебе составить пошаговый план, как накопить на это — просто скажи «да»!"

    return {"advice": advice}

def generate_visualization(state: SpendingState) -> dict:
    """Генерирует HTML-таблицу и график для интента 'visualization'."""
    message = state["original_description"].lower()
    user_id = state["user_id"]

    if "месяц" in message or "month" in message:
        period = "month"
    elif "всё" in message or "все" in message or "all" in message:
        period = "all"
    else:
        period = "week"

    try:
        result = visualizer.generate_visualization(user_id, period)
        advice = f"""
📊 **Финансовая визуализация** за {'последнюю неделю' if period == 'week' else 'месяц' if period == 'month' else 'всё время'}:

{result['summary']}

{result['table_html']}

{'<br><img src="image/png;base64,' + result['chart_base64'] + '" style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if result['chart_base64'] else ''}
        """.strip()
    except Exception as e:
        print(f"Visualization error: {e}")
        advice = "Не удалось сгенерировать визуализацию. Попробуйте позже."

    return {"advice": advice}

# === ЛОГИКА ВЕТВЛЕНИЯ ===
def should_classify(state: SpendingState) -> str:
    intent = state["intent"]
    if intent == "spending":
        return "classify"
    elif intent == "visualization":
        return "visualize"
    else:
        return "advise"

# === ПОСТРОЕНИЕ ГРАФА ===
workflow = StateGraph(SpendingState)

workflow.add_node("route", route_intent)
workflow.add_node("classify", classify_spending)
workflow.add_node("advise", generate_advice)
workflow.add_node("visualize", generate_visualization)

workflow.add_edge(START, "route")
workflow.add_conditional_edges(
    "route",
    should_classify,
    {
        "classify": "classify",
        "visualize": "visualize",
        "advise": "advise"
    }
)
workflow.add_edge("classify", "advise")
workflow.add_edge("visualize", END)
workflow.add_edge("advise", END)

spending_graph = workflow.compile()