# weekly_report_agent.py
from psychologist_agent import FinancialPsychologistAgent
import sqlite3
from datetime import datetime, timedelta

class WeeklyReportAgent:
    def __init__(self):
        self.psychologist = FinancialPsychologistAgent()

    def generate_weekly_report(self, user_id: int) -> str:
        """Генерирует текстовый отчёт (для обратной совместимости)."""
        data = self.get_weekly_report_data(user_id)
        return self.format_report_text(data)
    
    def get_weekly_report_data(self, user_id: int) -> dict:
        """
        Получает структурированные данные для недельного отчёта.
        Возвращает словарь с данными для аналитики и визуализации.
        """
        week_ago = datetime.now() - timedelta(days=7)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Все траты за неделю
        cursor.execute('''
            SELECT description, amount, category_main, category_psych, timestamp
            FROM spendings
            WHERE user_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (user_id, week_ago.isoformat()))
        all_spendings = cursor.fetchall()
        conn.close()

        if not all_spendings:
            return {
                "total_spent": 0,
                "category_totals": {},
                "spendings": [],
                "period": "Последняя неделя",
                "has_data": False
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
        
        return {
            "total_spent": total_spent,
            "category_totals": category_totals,
            "spendings": spendings_list,
            "period": "Последняя неделя",
            "has_data": True
        }
    
    def format_report_text(self, data: dict) -> str:
        """Форматирует структурированные данные в текстовый отчёт."""
        if not data.get("has_data", False):
            return (
                "**📊 Отчёт за последнюю неделю**\n\n"
                "У вас не было трат — это замечательно!\n"
                "Вы отлично контролируете свои финансы. Так держать! 💪"
            )
        
        total_spent = data["total_spent"]
        category_totals = data["category_totals"]
        spendings_list = data["spendings"]
        
        lines = []
        lines.append(f"**📊 Финансовый отчёт за последнюю неделю**")
        lines.append(f"Всего потрачено: **{round(total_spent, 2)} ₽**")
        lines.append("")
        lines.append("**🧠 Ваш психологический анализ:**")
        
        for cat, cat_data in category_totals.items():
            total = round(cat_data["total"], 2)
            count = cat_data["count"]
            psych_cat = self._map_to_psych_category(cat)
            desc = f"Потратил {total} ₽ на {cat.lower()} в {count} случаях за неделю"
            advice = self.psychologist.advise(desc, psych_cat)
            lines.append(f"• **{cat}**: {total} ₽ → {advice}")
        
        lines.append("")
        lines.append("**📋 Подробный список всех трат:**")
        
        for spending in spendings_list:
            ts = spending.get("timestamp")
            if ts == 'null' or ts is None:
                date_str = "время не указано"
            else:
                try:
                    date_str = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime("%d.%m %H:%M")
                except (ValueError, AttributeError):
                    date_str = "некорректная дата"
            amt = spending.get("amount", 0)
            desc = spending.get("description", "N/A")
            lines.append(f"• {desc} — **{round(amt, 2)} ₽** ({date_str})")
        
        lines.append("")
        lines.append("Спасибо, что заботитесь о своих финансах! 💫")
        return "\n".join(lines)

    def _map_to_psych_category(self, main_cat: str) -> str:
        mapping = {
            "Еда": "Необходимость",
            "Транспорт": "Необходимость",
            "Жилье": "Необходимость",
            "Здоровье": "Необходимость",
            "Образование": "Развитие",
            "Одежда": "Комфорт",
            "Связь": "Необходимость",
            "Развлечения": "Радость",
            "Другое": "Радость"
        }
        return mapping.get(main_cat, "Радость")