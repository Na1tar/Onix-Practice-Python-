from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, ChatRoom, MessageLog
from datetime import datetime
import random
import os

# Створення додатку Flask
app = Flask(__name__)
# Конфігурація секретного ключа
app.config['SECRET_KEY'] = 'your_secret_key'
# Налаштування URI для підключення до бази даних SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
# Вимкнення відстеження модифікацій SQLAlchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ініціалізація бази даних з додатком
db.init_app(app)
# Ініціалізація SocketIO з додатком
socketio = SocketIO(app)

# Створення всіх таблиць у базі даних
with app.app_context():
    db.create_all()

# Головна сторінка
@app.route('/')
def index():
    return render_template('index.html')

# Обробка логіну
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        # Перевірка паролю
        if check_password_hash(user.password_hash, password):
            session['username'] = username
            session['color'] = random_color()
            return redirect(url_for('chat'))
        else:
            return 'Invalid credentials'
    else:
        return render_template('register.html', username=username)

# Обробка реєстрації
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    # Хешування паролю
    password_hash = generate_password_hash(password)
    # Створення нового користувача
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    session['username'] = username
    session['color'] = random_color()
    return redirect(url_for('chat'))

# Сторінка чату
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'], color=session['color'])

# Обробка приєднання до кімнати
@socketio.on('join')
def on_join(data):
    username = session['username']
    room = data['room']
    join_room(room)
    send({'msg': f'{username} has entered the room.', 'color': session['color']}, room=room)
    log_message(room, f'{username} has entered the room.')

# Обробка виходу з кімнати
@socketio.on('leave')
def on_leave(data):
    username = session['username']
    room = data['room']
    leave_room(room)
    send({'msg': f'{username} has left the room.', 'color': session['color']}, room=room)
    log_message(room, f'{username} has left the room.')

# Обробка повідомлень
@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    username = session['username']
    send({'msg': f'{username}: {msg}', 'color': session['color']}, room=room)
    log_message(room, f'{username}: {msg}')

# Функція для вибору випадкового кольору
def random_color():
    COLORS = ['#FF5733', '#33FF57', '#3357FF', '#F333FF', '#33FFF2']
    return random.choice(COLORS)

# Функція для логування повідомлень
def log_message(room, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(f'logs/{room}.log', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

# Головна функція
if __name__ == '__main__':
    # Створення директорії для логів, якщо вона не існує
    os.makedirs('logs', exist_ok=True)
    # Запуск додатку
    socketio.run(app, debug=True)
