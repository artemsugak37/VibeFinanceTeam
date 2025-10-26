from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from classificator import SpendingClassifierAgent
from psychologist_agent import FinancialPsychologistAgent

class SpendingState(TypedDict):
    description: str
    amount: float
    main_category: str
    psych_category: str
    advice: str

classifier = SpendingClassifierAgent()
psychologist = FinancialPsychologistAgent()

def classify_spending(state: SpendingState) -> dict:
    raw = classifier.classify(state["description"])
    if " | " not in raw:
        raise ValueError(f"Неверный формат классификации: {raw}")
    main, psych = map(str.strip, raw.split(" | ", 1))
    return {"main_category": main, "psych_category": psych}

def generate_psych_advice(state: SpendingState) -> dict:
    advice = psychologist.advise(state["description"], state["psych_category"])
    return {"advice": advice}

# Строим граф
workflow = StateGraph(SpendingState)

workflow.add_node("classify", classify_spending)
workflow.add_node("advise", generate_psych_advice)

workflow.add_edge(START, "classify")
workflow.add_edge("classify", "advise")
workflow.add_edge("advise", END)

spending_graph = workflow.compile()