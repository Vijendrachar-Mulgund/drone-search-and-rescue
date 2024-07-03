import socket
import cv2
import numpy as np
import threading
import uuid
import os
import signal

from flask import Flask, Response
from ultralytics import YOLO

from config import (SERVER_HOST, SERVER_SOCKET_PORT, SERVER_FLASK_PORT, SERVER_SOCKET_ADDRESS, SERVER_MAX_QUEUE_SIZE,
                    IMAGE_ENCODE_DECODE_FORMAT, VIDEO_IMAGE_ENCODE_DECODE_FORMAT,
                    VIDEO_RECORDING_FRAME_RATE, SOCKET_TRANSMISSION_SIZE)

app = Flask(__name__)

# Shared variable to store the most recent frame
current_frame = None
frame_lock = threading.Lock()

# Initialise the YOLO model
model = YOLO("ai-models/dsar_yolo_v8n_1280p.pt")

# Create a new Case ID
case_id = str(uuid.uuid4())


# Server Initialization
def init_socket_server():
    # Create a socket object
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind to the port
    socket_server.bind(SERVER_SOCKET_ADDRESS)
    # Queue up to 5 requests
    socket_server.listen(SERVER_MAX_QUEUE_SIZE)

    print("Server listening on {}:{}".format(SERVER_HOST, SERVER_SOCKET_PORT))

    # Establish a connection
    client_connection, client_address = socket_server.accept()

    print("Got a connection from {}".format(client_address))

    receive_video(client_connection, socket_server)

    return client_connection, socket_server


def receive_video(client_conn, server_conn):
    global current_frame

    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    writer = cv2.VideoWriter(f"recordings/{case_id}.mp4", fourcc, VIDEO_RECORDING_FRAME_RATE, (1280, 720))

    while True:
        # Receive data from the client
        length = client_conn.recv(SOCKET_TRANSMISSION_SIZE)
        if not length:
            break
        length = int(length.decode(IMAGE_ENCODE_DECODE_FORMAT))

        data = b''
        while len(data) < length:
            packet = client_conn.recv(length - len(data))
            if not packet:
                break
            data += packet

        frame_data = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

        if frame is not None:
            # Each frame processed here
            processed_frame = frame_track(frame)

            # Record the video / Write the frame
            writer.write(processed_frame)

            # Update current_frame with the new frame
            with frame_lock:
                current_frame = processed_frame

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_conn.close()
    server_conn.close()
    cv2.destroyAllWindows()
    stop_server()


def generate_frames():
    global current_frame

    # Get each frame for the stream
    while True:
        with frame_lock:
            if current_frame is not None:
                frame = current_frame
            else:
                continue

        # Encode for stream
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Return each frame for stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def frame_track(frame):
    global model
    # Apply the YOLOv8 model for Object detection
    result = model.track(frame)
    updated_frame = result[0].plot()

    # Access confidence scores
    for res in result:
        boxes = res.boxes  # Boxes object for bounding box outputs
        for box in boxes:
            confidence = box.conf.item()  # Confidence score
            obj_cls = box.cls.item()  # class item

            print(f"Confidence: {confidence:.2f}")
            print(f"Class: {obj_cls:.2f}")

    return updated_frame


@app.route('/')
def index():
    return """
        <html>
            <body>
                <h1>Live Video Stream</h1>
                <img width="1280" height="720" src="/video_feed">
            </body>
        </html>
        """


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def stop_server():
    os.kill(os.getpid(), signal.SIGINT)


if __name__ == "__main__":
    try:
        while True:
            # Start Socket server
            receive_thread = threading.Thread(target=init_socket_server)
            receive_thread.daemon = True
            receive_thread.start()

            # Start Flask server
            app.run(host=SERVER_HOST, port=SERVER_FLASK_PORT)

    except KeyboardInterrupt:
        print("Server shut down 🛑")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"An error occurred {e}")
