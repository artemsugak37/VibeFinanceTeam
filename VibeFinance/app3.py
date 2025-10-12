from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    with open('main3.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/send_message', methods=['POST'])
def handle_message():
    data = request.get_json()
    user_message = data.get('message', '')
    print(f"Received message: {user_message}")
    return jsonify({'status': 'received'})

if __name__ == '__main__':
    app.run(debug=True)