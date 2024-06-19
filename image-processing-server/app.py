import datetime

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return {"status": "success", "message": "Healthy", "current": datetime.datetime.now()}


@socketio.on('message')
def handle_message(message):
    data = json.loads(message)
    # Handle signaling data
    emit('message', json.dumps({'response': 'received'}), broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, log_output=True, use_reloader=False, allow_unsafe_werkzeug=True)
