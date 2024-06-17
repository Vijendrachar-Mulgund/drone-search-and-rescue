import cv2
import socket
import time
import logging

SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080
SERVER_ADDRESS = (SERVER_IP, SERVER_PORT)
VIDEO_SOURCE = 1
VIDEO_IMAGE_FORMAT = '.jpg'
SOCKET_LISTEN_BACKLOG = 0


def generate_frames():
    camera = cv2.VideoCapture(VIDEO_SOURCE)
    while True:
        start_time = time.time()
        success, frame_camera = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode(VIDEO_IMAGE_FORMAT, frame_camera)
            frame_camera = buffer.tobytes()
            # Concatenate frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_camera + b'\r\n')
            elapsed_time = time.time() - start_time
            logging.debug(f"Frame generation time: {elapsed_time} seconds")


def initialize_server():
    # Setup socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(SOCKET_LISTEN_BACKLOG)

    print(f"Server listening on port {SERVER_IP}:{SERVER_PORT}")

    # Accept a single connection
    connection, address = server_socket.accept()

    print(f"Connection from: {address}")

    for frame in generate_frames():
        connection.sendall(frame)

    connection.close()
    server_socket.close()


if __name__ == '__main__':
    try:
        initialize_server()
    except Exception as e:
        print("An exception occurred: {}".format(e))
