import socket
import cv2
import random
import numpy as np
import threading
import queue
from flask import Flask, Response
from ultralytics import YOLO

app = Flask(__name__)

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9999
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)
SERVER_MAX_QUEUE_SIZE = 5
IMAGE_ENCODE_DECODE_FORMAT = 'utf-8'
VIDEO_IMAGE_ENCODE_DECODE_FORMAT = '.jpg'

# Shared variable to store the most recent frame
current_frame = None
frame_lock = threading.Lock()


# Server Initialization
def init_server():
    # Create a socket object
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind to the port
    socket_server.bind(SERVER_ADDRESS)
    # Queue up to 5 requests
    socket_server.listen(SERVER_MAX_QUEUE_SIZE)

    print("Server listening on {}:{}".format(SERVER_HOST, SERVER_PORT))

    # Establish a connection
    client_connection, client_address = socket_server.accept()

    print("Got a connection from {}".format(client_address))

    receive_video(client_connection, socket_server)

    return client_connection, socket_server


def receive_video(client_conn, server_conn):
    video_id = random.randint(0, 99999)
    model = YOLO("ai-models/dsar_yolo_v8n_1280p.pt")
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    writer = cv2.VideoWriter(f"recordings/{video_id}.mp4", fourcc, 15.0, (1280, 720))
    global current_frame
    while True:
        # Receive data from the client
        length = client_conn.recv(16)
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
            processed_frame = frame_track(frame, model)

            # Record the video / Write the frame
            writer.write(processed_frame)

            # # Add frame to queue, removing old frames if necessary
            # if frame_queue.full():
            #     frame_queue.empty()
            # frame_queue.put(frame)

            # Update current_frame with the new frame
            with frame_lock:
                current_frame = processed_frame

            # Return the frame back to the client / Record the video and store
            ret, buffer = cv2.imencode(VIDEO_IMAGE_ENCODE_DECODE_FORMAT, processed_frame)
            if ret:
                length = len(buffer)
                client_conn.sendall(str(length).ljust(16).encode(IMAGE_ENCODE_DECODE_FORMAT))
                client_conn.sendall(buffer.tobytes())

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_conn.close()
    server_conn.close()
    cv2.destroyAllWindows()


def generate_frames():
    global current_frame
    while True:
        with frame_lock:
            if current_frame is not None:
                frame = current_frame.copy()
            else:
                continue

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def frame_track(frame, model):
    # Apply filter / Run the frame through a model
    # Apply the YOLOv8 model for Object detection
    result = model.track(frame)
    print("Result Length: {}".format(len(result)))
    print("Result: {}".format(result[0]))
    updated_frame = result[0].plot()

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


if __name__ == "__main__":
    try:
        # Start frame receiving thread
        receive_thread = threading.Thread(target=init_server)
        receive_thread.daemon = True
        receive_thread.start()

        # Run Flask app
        app.run(host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        print("Server shut down 🛑")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"An error occurred {e}")
