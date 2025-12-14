# visualization_agent.py
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Any
import sqlite3
from datetime import datetime, timedelta

class VisualizationAgent:
    """
    Агент-визуализатор, который получает данные от аналитика (weekly_report_agent)
    и генерирует структурированные данные для графиков и таблиц.
    """
    
    def __init__(self):
        load_dotenv()
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not credentials:
            raise ValueError("GIGACHAT_CREDENTIALS environment variable is not set")
        
        self.llm = GigaChat(credentials=credentials, verify_ssl_certs=False)
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
Ты — агент-визуализатор финансовых данных. Твоя задача — анализировать данные от аналитика
и создавать структурированные данные для графиков и таблиц.

Ты получаешь данные о тратах пользователя и должен:
1. Определить наиболее подходящие типы визуализаций
2. Подготовить данные в формате JSON для отображения графиков и таблиц
3. Предложить инсайты на основе данных

Верни ТОЛЬКО JSON в следующем формате:
{
  "charts": [
    {
      "type": "pie" | "bar" | "line",
      "title": "Название графика",
      "data": {
        "labels": ["Категория1", "Категория2", ...],
        "values": [100, 200, ...]
      }
    }
  ],
  "tables": [
    {
      "title": "Название таблицы",
      "headers": ["Колонка1", "Колонка2", ...],
      "rows": [
        ["Значение1", "Значение2", ...],
        ...
      ]
    }
  ],
  "insights": ["Инсайт 1", "Инсайт 2", ...]
}

