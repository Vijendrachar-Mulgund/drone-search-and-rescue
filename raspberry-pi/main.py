from flask import Flask
import socketio
import cv2
from time import time
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET!!'

sio = socketio.Client()

VIDEO_SOURCE = 1
VIDEO_IMAGE_FORMAT = '.jpg'


def send_video():
    cap = cv2.VideoCapture(1)
    while cap.isOpened():
        start_time = time()
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        sio.emit('frame', frame_data)
        elapsed_time = time() - start_time
        print(f"Frame send time: {elapsed_time} seconds")


@sio.event
def connect():
    print('Connection established')
    sio.start_background_task(target=send_video)


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
