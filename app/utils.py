import socket, random
import websockets

def get_free_port():
    while True:
        port = random.randint(1024, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue

def get_address_from_websockets(websocket):
    ip, port, *_ = websocket.remote_address
    return (ip, port)