Не добавляй пояснений, только JSON.
"""),
            ("human", "Данные от аналитика:\n{analyst_data}")
        ])
    
    def generate_visualization_data(self, analyst_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует данные для визуализации на основе данных от аналитика.
        
        Args:
            analyst_data: Структурированные данные от weekly_report_agent
            
        Returns:
            Словарь с данными для графиков, таблиц и инсайтами
        """
        try:
            # Преобразуем данные аналитика в текстовый формат для LLM
            analyst_text = self._format_analyst_data(analyst_data)
            
            messages = self.prompt_template.format_messages(analyst_data=analyst_text)
            response = self.llm.invoke(messages)
            
            raw_response = response.content.strip()
            # Убираем обёртки типа ```json ... ```
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
            raw_response = raw_response.strip()
            
            result = json.loads(raw_response)
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from visualization agent: {e}")
            # Возвращаем базовую визуализацию на основе данных
            return self._generate_fallback_visualization(analyst_data)
        except Exception as e:
            print(f"Error in visualization agent: {e}")
            return self._generate_fallback_visualization(analyst_data)
    
    def _format_analyst_data(self, analyst_data: Dict[str, Any]) -> str:
        """Форматирует данные аналитика в текстовый формат для LLM."""
        lines = []
        
        if "total_spent" in analyst_data:
            lines.append(f"Общая сумма трат: {analyst_data['total_spent']} ₽")
        
        if "category_totals" in analyst_data:
            lines.append("\nТраты по категориям:")
            for cat, data in analyst_data["category_totals"].items():
                lines.append(f"  - {cat}: {data['total']} ₽ ({data['count']} трат)")
        
        if "spendings" in analyst_data:
            lines.append(f"\nВсего трат: {len(analyst_data['spendings'])}")
        
        if "period" in analyst_data:
            lines.append(f"\nПериод: {analyst_data['period']}")
        
        return "\n".join(lines)
    
    def _generate_fallback_visualization(self, analyst_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует базовую визуализацию без использования LLM,
        если LLM вернул некорректные данные.
        """
        charts = []
        tables = []
        insights = []
        
        # Круговая диаграмма по категориям
        if "category_totals" in analyst_data and analyst_data["category_totals"]:
            category_data = analyst_data["category_totals"]
            labels = list(category_data.keys())
            values = [data["total"] for data in category_data.values()]
            
            charts.append({
                "type": "pie",
                "title": "Распределение трат по категориям",
                "data": {
                    "labels": labels,
                    "values": values
                }
            })
            
            # Столбчатая диаграмма
            charts.append({
                "type": "bar",
                "title": "Сумма трат по категориям",
                "data": {
                    "labels": labels,
                    "values": values
                }
            })
        
        # График динамики трат по времени
        if "spendings" in analyst_data and analyst_data["spendings"]:
            # Группируем траты по датам
            daily_totals = {}
            for spending in analyst_data["spendings"]:
                try:
                    ts = spending.get("timestamp")
                    if ts and ts != "null":
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        date_key = dt.strftime("%Y-%m-%d")
                        if date_key not in daily_totals:
                            daily_totals[date_key] = 0
                        daily_totals[date_key] += spending.get("amount", 0)
                except:
                    continue
            
            if daily_totals:
                # Сортируем по дате
                sorted_dates = sorted(daily_totals.keys())
                dates = sorted_dates
                amounts = [daily_totals[date] for date in dates]
                
                charts.append({
                    "type": "line",
                    "title": "Динамика трат по времени",
                    "data": {
                        "dates": dates,
                        "values": amounts
                    }
                })
        
        # Таблица трат
        if "spendings" in analyst_data and analyst_data["spendings"]:
            table_rows = []
            for spending in analyst_data["spendings"][:10]:  # Первые 10 трат
                date_str = spending.get("timestamp", "N/A")
                try:
                    if date_str and date_str != "null":
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    pass
                
                table_rows.append([
                    spending.get("description", "N/A"),
                    f"{spending.get('amount', 0):.2f} ₽",
                    spending.get("category_main", "N/A"),
                    date_str
                ])
            
            tables.append({
                "title": "Последние траты",
                "headers": ["Описание", "Сумма", "Категория", "Дата"],
                "rows": table_rows
            })
        
        # Базовые инсайты
        if "total_spent" in analyst_data:
            total = analyst_data["total_spent"]
            insights.append(f"За период потрачено {total:.2f} ₽")
        
        if "category_totals" in analyst_data:
            if analyst_data["category_totals"]:
                top_category = max(
                    analyst_data["category_totals"].items(),
                    key=lambda x: x[1]["total"]
                )
                insights.append(f"Больше всего потрачено на '{top_category[0]}': {top_category[1]['total']:.2f} ₽")
        
        return {
            "charts": charts,
            "tables": tables,
            "insights": insights
        }
    
    def get_weekly_visualization_data(self, user_id: int) -> Dict[str, Any]:
        """
        Получает данные напрямую из БД и генерирует визуализацию.
        Это альтернативный метод, который не требует данных от аналитика.
        """
        return self.get_visualization_data_by_period(user_id, "week")
    
    def get_visualization_data_by_period(self, user_id: int, period: str = "week") -> Dict[str, Any]:
        """
        Получает данные из БД для указанного периода и генерирует визуализацию.
        
        Args:
            user_id: ID пользователя
            period: "week", "month" или "all"
        """
        if period == "week":
            start_date = datetime.now() - timedelta(days=7)
            period_label = "Последняя неделя"
        elif period == "month":
            start_date = datetime.now() - timedelta(days=30)
            period_label = "Последний месяц"
        else:  # all
            start_date = None
            period_label = "Всё время"
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        if start_date:
            cursor.execute('''
                SELECT description, amount, category_main, category_psych, timestamp
                FROM spendings
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            ''', (user_id, start_date.isoformat()))
        else:
            cursor.execute('''
                SELECT description, amount, category_main, category_psych, timestamp
                FROM spendings
                WHERE user_id = ?
                ORDER BY timestamp ASC
            ''', (user_id,))
        
        all_spendings = cursor.fetchall()
        conn.close()
        
        if not all_spendings:
            return {
                "charts": [],
                "tables": [],
                "insights": [f"За {period_label.lower()} не было трат"]
            }
        
        # Группировка по категориям
        category_totals = {}
        spendings_list = []
        
        for desc, amt, main_cat, psych_cat, ts in all_spendings:
            if main_cat not in category_totals:
                category_totals[main_cat] = {"total": 0, "count": 0}
            category_totals[main_cat]["total"] += amt
            category_totals[main_cat]["count"] += 1
            
            spendings_list.append({
                "description": desc,
                "amount": amt,
                "category_main": main_cat,
                "category_psych": psych_cat,
                "timestamp": ts
            })
        
        total_spent = sum(v["total"] for v in category_totals.values())
        
        # Формируем данные для аналитика
        analyst_data = {
            "total_spent": total_spent,
            "category_totals": category_totals,
            "spendings": spendings_list,
            "period": period_label
        }
        
        # Генерируем визуализацию
        return self.generate_visualization_data(analyst_data)

