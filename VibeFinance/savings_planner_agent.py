# savings_planner_agent.py

import re
import sqlite3
from datetime import datetime
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

class SavingsPlannerAgent:
    def __init__(self):
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not credentials:
            raise ValueError("GIGACHAT_CREDENTIALS environment variable is not set")
        self.llm = GigaChat(credentials=credentials, verify_ssl_certs=False)

        # Промпт для извлечения цели и суммы
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """
Ты — финансовый ассистент. Извлеки из сообщения пользователя **цель** (что он хочет купить/на что накопить) и **целевую сумму в рублях**.

Правила:
- Если сумма указана словами («сто тысяч»), переведи в число.
- Если валюта не рубли — конвертируй в рубли по текущему курсу (~1$ = 90₽, ~1€ = 100₽).
- Если сумма не указана — верни `"amount": null`.
- Верни ТОЛЬКО JSON без пояснений: {{"goal": "...", "amount": число | null}}
"""),
            ("human", "{user_message}")
        ])

        # Промпт для финального совета
        self.advice_prompt = ChatPromptTemplate.from_messages([
            ("system", """
Ты — мотивирующий финансовый коуч. На основе данных ниже сформулируй краткий (2–3 предложения), тёплый и поддерживающий совет.

Данные:
- Цель: {goal}
- Целевая сумма: {target_amount:,.0f} ₽
- Ежемесячный взнос: {monthly_savings:,.0f} ₽
- Срок накопления: {months} {months_word}

Совет должен:
- Похвалить за постановку цели.
- Подчеркнуть реалистичность плана.
- Добавить мотивационную фразу.
"""),
            ("human", "Сформируй совет.")
        ])

    def extract_goal_and_amount(self, message: str):
        """Извлекает цель и сумму из запроса."""
        messages = self.extraction_prompt.format_messages(user_message=message)
        response = self.llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        try:
            import json
            data = json.loads(raw.strip())
            return data.get("goal", ""), data.get("amount")
        except Exception as e:
            print(f"Ошибка парсинга цели: {e}")
            return "", None

    def estimate_monthly_income(self, user_id: int) -> float:
        """Оценивает средний ежемесячный доход (упрощённо — через траты + резерв)."""
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT amount, timestamp FROM spendings WHERE user_id = ?', (user_id,))
                rows = cursor.fetchall()
                if not rows:
                    return 60000.0  # дефолтное предположение

                # Группируем по месяцам
                monthly_spending = {}
                for amount, ts in rows:
                    try:
                        month = ts[:7]  # "YYYY-MM"
                        monthly_spending[month] = monthly_spending.get(month, 0) + amount
                    except:
                        continue

                if not monthly_spending:
                    return 60000.0

                avg_monthly_spending = sum(monthly_spending.values()) / len(monthly_spending)
                # Предполагаем, что человек тратит ~80% дохода → доход = трата / 0.8
                estimated_income = avg_monthly_spending / 0.8
                return max(estimated_income, 30000.0)  # минимум 30к
        except Exception as e:
            print(f"Ошибка оценки дохода: {e}")
            return 60000.0

    def calculate_plan(self, target_amount: float, user_id: int, goal: str = "Финансовая цель") -> dict:
        """
        Возвращает: {
            "monthly_savings": float,
            "months": int,
            "advice": str
        }
        """
        # Пытаемся оценить, сколько пользователь может откладывать
        estimated_income = self.estimate_monthly_income(user_id)
        max_savings = estimated_income * 0.3  # не более 30% дохода

        # Разумные границы
        min_savings = max(500.0, target_amount / 24)  # минимум — за 2 года
        monthly_savings = min(max_savings, target_amount / 3)  # стремимся к 3–8 месяцам
        monthly_savings = max(min_savings, monthly_savings)

        months = max(1, round(target_amount / monthly_savings))

        # Регулируем взнос, чтобы ровно накопить
        monthly_savings = target_amount / months

        # Определи слово для месяцев
        months_word = self._months_to_text(months)
        
        # Генерация совета — ИСПОЛЬЗУЕМ ПРОСТЫЕ ПЛЕЙСХОЛДЕРЫ
        messages = self.advice_prompt.format_messages(
            goal=goal,
            target_amount=target_amount,
            monthly_savings=monthly_savings,
            months=months,
            months_word=months_word
        )
        response = self.llm.invoke(messages)
        advice = response.content.strip()

        return {
            "monthly_savings": round(monthly_savings, 2),
            "months": months,
            "advice": advice
        }

    def generate_plan(self, user_message: str, user_id: int) -> str:
        goal, amount = self.extract_goal_and_amount(user_message)

        if not goal:
            goal = "Финансовая цель"

        if amount is None:
            return (
                "Хорошо! Чтобы составить план, мне нужно знать, **во сколько рублей оценивается ваша цель**.\n"
                "Например: «Хочу накопить на MacBook за 120000 рублей» или просто «Цель — 75000 ₽»."
            )

        if amount <= 0:
            return "Похоже, сумма некорректна. Укажите положительную сумму в рублях."

        # 🔹 Сначала рассчитываем план (без сохранения)
        try:
            plan = self.calculate_plan(amount, user_id, goal)
        except Exception as e:
            print(f"Ошибка расчёта плана: {e}")
            return "Не удалось рассчитать план. Попробуйте позже."

        # 🔹 Только после успешного расчёта — сохраняем в БД
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO goals (user_id, title, target_amount)
                    VALUES (?, ?, ?)
                ''', (user_id, goal, amount))
                conn.commit()
        except Exception as e:
            print(f"Цель рассчитана, но не сохранена в БД: {e}")
            # Не прерываем — всё равно показываем план

        # Формируем финальное сообщение
        months_word = self._months_to_text(plan["months"])
        return (
            f"🎯 **План накоплений на: {goal}**\n\n"
            f"• **Целевая сумма:** {plan['monthly_savings'] * plan['months']:,.0f} ₽\n"
            f"• **Ежемесячный взнос:** {plan['monthly_savings']:,.0f} ₽\n"
            f"• **Срок:** {plan['months']} {months_word}\n\n"
            f"{plan['advice']}\n\n"
            "Хочешь, я помогу создать напоминания или автоматизировать отчисления?"
        )

    def _months_to_text(self, n: int) -> str:
        if n % 10 == 1 and n % 100 != 11:
            return "месяц"
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return "месяца"
        else:
            return "месяцев"

    def get_user_goals(self, user_id: int) -> str:
        """Возвращает Markdown-список активных целей пользователя."""
        try:
            with sqlite3.connect('users.db') as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, target_amount, current_amount, target_date
                    FROM goals
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                ''', (user_id,))
                rows = cursor.fetchall()

            if not rows:
                return (
                    "У вас пока нет активных финансовых целей. 🎯\n"
                    "Просто скажите, на что хотите накопить — и я помогу составить план!"
                )

            lines = ["**🎯 Ваши активные цели:**"]
            for row in rows:
                title = row["title"]
                target = row["target_amount"]
                current = row["current_amount"] or 0
                progress = min(100, round(current / target * 100)) if target > 0 else 0

                # Прогресс-бар (текстовый)
                bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
                lines.append(f"\n**{title}**")
                lines.append(f"Цель: **{target:,.0f} ₽**")
                lines.append(f"Накоплено: **{current:,.0f} ₽** ({progress}%)")
                lines.append(f"`[{bar}]`")

            lines.append("\nХочешь добавить новую цель или изменить существующую?")
            return "\n".join(lines)

        except Exception as e:
            print(f"Ошибка загрузки целей: {e}")
            return "Не удалось загрузить цели. Попробуйте позже."