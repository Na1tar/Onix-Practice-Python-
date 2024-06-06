from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, ChatRoom, MessageLog
from datetime import datetime
import random
import os

# Create Flask app
app = Flask(__name__)
# Configure the secret key
app.config['SECRET_KEY'] = 'your_secret_key'
# Configure the database URI for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
# Disable SQLAlchemy modification tracking
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)
# Initialize SocketIO with the app
socketio = SocketIO(app)

# Create all tables in the database
with app.app_context():
    db.create_all()

# Main page
@app.route('/')
def index():
    return render_template('index.html')

# Handle login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        # Check password
        if check_password_hash(user.password_hash, password):
            session['username'] = username
            session['color'] = random_color()
            return redirect(url_for('chat'))
        else:
            return 'Invalid credentials'
    else:
        return render_template('register.html', username=username)

# Handle registration
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    # Hash the password
    password_hash = generate_password_hash(password)
    # Create a new user
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    session['username'] = username
    session['color'] = random_color()
    return redirect(url_for('chat'))

# Chat page
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'], color=session['color'])

# Handle joining a room
@socketio.on('join')
def on_join(data):
    username = session['username']
    room = data['room']
    join_room(room)
    send({'msg': f'{username} has entered the room.', 'color': session['color']}, room=room)
    log_message(room, f'{username} has entered the room.')

# Handle leaving a room
@socketio.on('leave')
def on_leave(data):
    username = session['username']
    room = data['room']
    leave_room(room)
    send({'msg': f'{username} has left the room.', 'color': session['color']}, room=room)
    log_message(room, f'{username} has left the room.')

# Handle messages
@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    username = session['username']
    send({'msg': f'{username}: {msg}', 'color': session['color']}, room=room)
    log_message(room, f'{username}: {msg}')

# Function to choose a random color
def random_color():
    COLORS = ['#FF5733', '#33FF57', '#3357FF', '#F333FF', '#33FFF2']
    return random.choice(COLORS)

# Function to log messages
def log_message(room, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(f'logs/{room}.log', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

# Main function
if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    # Run the app
    socketio.run(app, debug=True)
