import socket
import cv2


def client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Get local machine name
    host = '127.0.0.1'
    port = 9999
    # Connection to hostname on the port
    client_socket.connect((host, port))

    cap = cv2.VideoCapture(1)  # Use 0 for the webcam

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        data = buffer.tobytes()
        length = len(data)
        client_socket.sendall(str(length).ljust(16).encode('utf-8'))
        client_socket.sendall(data)

        cv2.imshow('Client Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    client_socket.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    client()
