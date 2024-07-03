import socket
import cv2
import sys

import numpy as np

from config import (SERVER_ADDRESS, IMAGE_ENCODE_DECODE_FORMAT, SOCKET_TRANSMISSION_SIZE,
                    VIDEO_IMAGE_ENCODE_DECODE_FORMAT, VIDEO_SOURCE)


def video_capture(client_conn, vid_source):
    cap = cv2.VideoCapture(vid_source if vid_source is not None else VIDEO_SOURCE)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        ret, buffer = cv2.imencode(VIDEO_IMAGE_ENCODE_DECODE_FORMAT, frame)
        if not ret:
            continue

        data = buffer.tobytes()
        length = len(data)
        client_conn.sendall(str(length).ljust(SOCKET_TRANSMISSION_SIZE).encode(IMAGE_ENCODE_DECODE_FORMAT))
        client_conn.sendall(data)

        # Receive processed frame from server
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
        processed_frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

        if processed_frame is not None:
            cv2.imshow('Client Video - Grayscale', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    client_conn.close()
    cv2.destroyAllWindows()


def init_client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(SERVER_ADDRESS)
    return client_socket


def get_params(cmd_params):
    params_dict = {}
    for i in range(1, len(cmd_params), 2):
        params_dict[cmd_params[i]] = cmd_params[i + 1]
    return params_dict


if __name__ == "__main__":
    try:
        params = get_params(sys.argv)
        socket_connection = init_client()
        video_capture(socket_connection, params["-source"])
    except KeyboardInterrupt:
        print("Client shutting down 🛑")
    except Exception as e:
        print("An error occurred: {}".format(e))
