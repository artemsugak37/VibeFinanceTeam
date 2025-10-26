# classificator.py

from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import json # <-- Добавить импорт json

class SpendingClassifierAgent:
    def __init__(self):
        try:
            load_dotenv()
            credentials = os.getenv("GIGACHAT_CREDENTIALS")
            print(f"Initializing GigaChat with credentials: {bool(credentials)}")

            if not credentials:
                raise ValueError("GIGACHAT_CREDENTIALS environment variable is not set")

            # Используем LangChain для работы с GigaChat
            self.llm = GigaChat(
                credentials=credentials,
                verify_ssl_certs=False
            )
            print("GigaChat initialized successfully")

        except Exception as e:
            print(f"Error initializing GigaChat: {type(e).__name__}: {e}")
            raise e

        # НОВЫЙ промпт-шаблон, возвращающий JSON
        # Используем placeholder {user_spending_input} вместо {spending_text}, чтобы избежать конфликта
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system",
             """Ты финансовый помощник-классификатор. Твоя задача - анализировать текстовое описание траты, извлекать из него сумму и дату (если указана), и присваивать двумя категориями. ВОЗВРАЩАЙ ТОЛЬКО JSON-ОБЪЕКТ СЛЕДУЮЩЕЙ СТРУКТУРЫ И НИЧЕГО БОЛЬШЕ:

        {{
          "original_description": "точно так же, как ввёл пользователь",
          "parsed_description": "очищенное описание траты, например 'кофе и круассан'",
          "amount": "число, извлечённая сумма, например 180.0. Если сумма не указана, верни null.",
          "main_category": "одна из: Еда, Транспорт, Развлечения, Здоровье, Одежда, Жилье, Образование, Связь, Другое",
          "psych_category": "одна из: Радость, Комфорт, Развитие, Необходимость",
          "parsed_date": "строка даты в формате YYYY-MM-DDTHH:MM:SS, например '2025-10-25T15:30:00'. Если дата не указана, верни null.",
          "confidence": "число от 0.0 до 1.0, уверенность в классификации"
        }}

        ПРАВИЛА:
        1. Всегда возвращай строго указанный JSON. Не добавляй комментарии, пояснения или лишний текст.
        2. Если сумма или дата не указаны в тексте, верни для них null.
        3. Постарайся извлечь дату, если она есть (вчера, сегодня, 15 октября, 2023-10-15 и т.п.). Если не уверен, верни null.
        4. Будь внимателен к контексту при классификации.

        ПРИМЕР:
        Вход: "Купил кофе и круассан в Starbucks за 180 рублей вчера"
        Выход: {{"original_description": "Купил кофе и круассан в Starbucks за 180 рублей вчера", "parsed_description": "кофе и круассан", "amount": 180.0, "main_category": "Еда", "psych_category": "Радость", "parsed_date": "2025-10-25T00:00:00", "confidence": 0.85}}

        Теперь проанализируй следующую трату:"""
            ),
            ("human", "{user_spending_input}") # <-- Используем НОВОЕ имя placeholder
        ])

    def classify(self, spending_text: str) -> dict: # <-- Изменили возвращаемый тип
        try:
            print(f"GigaChat credentials available: {bool(os.getenv('GIGACHAT_CREDENTIALS'))}")

            # Формируем сообщения через LangChain, используя новое имя
            messages = self.prompt_template.format_messages(user_spending_input=spending_text) # <-- Передаём с новым именем
            print(f"Formatted messages: {messages}")

            # Вызываем модель через стандартный интерфейс LangChain
            print("Calling GigaChat API...")
            response = self.llm.invoke(messages)
            print(f"GigaChat response: {response}")
            print(f"Response content: '{response.content}'")

            # Попытка распарсить JSON
            raw_response = response.content.strip()
            # Убираем потенциальные обёртки типа ```json ... ```
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:] # Убираем ```json
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3] # Убираем ```
            raw_response = raw_response.strip()

            result = json.loads(raw_response)
            print(f"Parsed JSON result: {result}")

            return result # <-- Возвращаем словарь

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from GigaChat: {e}")
            print(f"Raw response: {response.content}")
            raise ValueError(f"GigaChat вернул некорректный JSON: {response.content}")
        except Exception as e:
            print(f"Error in classify method: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise e
