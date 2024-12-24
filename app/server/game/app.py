import json, time, threading, socket
from game.item import *

WIDTH, HEIGHT = 1000, 800
PADDLE_WIDTH, PADDLE_HEIGHT = 20, 100
BALL_RADIUS = 7

class Game_Server():
    def __init__(self, left_client_sockets: set, right_client_sockets: set):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.settimeout(5)
        self.server.setblocking(False)
        self.lock = threading.Lock()
        self.left_paddles = dict()
        self.right_paddles = dict()
        self.ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_RADIUS)
        self.left_score = 0
        self.right_score = 0
        self.is_running = True
        self.client_address = None
        self.server_address = ("0.0.0.0", 5555)
        self.client_listener = SocketThread(self.server_address, self, threading.Lock())
        self.client_listener.start()
        self.client_sockets = left_client_sockets.union(right_client_sockets)
        self.data = None
        for client_socket in left_client_sockets:
            client_ip, client_port, *_ = client_socket.remote_address
            self.left_paddles[f"{client_ip}:{client_port}"] = Paddle(10, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        for client_socket in right_client_sockets: 
           client_ip, client_port, *_ = client_socket.remote_address
           self.right_paddles[f"{client_ip}:{client_port}"] = Paddle(WIDTH - 10 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.update_interval = 0.016
    
    def run(self):
        try:
            while self.is_running:
                self.game_loop()
                self.handle_client()
        except Exception as e:
            print(f"[ERROR] {e}")
    
    def game_loop(self):
        time.sleep(self.update_interval)
        self.ball.move()
        self.handle_collision()

        if self.ball.x < 0:
            self.right_score += 1
            self.ball.reset()
        elif self.ball.x > WIDTH:
            self.left_score += 1
            self.ball.reset()

        game_state = {
            "ball": (self.ball.x, self.ball.y),
            "left_paddles": [(paddle.x, paddle.y) for paddle in self.left_paddles.values()],
            "right_paddles": [(paddle.x, paddle.y) for paddle in self.right_paddles.values()],
            "left_score": self.left_score,
            "right_score": self.right_score
        }

        for client_socket in self.client_sockets:
            client_ip, client_port, *_ = client_socket.remote_address
            self.server.sendto(json.dumps(game_state).encode(), ("127.0.0.1", client_port))
    
    def handle_client(self):
        with self.lock:
            print(self.client_address)
            if self.client_address in self.left_paddles:
                if self.data == "MOVE_LEFT_UP":
                    self.left_paddles[self.client_address].move(up=True)
                elif self.data == "MOVE_LEFT_DOWN":
                    self.left_paddles[self.client_address].move(up=False)

            if self.client_address in self.right_paddles:
                if self.data == "MOVE_RIGHT_UP":
                    self.right_paddles[self.client_address].move(up=True)
                elif self.data == "MOVE_RIGHT_DOWN":
                    self.right_paddles[self.client_address].move(up=False)

    def handle_collision(self):
        if self.ball.y + self.ball.radius >= HEIGHT:
            self.ball.y_vel *= -1
        elif self.ball.y - self.ball.radius <= 0:
            self.ball.y_vel *= -1

        for paddle in list(self.left_paddles.values()) + list(self.right_paddles.values()):
            if self.ball.x_vel < 0:
                if self.ball.y >= paddle.y and self.ball.y <= paddle.y + paddle.height:
                    if self.ball.x - self.ball.radius <= paddle.x + paddle.width:
                        self.ball.x_vel *= -1
                        middle_y = paddle.y + paddle.height / 2
                        difference_in_y = middle_y - self.ball.y
                        reduction_factor = (paddle.height / 2) / self.ball.MAX_VEL
                        y_vel = difference_in_y / reduction_factor
                        self.ball.y_vel = -1 * y_vel

            if self.ball.y >= paddle.y and self.ball.y <= paddle.y + paddle.height:
                if self.ball.x + self.ball.radius >= paddle.x:
                    self.ball.x_vel *= -1
                    middle_y = paddle.y + paddle.height / 2
                    difference_in_y = middle_y - self.ball.y
                    reduction_factor = (paddle.height / 2) / self.ball.MAX_VEL
                    y_vel = difference_in_y / reduction_factor
                    self.ball.y_vel = -1 * y_vel

class SocketThread(threading.Thread):
    def __init__(self, addr, server, lock):
        threading.Thread.__init__(self)
        self.server: Game_Server = server
        self.lock = lock
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(addr)

    def run(self):
        while True:
            try:
                data = self.socket.recvfrom(1024)
                game_state = json.loads(data.decode())
            except socket.timeout:
                print("[INFO] Timeout waiting for server response.")
            except Exception as e:
                print(f"[ERROR] {e}")