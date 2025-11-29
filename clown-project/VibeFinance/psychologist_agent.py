# FinancialPsychologistAgent.py (или psychologist_agent.py)

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
        - В критике будь мягок и ненавязчив, советуй альтернативы.
        - Используй обращение «ты».
        - Не упоминай категории напрямую — говори естественно.
        - Не добавляй пояснений, только сам ответ.
        - **Важно:** если описание говорит о сумме за неделю или нескольких покупках (например, "Потратил 8000 ₽ на развлечения за неделю"), реагируй на **общую тенденцию**, а не на одну трату. Отмечай осознанность, хвали за заботу о себе или мягко указывай на возможности улучшения.
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
        general_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
Ты — дружелюбный и поддерживающий финансовый психолог. Пользователь может задавать тебе вопросы о финансах, делиться своими переживаниями или просто здороваться.
Отвечай эмпатично, кратко и по существу.
Не отвечай на вопросы не по теме финансов, мягко говори что не знаешь ничего об этом
Если пользователь упоминает финансовую цель (накопить на машину, отпуск, чёрный день и т.п.), обязательно дай полезный совет.
Не предлагай пошаговый план — этим займётся другой агент. Просто поддержи и дай общий совет.
"""),
    ("human", "Сообщение пользователя: {user_message}")
])
        messages = general_prompt_template.format_messages(user_message=user_message)
        response = self.llm.invoke(messages)
        return response.content.strip()
