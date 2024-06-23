import socket
import cv2
import numpy as np

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9999
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)
SERVER_MAX_QUEUE_SIZE = 5
IMAGE_ENCODE_DECODE_FORMAT = 'utf-8'
VIDEO_IMAGE_ENCODE_DECODE_FORMAT = '.jpg'


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
    return client_connection, socket_server


def receive_video(client_conn, server_conn):
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
            processed_frame = process_frame(frame)

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


def process_frame(image_frame):
    # Apply filter / Run the frame through a model
    # Apply the YOLOv8 model for Object detection
    gray_frame = cv2.cvtColor(image_frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
    return gray_frame


if __name__ == "__main__":
    try:
        # Re-establish the server after a client disconnects
        while True:
            client_socket, server_socket = init_server()
            receive_video(client_socket, server_socket)
    except KeyboardInterrupt:
        print("Server shut down 🛑")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"An error occurred {e}")
