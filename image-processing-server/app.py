from flask import Flask, Response
from flask_socketio import SocketIO, send
import base64
import numpy as np
import cv2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET!!!!!!'
socketio = SocketIO(app, cors_allowed_origins="*")

frames = []


@socketio.on('frame')
def handle_frame(data):
    global frames
    frame_data = base64.b64decode(data)
    np_data = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    frames.append(frame)


def generate_frames():
    global frames
    while True:
        if frames:
            frame = frames.pop(0)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return "Hello World!"


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


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
