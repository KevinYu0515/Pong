import socket
from .items import *
import threading, json, time
import argparse
from .constants import *

class Game_Server():
    def __init__(self, addr, left_client_address, right_client_address, left_paddles, right_paddles, winning_points=10, timer=30, mode='normal'):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(False)
        self.is_running = True
        self.timer = Timer(timer)
        self.start_timer = Timer(3)
        self.mode = mode

        self.winning_points = winning_points
        self.ball = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS)]
        self.chaos_timer = Timer(999)

        self.comming_data = None
        self.data = {
            'start_time': 3,
            'timer': timer,
            "left_paddles": [],
            "right_paddles": [],
            "ball": [{"x": 0, "y": 0}],
            "left_score": 0,
            "right_score": 0,
            "won": False,
            "win_text": ''
        }

        for paddle in left_paddles:
            start_x = 10 + (int(paddle.get('position')) - 1) * 100
            self.data.get('left_paddles').append({"x": start_x, "y": SCREEN_HEIGHT // 2, "width": PADDLE_WIDTH, "height": PADDLE_HEIGHT})
        
        for paddle in right_paddles:
            start_x = SCREEN_WIDTH - 10 - PADDLE_WIDTH - (int(paddle.get('position')) - 1) * 100
            self.data.get('right_paddles').append({"x": start_x, "y": SCREEN_HEIGHT // 2, "width": PADDLE_WIDTH, "height": PADDLE_HEIGHT})

        self.left_client_address = left_client_address
        self.right_client_address = right_client_address
        self.lock = threading.Lock()
        self.receiver = SocketThread(addr, self, self.lock)
        self.receiver.daemon = True
        self.receiver.start()
        self.update_time = 0.01
        self.check_address_conn = {}
        for address in left_client_address + right_client_address:
            self.check_address_conn[address] = False

    def run(self):
        last_time = self.timer.countdown_seconds if self.mode == 'normal' else self.chaos_timer.countdown_seconds
        self.data['timer'] = last_time
        while self.is_running:
            time.sleep(self.update_time)
            self.handle_client()
            if all(self.check_address_conn.values()):
                if not self.start_timer.running:
                    self.start_timer.start()
                remaining_time = self.start_timer.get_remaining_time()
                if remaining_time != last_time:
                    last_time = remaining_time
                if remaining_time >= 0:
                    self.data['start_time'] = remaining_time
                    self.sendTo()
                else:
                    self.data['start_game'] = True
                    self.start_timer.stop()
                    self.sendTo()
                    break
        
        last_time = self.timer.countdown_seconds if self.mode == 'normal' else self.chaos_timer.countdown_seconds
        while self.is_running:
            time.sleep(self.update_time)
            self.handle_client()
            if self.mode == 'normal':
                if not self.timer.running:
                    self.timer.start()
                remaining_time = self.timer.get_remaining_time()
                if remaining_time != last_time:
                    last_time = remaining_time
                if remaining_time >= 0:
                    self.data['timer'] = remaining_time

            elif self.mode == 'chaos':
                if not self.chaos_timer.running:
                    self.chaos_timer.start()
                remaining_time = self.chaos_timer.get_remaining_time()
                if remaining_time <= last_time - 1:
                    last_time = remaining_time
                    if len(self.ball) < 10:
                        self.ball.append(Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS))
                if remaining_time >= 0:
                    self.data['timer'] = remaining_time

            for idx, ball in enumerate(self.ball):
                ball.move()
                self.handle_collision(ball)
                if ball.x < 0:
                    self.data['right_score'] =  self.data.get('right_score') + 1
                    if self.mode == 'chaos':
                        self.ball.pop(idx)
                    else:
                        ball.reset()
                        self.timer.reset()
                elif ball.x > SCREEN_WIDTH:
                    self.data['left_score'] = self.data.get('left_score') + 1
                    if self.mode == 'chaos':
                        self.ball.pop(idx)
                    else:
                        ball.reset()
                        self.timer.reset()
                if remaining_time <=0:
                    self.data['right_score'] =  self.data.get('right_score') + 1
                    self.data['left_score'] = self.data.get('left_score') + 1
                    ball.reset()
                    self.timer.reset()
                if self.data.get('left_score') >= self.winning_points:
                    self.data['won'] = True
                    self.data['win_text'] = "Left Player Won!"
                elif self.data.get('right_score') >= self.winning_points:
                    self.data['won'] = True
                    self.data['win_text'] = "Right Player Won!"

            self.data['ball'] = [{"x": ball.x, "y": ball.y} for ball in self.ball]
            self.sendTo()

            if self.data.get('won'):
                self.is_running = False

        if self.timer.running:
            self.timer.stop()
        if self.chaos_timer.running:
            self.chaos_timer.stop()
        
        self.receiver.join()
        try:
            print('Closing Main socket...')
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception as e:
            print(f"Error closing socket: {e}")

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
            self.socket.sendto(json.dumps(self.data).encode(), client_address)

    def handle_collision(self, ball):
        if ball.y + ball.radius >= SCREEN_HEIGHT:
            ball.y_vel *= -1
        elif ball.y - ball.radius <= 0:
            ball.y_vel *= -1

        if ball.x_vel < 0:
            for paddle in self.data.get('left_paddles'):
                paddle = Paddle(paddle.get('x'), paddle.get('y'), paddle.get('width'), paddle.get('height'))
                if ball.y >= paddle.y and ball.y <= paddle.y + paddle.height:
                    if ball.x - ball.radius <= paddle.x + paddle.width:
                        ball.x_vel *= -1
                        middle_y = paddle.y + paddle.height / 2
                        difference_in_y = middle_y - ball.y
                        reduction_factor = (paddle.height / 2) / ball.MAX_VEL
                        y_vel = difference_in_y / reduction_factor
                        ball.y_vel = -1 * y_vel

        for paddle in self.data.get('right_paddles'):
            paddle = Paddle(paddle.get('x'), paddle.get('y'), paddle.get('width'), paddle.get('height'))
            if ball.y >= paddle.y and ball.y <= paddle.y + paddle.height:
                if ball.x + ball.radius >= paddle.x:
                    ball.x_vel *= -1
                    middle_y = paddle

class SocketThread(threading.Thread):
    def __init__(self, addr, server, lock):
        threading.Thread.__init__(self)
        self.server: Game_Server = server
        self.lock = lock
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(False)
        self.socket.settimeout(0.1)
        self.socket.bind(addr)
        self.disconnect = 0

    def run(self):
        data, addr = None, None
        print("Listening from players...")
        while self.server.is_running:
            try:
                data, addr = self.socket.recvfrom(1024)
                data = json.loads(data.decode())
                self.disconnect = 0
            except socket.timeout:
                print('Timeout')
                self.disconnect += 1
                if self.disconnect >= 30:
                    self.server.is_running = False
                continue
            finally:
                if data is not None:
                    client_address = (data.get('client_address')[0], data.get('client_address')[1])
                    self.server.check_address_conn[client_address] = True
                    if all(self.server.check_address_conn.values()):
                        self.server.comming_data = data
        try:
            print('Closing Thread socket...')
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception as e:
            print(f"Error closing socket: {e}")

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
    
    server = Game_Server(("0.0.0.0", 5555), left_client_address, right_client_address, left_paddles, right_paddles)
    server.run()