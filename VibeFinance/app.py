from flask import Flask, request, jsonify
import hashlib
import sqlite3
import os

from langchain_gigachat.chat_models import GigaChat
from dotenv import load_dotenv

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
        conn.commit()
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    with open('main.html', 'r', encoding='utf-8') as f:
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
            return jsonify({'success': True, 'message': 'Вход успешен'})
        else:
            return jsonify({'success': False, 'message': 'Неверный пароль'})

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при входе'})


@app.route('/send_message', methods=['POST'])
def handle_message():
    data = request.get_json()
    user_message = data.get('message', '')
    print(f"Received message: {user_message}")
    return jsonify({'status': 'received'})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)