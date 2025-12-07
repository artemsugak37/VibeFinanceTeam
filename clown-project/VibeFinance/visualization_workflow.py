# visualization_workflow.py
"""
LangGraph workflow для связи аналитика (weekly_report_agent) и визуализатора (visualization_agent).
Это часть мультиагентной системы на LangGraph и LangChain.
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from weekly_report_agent import WeeklyReportAgent
from visualization_agent import VisualizationAgent

class VisualizationState(TypedDict):
    """Состояние для workflow визуализации."""
    user_id: int
    request_type: str  # "weekly_report" | "visualization" | "both"
    analyst_data: dict | None
    visualization_data: dict | None
    report_text: str | None
    error: str | None

# Инициализация агентов
analyst = WeeklyReportAgent()
visualizer = VisualizationAgent()

def get_analyst_data(state: VisualizationState) -> dict:
    """
    Узел: получение данных от аналитика (weekly_report_agent).
    """
    try:
        user_id = state["user_id"]
        analyst_data = analyst.get_weekly_report_data(user_id)
        return {
            "analyst_data": analyst_data,
            "error": None
        }
    except Exception as e:
        return {
            "analyst_data": None,
            "error": f"Ошибка аналитика: {str(e)}"
        }

def generate_visualization(state: VisualizationState) -> dict:
    """
    Узел: генерация визуализации на основе данных аналитика.
    """
    try:
        analyst_data = state.get("analyst_data")
        if not analyst_data:
            return {
                "visualization_data": None,
                "error": "Нет данных от аналитика"
            }
        
        visualization_data = visualizer.generate_visualization_data(analyst_data)
        return {
            "visualization_data": visualization_data,
            "error": None
        }
    except Exception as e:
        return {
            "visualization_data": None,
            "error": f"Ошибка визуализатора: {str(e)}"
        }

def generate_report_text(state: VisualizationState) -> dict:
    """
    Узел: генерация текстового отчёта на основе данных аналитика.
    """
    try:
        analyst_data = state.get("analyst_data")
        if not analyst_data:
            return {
                "report_text": "Нет данных для формирования отчёта",
                "error": None
            }
        
        # Используем метод format_report_text для форматирования уже полученных данных
        report_text = analyst.format_report_text(analyst_data)
        return {
            "report_text": report_text,
            "error": None
        }
    except Exception as e:
        return {
            "report_text": None,
            "error": f"Ошибка генерации отчёта: {str(e)}"
        }

def should_visualize(state: VisualizationState) -> str:
    """
    Условное ветвление: определяет, нужно ли генерировать визуализацию.
    """
    request_type = state.get("request_type", "both")
    
    if request_type == "visualization" or request_type == "both":
        return "visualize"
    else:
        return "report_only"

def should_generate_report(state: VisualizationState) -> str:
    """
    Условное ветвление: определяет, нужно ли генерировать текстовый отчёт.
    """
    request_type = state.get("request_type", "both")
    
    if request_type == "weekly_report" or request_type == "both":
        return "generate_report"
    else:
        return "end"

# Создание графа workflow
visualization_workflow = StateGraph(VisualizationState)

# Добавление узлов
visualization_workflow.add_node("get_analyst_data", get_analyst_data)
visualization_workflow.add_node("visualize", generate_visualization)
visualization_workflow.add_node("generate_report", generate_report_text)

# Добавление рёбер
visualization_workflow.add_edge(START, "get_analyst_data")

# После получения данных аналитика - проверяем, нужна ли визуализация
visualization_workflow.add_conditional_edges(
    "get_analyst_data",
    should_visualize,
    {
        "visualize": "visualize",
        "report_only": "generate_report"
    }
)

# После визуализации - проверяем, нужен ли текстовый отчёт
visualization_workflow.add_conditional_edges(
    "visualize",
    should_generate_report,
    {
        "generate_report": "generate_report",
        "end": END
    }
)

# После генерации отчёта - завершаем
visualization_workflow.add_edge("generate_report", END)

# Компиляция графа
visualization_graph = visualization_workflow.compile()

