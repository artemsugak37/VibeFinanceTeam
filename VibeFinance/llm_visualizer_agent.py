# llm_visualizer_agent.py
"""
LLM-powered visualizer compatible with workflow.py.
Exposes SpendingVisualizerAgent with generate_visualization(user_id, period).
Internally uses VisualizationAgent + WeeklyReportAgent for data.
"""

from visualization_agent import VisualizationAgent  
from weekly_report_agent import WeeklyReportAgent  

class SpendingVisualizerAgent:
    def __init__(self):
        self.llm_viz = VisualizationAgent()
        self.report_agent = WeeklyReportAgent()  # для получения structured_data

    def generate_visualization(self, user_id: int, period: str = "week") -> dict:
        """
        Совместим с workflow.py: возвращает dict с table_html, chart_base64, summary.
        Но внутри использует LLM для генерации.
        """
        # 1. Получаем structured_data (как в недельном отчёте, но для нужного периода)
        analyst_data = self._get_analyst_data(user_id, period)
        
        if not analyst_data.get("spendings"):
            return {
                "table_html": "<p>За выбранный период нет трат.</p>",
                "chart_base64": None,
                "summary": "Нет данных для визуализации."
            }

        # 2. Генерируем LLM-визуализацию
        viz_result = self.llm_viz.generate_visualization_data(analyst_data)

        # 3. Преобразуем в формат, ожидаемый workflow.py
        table_html = self._tables_to_html(viz_result.get("tables", []))
        # chart_base64 пока None — можно добавить позже через matplotlib
        summary = "\n".join(viz_result.get("insights", [])) or f"Всего потрачено: {analyst_data['total_spent']:,.0f} ₽"

        return {
            "table_html": table_html,
            "chart_base64": None,  # или реализуй через matplotlib на основе viz_result['charts']
            "summary": summary
        }

    def _get_analyst_data(self, user_id: int, period: str):
        """Аналог weekly_report_agent, но для любого периода."""
        from datetime import datetime, timedelta
        import sqlite3
        
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
                ORDER BY timestamp DESC
            ''', (user_id, start_date.isoformat()))
        else:
            cursor.execute('''
                SELECT description, amount, category_main, category_psych, timestamp
                FROM spendings
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"spendings": [], "total_spent": 0, "category_totals": {}, "period": period_label}

        # Группировка
        category_totals = {}
        spendings = []
        total_spent = 0

        for desc, amt, main_cat, psych_cat, ts in rows:
            total_spent += amt
            if main_cat not in category_totals:
                category_totals[main_cat] = {"total": 0, "count": 0}
            category_totals[main_cat]["total"] += amt
            category_totals[main_cat]["count"] += 1

            spendings.append({
                "description": desc,
                "amount": amt,
                "category_main": main_cat,
                "category_psych": psych_cat,
                "timestamp": ts
            })

        return {
            "total_spent": total_spent,
            "category_totals": category_totals,
            "spendings": spendings,
            "period": period_label
        }

    def _tables_to_html(self, tables):
        if not tables:
            return "<p>Нет данных для таблицы.</p>"
        # Берём первую таблицу
        t = tables[0]
        html = f"<h3>{t.get('title', 'Таблица')}</h3>"
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<thead><tr>" + "".join(f"<th>{h}</th>" for h in t["headers"]) + "</tr></thead>"
        html += "<tbody>"
        for row in t["rows"]:
            html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        html += "</tbody></table>"
        return html