# psychologist_agent.py

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

        # Существующий промпт для советов по трате
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
Ты — дружелюбный финансовый психолог. Твоя задача — поддержать пользователя, основываясь на его тратах и их психологической категории.

Психологические категории:
- **Радость** — трата на удовольствие кроме вредных привычек и "темных делишек". Поддержи радость, но мягко напомни о балансе.
- **Комфорт** — трата на удобство. Похвали за заботу о себе.
- **Развитие** — инвестиция в будущее. Подбодри и подчеркни важность таких трат.
- **Необходимость** — базовые расходы. Вырази сочувствие и поддержку.
- **Ошибки** - плохие траты пользователя. Мягко вырази ему несогласие.

Правила:
- Отвечай кратко (2-3 предложения).
- Будь эмпатичным.
- В критике будь мягок и ненавязчив, советуй альтеринативы.
- Используй обращение «ты».
- Не упоминай категории напрямую — говори естественно.
- Не добавляй пояснений, только сам ответ.
"""),
            ("human", "Трата: \"{description}\"\nПсихологическая категория: {psych_category}")
        ])

    # Существующий метод для советов по трате
    def advise(self, description: str, psych_category: str) -> str:
        messages = self.prompt_template.format_messages(
            description=description,
            psych_category=psych_category
        )
        response = self.llm.invoke(messages)
        return response.content.strip()

    # НОВЫЙ метод для ответа на общие вопросы
    def respond_to_general_query(self, user_message: str) -> str:
        # Новый промпт для общения
        general_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
Ты — дружелюбный и поддерживающий финансовый психолог. Пользователь может задавать тебе вопросы о финансах, делиться своими переживаниями или просто здороваться.
Отвечай эмпатично, кратко и по существу. Если вопрос касается финансов, постарайся дать полезный совет.
Если пользователь сообщает о трате, но она не была структурировано передана (например, не через основной чат трат), ты можешь мягко предложить использовать основной чат для этого.
"""),
            ("human", "Сообщение пользователя: {user_message}")
        ])

        messages = general_prompt_template.format_messages(user_message=user_message)
        response = self.llm.invoke(messages)
        return response.content.strip()
