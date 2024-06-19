from flask import Flask
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET!!!!!!'
socketio = SocketIO(app, cors_allowed_origins="*")


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    send('Welcome to the server!')


@socketio.on('message')
def handle_message(msg):
    print('Message from client: ' + msg)
    send('Received: ' + msg)


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True,
                 allow_unsafe_werkzeug=True)
