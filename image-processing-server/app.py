import socket
import cv2
import numpy as np


def server():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Get local machine name
    # host = socket.gethostname()
    host = '0.0.0.0'
    port = 9999
    # Bind to the port
    server_socket.bind((host, port))
    # Queue up to 5 requests
    server_socket.listen(5)

    print("Server listening on {}:{}".format(host, port))

    # Establish a connection
    client_socket, addr = server_socket.accept()
    print("Got a connection from {}".format(addr))

    while True:
        # Receive data from the client
        length = client_socket.recv(16)
        if not length:
            break
        length = int(length.decode('utf-8'))

        data = b''
        while len(data) < length:
            packet = client_socket.recv(length - len(data))
            if not packet:
                break
            data += packet

        frame_data = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow('Server Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_socket.close()
    server_socket.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    server()
