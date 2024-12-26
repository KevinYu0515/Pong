import socket
from .items import *
import threading, json, time
import argparse
from .constants import *

class Game_Server():
    def __init__(self, addr, left_client_address, right_client_address, left_paddles, right_paddles, winning_points=10):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.left_client_address = left_client_address
        self.right_client_address = right_client_address
        self.lock = threading.Lock()
        self.recevier = SocketThread(addr, self, self.lock)
        self.recevier.start()
        self.update_time = 0.01

        self.winning_points = winning_points
        self.ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 10)
        self.comming_data = None
        self.data = {
            "left_paddles": [],
            "right_paddles": [],
            "ball": {
                "x": 0, "y": 0
            },
            "left_score": 0,
            "right_score": 0,
            "won": False,
            "win_text": ''
        }

        for paddle in left_paddles:
            start_x = 10 + int(paddle.get('position')) * 100
            self.data.get('left_paddles').append({"x": start_x, "y": PADDLE_HEIGHT // 2, "width": PADDLE_WIDTH, "height": PADDLE_HEIGHT})
        
        for paddle in right_paddles:
            start_x = SCREEN_WIDTH - 10 - PADDLE_WIDTH - int(paddle.get('position')) * 100
            self.data.get('right_paddles').append({"x": start_x, "y": PADDLE_HEIGHT // 2, "width": PADDLE_WIDTH, "height": PADDLE_HEIGHT})

        self.is_running = True
    
    def run(self):
        while self.is_running:
            time.sleep(self.update_time)
            self.handle_client()
            self.ball.move()
            self.handle_collision()

            if self.ball.x < 0:
                self.data['right_score'] =  self.data.get('right_score') + 1
                self.ball.reset()
            elif self.ball.x > SCREEN_WIDTH:
                self.data['left_score'] = self.data.get('left_score') + 1
                self.ball.reset()

            if self.data.get('left_score') >= self.winning_points:
                self.data['won'] = True
                self.data['win_text'] = "Left Player Won!"
            elif self.data.get('right_score') >= self.winning_points:
                self.data['won'] = True
                self.data['win_text'] = "Right Player Won!"

            if self.data.get('won'):
                self.is_running = False

            self.data['ball'] = {"x": self.ball.x, "y": self.ball.y}
            self.sendTo()

    def handle_client(self):
        if self.comming_data:
            with self.lock:
                side, idx = self.comming_data.get('side'), self.comming_data.get('idx')
                if side == 'left':
                    self.data.get('left_paddles')[idx]['y'] = self.comming_data.get('y')
                elif side == 'right':
                    self.data.get('right_paddles')[idx]['y'] = self.comming_data.get('y')
                self.comming_data = None
            
    def sendTo(self):
        for client_address in self.left_client_address + self.right_client_address:
            self.server.sendto(json.dumps(self.data).encode(), client_address)

    def handle_collision(self):
        if self.ball.y + self.ball.radius >= SCREEN_HEIGHT:
            self.ball.y_vel *= -1
        elif self.ball.y - self.ball.radius <= 0:
            self.ball.y_vel *= -1

        if self.ball.x_vel < 0:
            for paddle in self.data.get('left_paddles'):
                paddle = Paddle(paddle.get('x'), paddle.get('y'), paddle.get('width'), paddle.get('height'))
                if self.ball.y >= paddle.y and self.ball.y <= paddle.y + paddle.height:
                    if self.ball.x - self.ball.radius <= paddle.x + paddle.width:
                        self.ball.x_vel *= -1
                        middle_y = paddle.y + paddle.height / 2
                        difference_in_y = middle_y - self.ball.y
                        reduction_factor = (paddle.height / 2) / self.ball.MAX_VEL
                        y_vel = difference_in_y / reduction_factor
                        self.ball.y_vel = -1 * y_vel

        for paddle in self.data.get('right_paddles'):
            paddle = Paddle(paddle.get('x'), paddle.get('y'), paddle.get('width'), paddle.get('height'))
            if self.ball.y >= paddle.y and self.ball.y <= paddle.y + paddle.height:
                if self.ball.x + self.ball.radius >= paddle.x:
                    self.ball.x_vel *= -1
                    middle_y = paddle

class SocketThread(threading.Thread):
    def __init__(self, addr, server, lock):
        threading.Thread.__init__(self)
        self.server: Game_Server = server
        self.lock = lock
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(addr)

    def run(self):
        while True:
            print("Listening from players...")
            data, addr = self.socket.recvfrom(1024)
            self.client_address = addr
            self.server.comming_data = json.loads(data.decode())

if __name__ == "__main__":
    left_paddles = [{"position": 0}, {"position": 1}]
    right_paddles = [{"position": 0}, {"position": 1}]

    parser = argparse.ArgumentParser(description='Pong Game Server')
    parser.add_argument("--left", type=str, required=True, help="Comma-separated list of left client ports (e.g., '1234,2345')")
    parser.add_argument("--right", type=str, required=True, help="Comma-separated list of right client ports (e.g., '2222,1212')")
    
    args = parser.parse_args()
    left_ports = [int(port) for port in args.left.split(',')]
    right_ports = [int(port) for port in args.right.split(',')]

    left_client_address = [('127.0.0.1', left_ports[i]) for i in range(len(left_ports))]
    right_client_address = [('127.0.0.1', right_ports[i]) for i in range(len(right_ports))]
    print(left_client_address, right_client_address)
    
    server = Game_Server(("0.0.0.0", 5555), left_client_address, right_client_address, left_paddles, right_paddles)
    server.run()