from flask import Flask
import socketio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET!!'

sio = socketio.Client()


@sio.event
def connect():
    print('Connection established')
    sio.send('Hello from the client!')


@sio.event
def message(data):
    print('Message from server:', data)


@sio.event
def disconnect():
    print('Disconnected from server')


@app.route('/')
def index():
    return 'Client App Running'


if __name__ == '__main__':
    sio.connect('http://127.0.0.1:5000')
    app.run(host='0.0.0.0', port=5001)
