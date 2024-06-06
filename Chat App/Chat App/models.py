from flask_sqlalchemy import SQLAlchemy

# Ініціалізація бази даних
db = SQLAlchemy()

# Модель користувача
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

# Модель кімнати чату
class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# Модель логів повідомлень
class MessageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
