# app_sender.py
from flask import Flask, Response, stream_with_context
from dotenv import load_dotenv
from os import getenv
import cv2

# Load the environment variables
load_dotenv()

# Init the Flask Application
app = Flask(__name__)

VIDEO_CAPTURE = 1


def generate_frames():
    camera = cv2.VideoCapture(VIDEO_CAPTURE)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_stream', methods=['GET'])
def video_stream():
    return Response(stream_with_context(generate_frames()), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    print("The Raspberry Pi - Video Stream server has started 🚀")
    port = int(getenv("PORT", 8001))
    host = getenv("HOST", "0.0.0.0")
    app.run(debug=True, port=port, host=host)
