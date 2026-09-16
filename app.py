import os
import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

USERS_FILE = 'users.json'
HISTORY_FILE = 'chat_history.json'

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('login')
def handle_login(data):
    users = load_json(USERS_FILE)
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username]['password'] == password:
        emit('login_success', {
            'username': username,
            'name': users[username]['name'],
            'avatar': users[username]['avatar']
        })
    else:
        emit('login_fail', {'message': '帳號或密碼錯誤！'})

@socketio.on('register')
def handle_register(data):
    users = load_json(USERS_FILE)
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    avatar = data.get('avatar', '')

    if username in users:
        emit('register_fail', {'message': '此帳號已被註冊！'})
    else:
        users[username] = {
            'password': password,
            'name': name,
            'avatar': avatar
        }
        save_json(USERS_FILE, users)
        emit('register_success', {'message': '註冊成功！請登入。'})

@socketio.on('update_profile')
def handle_update_profile(data):
    users = load_json(USERS_FILE)
    username = data.get('username')
    if username in users:
        users[username]['name'] = data.get('name')
        users[username]['avatar'] = data.get('avatar')
        save_json(USERS_FILE, users)
        emit('update_success', {
            'message': '資料修改成功！',
            'name': users[username]['name'],
            'avatar': users[username]['avatar']
        })
    else:
        emit('update_fail', {'message': '更新失敗，找不到使用者'})

@socketio.on('send_message')
def handle_send_message(data):
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list):
        history = []
    
    msg_id = str(len(history) + 1)
    message_item = {
        'id': msg_id,
        'type': data.get('type'),
        'sender': data.get('sender'),
        'senderName': data.get('senderName'),
        'avatar': data.get('avatar'),
        'content': data.get('content'),
        'edited': False
    }
    history.append(message_item)
    save_json(HISTORY_FILE, history)
    emit('receive_message', message_item, broadcast=True)

@socketio.on('edit_message')
def handle_edit_message(data):
    history = load_json(HISTORY_FILE)
    msg_id = data.get('id')
    new_content = data.get('content')
    
    for item in history:
        if item['id'] == msg_id:
            item['content'] = new_content
            item['edited'] = True
            break
            
    save_json(HISTORY_FILE, history)
    emit('message_edited', {'id': msg_id, 'content': new_content}, broadcast=True)

@socketio.on('delete_message')
def handle_delete_message(data):
    history = load_json(HISTORY_FILE)
    msg_id = data.get('id')
    
    global history_updated
    history = [item for item in history if item['id'] != msg_id]
    save_json(HISTORY_FILE, history)
    emit('message_deleted', {'id': msg_id}, broadcast=True)

@socketio.on('clear_history')
def handle_clear_history(data):
    if data.get('password') == '0617':
        save_json(HISTORY_FILE, [])
        emit('history_cleared', broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
