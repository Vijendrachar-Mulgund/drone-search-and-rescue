import socket
import cv2
import numpy as np

SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999
SERVER_ADDRESS = (SERVER_IP, SERVER_PORT)
IMAGE_ENCODE_DECODE_FORMAT = 'utf-8'
VIDEO_IMAGE_ENCODE_DECODE_FORMAT = '.jpg'
# VIDEO_SOURCE = 1  # 1 - FaceTime camera | 0 - Raspberry Pi camera
VIDEO_SOURCE = "drone_footages/drone_footage_13.mp4"


def video_capture(client_conn):
    cap = cv2.VideoCapture(VIDEO_SOURCE)  # Use 0 for the webcam
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    #
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        print("Res ", str(frame.shape))

        if not ret:
            break

        ret, buffer = cv2.imencode(VIDEO_IMAGE_ENCODE_DECODE_FORMAT, frame)
        if not ret:
            continue

        data = buffer.tobytes()
        length = len(data)
        client_conn.sendall(str(length).ljust(16).encode(IMAGE_ENCODE_DECODE_FORMAT))
        client_conn.sendall(data)

        # Receive processed frame from server
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


if __name__ == "__main__":
    try:
        socket_connection = init_client()
        video_capture(socket_connection)
    except KeyboardInterrupt:
        print("Client shutting down 🛑")
    except Exception as e:
        print("An error occurred: {}".format(e))
