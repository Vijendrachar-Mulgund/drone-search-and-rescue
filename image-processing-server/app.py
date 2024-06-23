import socket
import cv2
import numpy as np


def init_server():
    # Create a socket object
    s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = '0.0.0.0'
    port = 9999

    # Bind to the port
    s_socket.bind((host, port))
    # Queue up to 5 requests
    s_socket.listen(5)

    print("Server listening on {}:{}".format(host, port))

    # Establish a connection
    c_socket, addr = s_socket.accept()
    print("Got a connection from {}".format(addr))
    return c_socket, s_socket


def process_data(client_conn, server_conn):
    while True:
        # Receive data from the client
        length = client_conn.recv(16)
        if not length:
            break
        length = int(length.decode('utf-8'))

        data = b''
        while len(data) < length:
            packet = client_conn.recv(length - len(data))
            if not packet:
                break
            data += packet

        frame_data = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

        # Apply the YOLOv8 model for Object detection
        if frame is not None:
            # Apply grayscale filter
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

            ret, buffer = cv2.imencode('.jpg', gray_frame)
            if ret:
                length = len(buffer)
                client_conn.sendall(str(length).ljust(16).encode('utf-8'))
                client_conn.sendall(buffer.tobytes())

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_conn.close()
    server_conn.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        # Re-establish the server after a client disconnects
        while True:
            client_socket, server_socket = init_server()
            process_data(client_socket, server_socket)
    except KeyboardInterrupt:
        print("Server shut down 🛑")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"An error occurred {e}")
