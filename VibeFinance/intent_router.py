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
            ("system", "Ты — классификатор запросов. Ответь одной строкой: spending, goal, goals, question, greeting или visualization."),
            ("human", "Сообщение: '{message}'\nКлассификация:")
        ])

    def route(self, message: str) -> str:
        try:
            messages = self.prompt.format_messages(message=message)
            response = self.llm.invoke(messages)
            intent = response.content.strip().split()[0].lower()
            if intent in ["spending", "goal", "goals", "question", "greeting", "visualization"]:
                return intent
        except Exception as e:
            print(f"Intent routing error: {e}")
        return "question"