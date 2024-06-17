import cv2
import socket
import time
import logging


def generate_frames():
    camera = cv2.VideoCapture(1)  # Change to 1 if your default camera is at index 1
    while True:
        start_time = time.time()
        success, frame_camera = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame_camera)
            frame_camera = buffer.tobytes()
            # Concatenate frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_camera + b'\r\n')
            elapsed_time = time.time() - start_time
            logging.debug(f"Frame generation time: {elapsed_time} seconds")


# Setup socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 8001))
server_socket.listen(0)

print("Server listening on port 8485")

# Accept a single connection
connection, address = server_socket.accept()
print(f"Connection from: {address}")

for frame in generate_frames():
    connection.sendall(frame)

connection.close()
server_socket.close()
