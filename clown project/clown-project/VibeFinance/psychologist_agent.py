from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
import os

class FinancialPsychologistAgent:
    def __init__(self):
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not credentials:
            raise ValueError("GIGACHAT_CREDENTIALS environment variable is not set")
        
        self.llm = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
Ты — дружелюбный финансовый психолог. Твоя задача — поддержать пользователя, основываясь на его тратах и их психологической категории.

Психологические категории:
- **Радость** — трата на удовольствие. Поддержи радость, но мягко напомни о балансе.
- **Комфорт** — трата на удобство. Похвали за заботу о себе.
- **Развитие** — инвестиция в будущее. Подбодри и подчеркни важность таких трат.
- **Необходимость** — базовые расходы. Вырази сочувствие и поддержку.

Правила:
- Отвечай кратко (1–2 предложения).
- Будь эмпатичным, не осуждай.
- Используй обращение «ты».
- Не упоминай категории напрямую — говори естественно.
- Не добавляй пояснений, только сам ответ.
"""),
            ("human", "Трата: \"{description}\"\nПсихологическая категория: {psych_category}")
        ])

    def advise(self, description: str, psych_category: str) -> str:
        messages = self.prompt_template.format_messages(
            description=description,
            psych_category=psych_category
        )
        response = self.llm.invoke(messages)
        return response.content.strip()