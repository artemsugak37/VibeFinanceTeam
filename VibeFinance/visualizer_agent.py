# visualizer_agent.py
import sqlite3
import base64
import io
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

class SpendingVisualizerAgent:
    def __init__(self):
        # Настройка стиля графиков под ваш бренд
        sns.set_style("whitegrid")
        plt.rcParams.update({
            'font.family': 'Segoe UI',
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10
        })

    def generate_visualization(self, user_id: int, period: str = "week") -> dict:
        """
        Генерирует таблицу и график трат за указанный период.
        period: "week", "month", "all"
        """
        # Определяем дату начала периода
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
            title_period = "неделю"
        elif period == "month":
            start_date = now - timedelta(days=30)
            title_period = "месяц"
        else:  # all
            start_date = None
            title_period = "всё время"

        # Загружаем данные
        spendings = self._fetch_spendings(user_required=user_id, start_date=start_date)
        
        if not spendings:
            return {
                "table_html": "<p>За выбранный период нет трат.</p>",
                "chart_base64": None,
                "summary": "Нет данных для визуализации."
            }

        # Генерация HTML-таблицы
        table_html = self._generate_html_table(spendings)

        # Генерация графика
        chart_base64 = self._generate_chart_base64(spendings)

        # Итоговая сводка
        total = sum(s["amount"] for s in spendings)
        count = len(spendings)
        summary = f"Всего потрачено: **{total:,.0f} ₽** в **{count}** операциях за {title_period}."

        return {
            "table_html": table_html,
            "chart_base64": chart_base64,
            "summary": summary
        }

    def _fetch_spendings(self, user_required: int, start_date=None):
        try:
            with sqlite3.connect('users.db') as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if start_date:
                    cursor.execute('''
                        SELECT description, amount, category_main, category_psych, timestamp
                        FROM spendings
                        WHERE user_id = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                    ''', (user_required, start_date.isoformat()))
                else:
                    cursor.execute('''
                        SELECT description, amount, category_main, category_psych, timestamp
                        FROM spendings
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                    ''', (user_required,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Visualizer DB error: {e}")
            return []

    def _generate_html_table(self, spendings):
        html = """
        <div style="overflow-x: auto; margin: 16px 0;">
          <table style="min-width: 500px; border-collapse: collapse; width: 100%;">
            <thead>
              <tr style="background-color: #f1f5f9;">
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Описание</th>
                <th style="padding: 12px; text-align: right; border-bottom: 23px solid #e2e8f0;">Сумма</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Категория</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Психология</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th>
              </tr>
            </thead>
            <tbody>
        """
        for s in spendings[:20]:  # Ограничиваем 20 строками
            date_str = s["timestamp"][:16].replace("T", " ") if s["timestamp"] else "—"
            html += f"""
              <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px;">{s["description"]}</td>
                <td style="padding: 10px; text-align: right; font-weight: 600; color: #4f46e5;">{s["amount"]:,.0f} ₽</td>
                <td style="padding: 10px;">
                  <span style="background: #e0e7ff; color: #4f46e5; padding: 2px 8px; border-radius: 12px; font-size: 0.85em;">
                    {s["category_main"]}
                  </span>
                </td>
                <td style="padding: 10px;">
                  <span style="background: #dcfce7; color: #10b981; padding: 2px 8px; border-radius: 12px; font-size: 0.85em;">
                    {s["category_psych"]}
                  </span>
                </td>
                <td style="padding: 10px; color: #64748b;">{date_str}</td>
              </tr>
            """
        html += """
            </tbody>
          </table>
        </div>
        """
        return html

    def _generate_chart_base64(self, spendings):
        # Агрегация по основным категориям
        cat_totals = {}
        for s in spendings:
            cat = s["category_main"]
            cat_totals[cat] = cat_totals.get(cat, 0) + s["amount"]

        if not cat_totals:
            return None

        # Сортировка и ограничение до 6 категорий + "Другое"
        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_cats) > 6:
            top = sorted_cats[:6]
            other = sum(v for _, v in sorted_cats[6:])
            cat_totals = dict(top)
            if other > 0:
                cat_totals["Другое"] = other
        else:
            cat_totals = dict(sorted_cats)

        # Цвета под ваш бренд
        colors = ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff", "#f0f9ff", "#10b981"]

        fig, ax = plt.subplots(figsize=(8, 5))
        wedges, texts, autotexts = ax.pie(
            cat_totals.values(),
            labels=cat_totals.keys(),
            autopct=lambda pct: f'{pct:.1f}%\n({pct/100*sum(cat_totals.values()):,.0f} ₽)',
            startangle=90,
            colors=colors[:len(cat_totals)],
            textprops={'fontsize': 10}
        )
        ax.set_title("Распределение трат по категориям", pad=20, fontsize=14, fontweight='bold')
        plt.tight_layout()

        # Конвертация в base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64
