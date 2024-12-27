import socket, random

def get_free_port():
    while True:
        port = random.randint(1024, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue

def get_remote_address_from_websockets(websocket):
    ip, port, *_ = websocket.remote_address
    if ip == '::1':
        ip = '127.0.0.1'
    return (ip, port)

def get_local_address_from_websockets(websocket):
    ip, port, *_ = websocket.local_address
    if ip == '::1':
        ip = '127.0.0.1'
    return (ip, port)