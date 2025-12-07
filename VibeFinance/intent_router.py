# intent_router.py
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import json

load_dotenv()

class IntentRouterAgent:
    def __init__(self):
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not credentials:
            raise ValueError("GIGACHAT_CREDENTIALS environment variable is not set")
        self.llm = GigaChat(credentials=credentials, verify_ssl_certs=False)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
Ты — маршрутизатор запросов. Определи **намерение пользователя** на основе его сообщения.

Возможные типы:
- "spending": пользователь **описывает конкретную покупку или расход** (даже если сумма не указана). Примеры: "Купил кофе", "Заправил машину".
- "goal": пользователь говорит о **накоплениях, целях, мечтах, бюджете на будущее**. Примеры: "Хочу накопить на машину", "Как отложить на отпуск?"
- "question": пользователь **задаёт общий вопрос** о финансах или делится переживаниями. Примеры: "Как сэкономить?", "Почему я всё трачу?"
- "greeting": приветствие, прощание или техническая фраза. Примеры: "Привет", "Пока", "Ты тут?"
- "visualization": запрос на **графики, диаграммы, статистику, таблицы трат**. Примеры: "Покажи графики", "Статистика за неделю", "Визуализируй мои траты".

Верни ТОЛЬКО JSON в формате:
{{"intent": "spending" | "goal" | "question" | "greeting"}}

Не добавляй пояснений.
"""),
            ("human", "{message}")
        ])

    def route(self, message: str) -> str:
        messages = self.prompt.format_messages(message=message)
        response = self.llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        try:
            result = json.loads(raw.strip())
            intent = result.get("intent")
            if intent in ["spending", "goal", "question", "greeting", "visualization"]:
                return intent
        except:
            pass
        return "question"
