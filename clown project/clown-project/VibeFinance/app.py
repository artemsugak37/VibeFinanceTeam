from flask import Flask, request, jsonify
import hashlib
import sqlite3
import os

from langchain_gigachat.chat_models import GigaChat
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import Dict, Any

from classificator import SpendingClassifierAgent

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
                        amount REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
        conn.commit()
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    with open('clown-project/VibeFinance/main.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'Все поля обязательны'})

    # Проверяем длину пароля
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Проверяем, существует ли уже такой email
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Пользователь с таким email уже существует'})

        # Регистрируем нового пользователя
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
        password_hash = hash_password(password)

        if password_hash == stored_hash:
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

@app.route('/send_message', methods=['POST'])
def handle_message():
    data = request.get_json()
    user_id = data.get('user_id')
    description = data.get('message', '').strip()
    amount = data.get('amount')  # может быть null

    if not user_id or not description:
        return jsonify({'success': False, 'message': 'Не указан пользователь или описание траты'})

    # Проверим, существует ли пользователь
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

    # Классифицируем трату
    classifier = SpendingClassifierAgent()
    try:
        classification = classifier.classify(description).strip()
        if " | " not in classification:
            raise ValueError("Неверный формат ответа от модели")
        main_cat, psych_cat = map(str.strip, classification.split(" | ", 1))
    except Exception as e:
        print(f"Classification error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при классификации траты'})

    # Сохраняем в базу
    try:
        cursor.execute('''
                INSERT INTO spendings (user_id, description, category_main, category_psych, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, description, main_cat, psych_cat, amount))
        conn.commit()
        conn.close()
        print('Все гуд сохранено')
    except Exception as e:
        print(f"Database save error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при сохранении траты'})

    return jsonify({
        'success': True,
        'message': 'Трата успешно сохранена',
        'classification': f"{main_cat} | {psych_cat}"
    })

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