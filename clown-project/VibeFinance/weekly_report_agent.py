# weekly_report_agent.py
from psychologist_agent import FinancialPsychologistAgent
import sqlite3
from datetime import datetime, timedelta

class WeeklyReportAgent:
    def __init__(self):
        self.psychologist = FinancialPsychologistAgent()

    def generate_weekly_report(self, user_id: int) -> str:
        week_ago = datetime.now() - timedelta(days=7)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Все траты за неделю
        cursor.execute('''
            SELECT description, amount, category_main, timestamp
            FROM spendings
            WHERE user_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (user_id, week_ago.isoformat()))
        all_spendings = cursor.fetchall()
        conn.close()

        if not all_spendings:
            return (
                "**📊 Отчёт за последнюю неделю**\n\n"
                "У вас не было трат — это замечательно!\n"
                "Вы отлично контролируете свои финансы. Так держать! 💪"
            )

        # Группировка по категориям
        category_totals = {}
        for desc, amt, cat, ts in all_spendings:
            if cat not in category_totals:
                category_totals[cat] = {"total": 0, "count": 0}
            category_totals[cat]["total"] += amt
            category_totals[cat]["count"] += 1

        total_spent = sum(v["total"] for v in category_totals.values())
        
        lines = []
        lines.append(f"**📊 Финансовый отчёт за последнюю неделю**")
        lines.append(f"Всего потрачено: **{round(total_spent, 2)} ₽**")
        lines.append("")
        lines.append("**🧠 Ваш психологический анализ:**")
        
        for cat, data in category_totals.items():
            total = round(data["total"], 2)
            count = data["count"]
            psych_cat = self._map_to_psych_category(cat)
            desc = f"Потратил {total} ₽ на {cat.lower()} в {count} случаях за неделю"
            advice = self.psychologist.advise(desc, psych_cat)
            lines.append(f"• **{cat}**: {total} ₽ → {advice}")
        
        lines.append("")
        lines.append("**📋 Подробный список всех трат:**")
        
        for desc, amt, cat, ts in all_spendings:
            if ts == 'null' or ts is None:
                date_str = "время не указано"
            else:
                try:
                    date_str = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime("%d.%m %H:%M")
                except (ValueError, AttributeError):
                    date_str = "некорректная дата"
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