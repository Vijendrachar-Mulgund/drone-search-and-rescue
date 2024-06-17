from flask import Flask, Response, render_template, render_template_string
import cv2
import socket
import numpy as np

app = Flask(__name__)


# Client setup to receive video stream
def receive_frames():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 8001))  # Replace with your server's IP address

    data = b""
    while True:
        try:
            while True:
                data += client_socket.recv(4096)
                start = data.find(b'\xff\xd8')  # JPEG start
                end = data.find(b'\xff\xd9')  # JPEG end
                if start != -1 and end != -1:
                    jpg = data[start:end + 2]
                    data = data[end + 2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    break
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error receiving frame: {e}")
            break
    client_socket.close()


@app.route('/video_feed')
def video_feed():
    return Response(receive_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
