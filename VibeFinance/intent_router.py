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
Ты — строгий маршрутизатор. Твоя задача — ОДНОЗНАЧНО определить тип сообщения и вернуть только одно слово из списка:
- spending
- goal
- goals
- question
- greeting
- visualization

Правила:
1. Если пользователь описывает покупку или расход (даже без суммы) — "spending".
2. Если речь о накоплениях, целях, бюджете — "goal".
3. Если запрос на просмотр целей — "goals".
4. Если общий вопрос — "question".
5. Приветствие — "greeting".
6. Запрос на графики/статистику — "visualization".

Никаких пояснений, только одно слово.

"""),
            ("human", "{message}")
        ])

    def route(self, message: str) -> str:
        try:
            messages = self.prompt.format_messages(message=message)
            response = self.llm.invoke(messages)
            intent = response.content.strip().lower()
            if intent in ["spending", "goal", "goals", "question", "greeting", "visualization"]:
                return intent
        except Exception as e:
            print(f"Intent routing error: {e}")
        return "question"