from flask import Flask, request, jsonify
import hashlib
import sqlite3
import os
import secrets

from langchain_gigachat.chat_models import GigaChat
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import Dict, Any

from classificator import SpendingClassifierAgent
from workflow import spending_graph

# Функции для работы с паролями - ИСПРАВЛЕННЫЕ
def hash_password(password: str) -> str:
    """Хеширование пароля с использованием соли"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode(), 
        salt.encode(), 
        100000
    ).hex()
    return f"{password_hash}:{salt}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Проверка пароля против хеша"""
    try:
        stored_hash, salt = hashed_password.split(':')
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
        return secrets.compare_digest(new_hash, stored_hash)
    except (ValueError, AttributeError):
        return False

load_dotenv()

gigachat_credentials = os.getenv("GIGACHAT_CREDENTIALS")

giga = GigaChat(
    credentials = f"{gigachat_credentials}",
    verify_ssl_certs = False
)

app = Flask(__name__)

# Создаем базу данных при запуске
def init_db():
    if not os.path.exists('users.db'):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE spendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                category_main TEXT NOT NULL,
                category_psych TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_description TEXT,
                parsed_description TEXT,
                confidence REAL,
                parsed_date DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()
        print("База данных users.db создана с новой структурой.")
    else:
        print("Файл users.db уже существует.")

@app.route('/')
def index():
    with open('VibeFinance/main.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'Все поля обязательны'})

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Пользователь с таким email уже существует'})

        # Регистрируем нового пользователя - ЭТО ПРАВИЛЬНО
        password_hash = hash_password(password)
        cursor.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                       (name, email, password_hash))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Регистрация успешна'})

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при регистрации'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'success': False, 'message': 'Email и пароль обязательны'})

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})

        user_id, name, stored_hash = user
        
        # ИСПРАВЛЕНИЕ: используем verify_password вместо hash_password
        if verify_password(password, stored_hash):
            return jsonify({
                'success': True,
                'message': 'Вход успешен',
                'user_id': user_id,
                'name': name
            })
        else:
            return jsonify({'success': False, 'message': 'Неверный пароль'})

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при входе'})

# ... остальной код без изменений (send_message, get_spendings и т.д.)

@app.route('/send_message', methods=['POST'])
def handle_message():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message', '').strip() # <-- Теперь только message

    # Проверяем наличие user_id и message
    if not user_id or not message:
        return jsonify({'success': False, 'message': 'Нужны описание и пользователь'})

    # Проверка существования пользователя (остаётся)
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
    except Exception as e:
        print(f"User check error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка проверки пользователя'})

    # 🔁 Запуск LangGraph workflow
    # initial_state теперь содержит original_description вместо description и amount
    initial_state = {"original_description": message, "user_id": user_id}
    try:
        final_state = spending_graph.invoke(initial_state)
        # Теперь final_state содержит amount, main_category, psych_category, parsed_date и т.д.
        amount = final_state["amount"]
        main_cat = final_state["main_category"]
        psych_cat = final_state["psych_category"]
        parsed_date = final_state["parsed_date"]
        original_description = final_state["original_description"]
        parsed_description = final_state.get("parsed_description", "")
        confidence = final_state.get("confidence", 0.0)
        advice = final_state["advice"] # <-- Это advice от FinancialPsychologistAgent, основанный на трате

        # Сохранение в БД
        try:
            # Используем parsed_date, который уже подготовлен в workflow
            cursor.execute('''
                INSERT INTO spendings (
                    user_id, description, category_main, category_psych, amount, timestamp, original_description, parsed_description, confidence, parsed_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                original_description, # <-- Сохраняем оригинальное описание
                main_cat,
                psych_cat,
                amount,
                parsed_date, # <-- Сохраняем извлечённую или текущую дату
                original_description, # <-- Поле original_description
                parsed_description, # <-- Поле parsed_description
                confidence, # <-- Поле confidence
                parsed_date # <-- Поле parsed_date
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB error: {e}")
            return jsonify({'success': False, 'message': 'Ошибка сохранения в базу'})

        # Возвращаем успешный ответ клиенту
        # Можно включить извлечённую сумму и дату в ответ, если нужно отобразить
        return jsonify({
            'success': True,
            'classification': f"{main_cat} | {psych_cat}",
            'advice': advice,
            'amount': amount, # <-- Отправляем извлечённую сумму
            'timestamp': parsed_date, # <-- Отправляем дату
            'is_spending': True # <-- Индикатор, что это была трата
        })

    except ValueError as ve: # Ловим ошибки из classify_spending
        print(f"Classification/Value error: {ve}")
        # Если classify_spending не нашёл сумму -> это НЕ трата
        conn.close() # Закрываем соединение, т.к. трату не сохраняем
    except Exception as e:
        print(f"Workflow error: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        # Попробуем обработать как общий запрос, чтобы не терять сообщение пользователя
        print("Treating as general query due to workflow error.")

    # Если мы дошли до этой точки, это НЕ трата
    # Вызываем психолога для общего ответа
    try:
        # Создаём экземпляр психолога (предполагается, что файл называется psychologist_agent.py)
        from psychologist_agent import FinancialPsychologistAgent
        local_psychologist = FinancialPsychologistAgent()
        general_advice = local_psychologist.respond_to_general_query(message)
        return jsonify({
            'success': True, # <-- Важно: возвращаем success: True для общего ответа
            'advice': general_advice, # <-- Ответ ИИ, не основанный на трате
            'is_spending': False # <-- Индикатор, что это был общий запрос
            # 'timestamp': datetime.now().isoformat() # <-- Можно добавить, если нужно
        })
    except Exception as e:
        print(f"Psychologist agent error for general query: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Ошибка при обработке запроса психологом.'})

@app.route('/get_spendings/<int:user_id>', methods=['GET'])
def get_spendings(user_id):
    try:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row  # чтобы можно было обращаться по имени колонки
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, description, category_main, category_psych, amount, timestamp
            FROM spendings
            WHERE user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()

        spendings = [dict(row) for row in rows]
        return jsonify({'success': True, 'spendings': spendings})
    except Exception as e:
        print(f"Fetch spendings error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при загрузке трат'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)