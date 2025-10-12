# gigachat_agent.py с LangChain
from langchain.chat_models.gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
import os
import logging
from typing import Optional

# Настраиваем логирование для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpendingClassifierAgent:
    """Агент для классификации текстовых описаний трат по категориям."""

    def __init__(self, credentials: Optional[str] = None):
        """
        Инициализация агента классификатора.

        Args:
            credentials: Токен доступа GigaChat. Если None, берется из переменной окружения.
        """
        # Получаем credentials из аргумента или переменной окружения
        self.credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")

        if not self.credentials:
            raise ValueError(
                "Не найден токен GigaChat. Установите переменную окружения GIGACHAT_CREDENTIALS "
                "или передайте токен напрямую в конструктор."
            )

        # Инициализируем GigaChat через LangChain
        try:
            self.llm = GigaChat(
                credentials=self.credentials,
                verify_ssl_certs=False,  # Для избежания SSL ошибок
                timeout=30,  # Таймаут в секундах
                model="GigaChat",  # Указываем модель
                scope="GIGACHAT_API_PERS"  # Область доступа
            )
            logger.info("GigaChat инициализирован успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации GigaChat: {e}")
            raise

        # Создаем промпт-шаблон с улучшенной инструкцией
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{spending_text}")
        ])

    def _get_system_prompt(self) -> str:
        """Возвращает системный промпт для классификации."""
        return """
        Ты финансовый помощник-классификатор. Твоя задача - анализировать текстовое описание траты и присваивать ей две категории через знак " | ".

        ПЕРВАЯ КАТЕГОРИЯ (основной тип траты):
        - Еда (продукты питания, рестораны, кафе, кофе)
        - Транспорт (топливо, такси, общественный транспорт, ремонт авто)
        - Развлечения (кино, концерты, игры, хобби)
        - Здоровье (медицина, лекарства, спортзал)
        - Одежда (одежда, обувь, аксессуары)
        - Жилье (коммунальные услуги, аренда, ремонт)
        - Образование (курсы, книги, обучение)
        - Связь (интернет, мобильная связь)
        - Другое (все остальное)

        ВТОРАЯ КАТЕГОРИЯ (психологический характер траты):
        - Радость (трата, которая приносит сиюминутное удовольствие, развлечения)
        - Комфорт (трата, которая повышает ежедневное качество жизни, удобство)
        - Развитие (трата на образование, здоровье, саморазвитие, инвестиции в будущее)
        - Необходимость (обязательные траты, без которых нельзя обойтись)

        ПРАВИЛА КЛАССИФИКАЦИИ:
        1. Будь внимателен к контексту
        2. Если не уверен в категории - выбирай "Другое" для первой категории
        3. Всегда возвращай ответ строго в формате: "ПерваяКатегория | ВтораяКатегория"
        4. Не добавляй никаких дополнительных слов, точек или объяснений

        ПРИМЕРЫ:
        - "Купил кофе и круассан в Starbucks по дороге на работу" → Еда | Радость
        - "Оплата проездного на месяц на метро" → Транспорт | Комфорт
        - "Заправил полный бак бензина на АЗС" → Транспорт | Необходимость
        - "Купил новую подушку, чтобы лучше спать" → Другое | Комфорт
        - "Записался на курсы английского языка" → Образование | Развитие
        - "Купил обезболивающее в аптеке" → Здоровье | Необходимость
        - "Билеты в кино на премьеру" → Развлечения | Радость
        - "Оплатил интернет за месяц" → Связь | Необходимость
        - "Купил кроссовки для бега" → Одежда | Развитие

        Теперь проанализируй следующую трату:
        """

    def classify(self, spending_text: str) -> str:
        """
        Классифицирует текст траты на категории.

        Args:
            spending_text: Текстовое описание траты

        Returns:
            Строка с категориями в формате "ПерваяКатегория | ВтораяКатегория"

        Raises:
            Exception: Если произошла ошибка при обращении к API
        """
        if not spending_text or not spending_text.strip():
            return "Другое | Необходимость"

        try:
            # Формируем сообщения через LangChain
            messages = self.prompt_template.format_messages(spending_text=spending_text.strip())

            logger.info(f"Отправка запроса для классификации: '{spending_text}'")

            # Вызываем модель через стандартный интерфейс LangChain
            response = self.llm.invoke(messages)
            result = response.content.strip()

            logger.info(f"Получен ответ от GigaChat: '{result}'")

            # Валидация и очистка ответа
            cleaned_result = self._validate_and_clean_response(result)

            return cleaned_result

        except Exception as e:
            logger.error(f"Ошибка при классификации траты '{spending_text}': {e}")
            return "Другое | Необходимость"

    def _validate_and_clean_response(self, response: str) -> str:
        """
        Валидирует и очищает ответ от модели.

        Args:
            response: Ответ от GigaChat

        Returns:
            Очищенный и валидированный ответ
        """
        # Убираем лишние пробелы и кавычки
        cleaned = response.strip().strip('"').strip("'").strip()

        # Проверяем формат "Категория | Категория"
        if "|" not in cleaned:
            logger.warning(f"Некорректный формат ответа: '{response}'. Возвращаем категорию по умолчанию.")
            return "Другое | Необходимость"

        # Разделяем на категории и очищаем каждую
        parts = cleaned.split("|")
        if len(parts) != 2:
            return "Другое | Необходимость"

        category1 = parts[0].strip()
        category2 = parts[1].strip()

        # Проверяем, что категории не пустые
        if not category1 or not category2:
            return "Другое | Необходимость"

        return f"{category1} | {category2}"

    def batch_classify(self, spending_texts: list[str]) -> list[str]:
        """
        Классифицирует несколько трат за один вызов.

        Args:
            spending_texts: Список текстовых описаний трат

        Returns:
            Список категорий для каждой траты
        """
        results = []
        for text in spending_texts:
            try:
                result = self.classify(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при классификации '{text}': {e}")
                results.append("Другое | Необходимость")

        return results


# Функция для быстрого создания агента
def create_spending_classifier(credentials: Optional[str] = None) -> SpendingClassifierAgent:
    """
    Создает и возвращает экземпляр агента-классификатора.

    Args:
        credentials: Токен GigaChat (опционально)

    Returns:
        SpendingClassifierAgent instance
    """
    return SpendingClassifierAgent(credentials=credentials)


# Пример использования и тестирования
if __name__ == "__main__":
    # Тестирование агента
    def test_agent():
        """Тестирует работу агента с примерными данными."""
        try:
            # Создаем агента
            agent = create_spending_classifier()
            print("✅ Агент успешно создан")

            # Тестовые примеры
            test_cases = [
                "Купил кофе в Starbucks",
                "Оплатил проездной на метро",
                "Заправил полный бак бензина",
                "Купил билеты в кино",
                "Оплатил курсы английского",
                "Купил новую подушку для сна"
            ]

            print("\n🧪 Тестирование классификации:")
            print("-" * 50)

            for i, test_case in enumerate(test_cases, 1):
                result = agent.classify(test_case)
                print(f"{i}. '{test_case}'")
                print(f"   → {result}")
                print()

            print("✅ Тестирование завершено успешно")

        except Exception as e:
            print(f"❌ Ошибка при тестировании: {e}")
            print("\n💡 Советы по устранению проблем:")
            print("1. Проверьте переменную окружения GIGACHAT_CREDENTIALS")
            print("2. Убедитесь, что токен активен и имеет достаточные права")
            print("3. Проверьте подключение к интернету")
            print("4. Убедитесь, что установлены все зависимости: pip install langchain langchain-community")
