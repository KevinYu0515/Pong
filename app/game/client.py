import threading, socket, json, argparse
import pygame
from .items import *
from .constants import *

clock = pygame.time.Clock()

class Game_Client():
    def __init__(self, addr, server_address, left_paddles, right_paddles, my_paddles):
        self.is_running = True

        # Initialize socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lock = threading.Lock()
        self.receiver = SocketThread(addr, self, self.lock)
        self.receiver.start()
        self.server_address = server_address

        # Initialize game objects
        self.left_paddles = []
        self.right_paddles = []
        self.ball = []
        self.left_score = 0
        self.right_score = 0
        self.won = False
        self.win_text = ''
        self.data = {'client_address': addr}
        self.my_paddles = my_paddles
        self.timer = 0
        self.start_txt = ''
        self.start_game = False
        self.save_end = True

        for paddle in left_paddles:
            start_x = 10 + int(paddle.get('position')) * 100
            self.left_paddles.append(Paddle(start_x, PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))

        for paddle in right_paddles:
            start_x = SCREEN_WIDTH - 10 - PADDLE_WIDTH - int(paddle.get('position')) * 100
            self.right_paddles.append(Paddle(start_x, PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))

        # Initialize pygame
        pygame.init()
        self.win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.SCORE_FONT = pygame.font.SysFont("comicsans", 50)
        pygame.display.set_caption("Pong")

    def run(self):
        self.sendTo()
        while self.is_running:
            clock.tick(FPS)

            keys = pygame.key.get_pressed()
            self.handle_paddle_movement(keys, self.my_paddles.get('idx'), self.my_paddles.get('side'))
            self.poll_events()
            self.draw()

        if self.save_end:
            time.sleep(3)
        self.socket.close()
        pygame.quit()
    
    def sendTo(self):
        side, idx = self.my_paddles.get('side'), self.my_paddles.get('idx')
        self.data['side'], self.data['idx'] = side, idx
        if side == 'left':
            self.data['y'] = self.left_paddles[idx].y
        elif side == 'right':
            self.data['y'] = self.right_paddles[idx].y

        self.socket.sendto(json.dumps(self.data).encode(), self.server_address)

    def poll_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                self.save_end = False
            elif event.type == pygame.KEYDOWN:
                pass

    def draw(self):
        self.win.fill(BLACK)
        if not self.start_game:
            if self.start_txt == 0:
                start_txt = self.SCORE_FONT.render(f"START", 1, WHITE)
            else:
                start_txt = self.SCORE_FONT.render(f"{self.start_txt}", 1, WHITE)
            self.win.blit(start_txt, (SCREEN_WIDTH // 2 - start_txt.get_width() // 2, SCREEN_HEIGHT // 2 - start_txt.get_height() // 2))
        elif self.won:
            text = self.SCORE_FONT.render(self.win_text, 1, WHITE)
            self.win.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height()//2))
            self.is_running = False
            
        else:
            for i in range(10, SCREEN_HEIGHT, SCREEN_HEIGHT // 20):
                if i % 2 == 1:
                    continue
                pygame.draw.rect(self.win, WHITE, (SCREEN_WIDTH // 2 - 5, i, 5, (SCREEN_HEIGHT - 20) // 20))
            for ball in self.ball:
                ball.draw(self.win)
        
        current_timer = self.SCORE_FONT.render(f"{self.timer}", 1, TIMER_COLOR)
        self.win.blit(current_timer, (SCREEN_WIDTH // 2 - current_timer.get_width() //2 , 20))

        left_score_text = self.SCORE_FONT.render(f"{self.left_score}", 1, WHITE)
        self.win.blit(left_score_text, (SCREEN_WIDTH // 4 - left_score_text.get_width() // 2, 20))
        right_score_text = self.SCORE_FONT.render(f"{self.right_score}", 1, WHITE)
        self.win.blit(right_score_text, (SCREEN_WIDTH * (3/4) - right_score_text.get_width() // 2, 20))
        
        
        for idx, paddle in enumerate(self.left_paddles):
            if self.my_paddles.get('side') == 'left' and idx == self.my_paddles.get('idx'):
                paddle.draw(self.win, MY_PADDLE_COLOR)
            else:
                paddle.draw(self.win)
        
        for idx, paddle in enumerate(self.right_paddles):
            if self.my_paddles.get('side') == 'right' and idx == self.my_paddles.get('idx'):
                paddle.draw(self.win, MY_PADDLE_COLOR)
            else:
                paddle.draw(self.win)

        pygame.display.update()

    def handle_paddle_movement(self, keys, idx, side):
        if side == 'left':
            if keys[pygame.K_w] and self.left_paddles[idx].y - self.left_paddles[idx].VEL >= 0:
                self.left_paddles[idx].move(up=True)
                self.sendTo()
            if keys[pygame.K_s] and self.left_paddles[idx].y + self.left_paddles[idx].VEL + self.left_paddles[idx].height <= SCREEN_HEIGHT:
                self.left_paddles[idx].move(up=False)
                self.sendTo()

        elif side == 'right':
            if keys[pygame.K_UP] and self.right_paddles[idx].y - self.right_paddles[idx].VEL >= 0:
                self.right_paddles[idx].move(up=True)
                self.sendTo()
            if keys[pygame.K_DOWN] and self.right_paddles[idx].y + self.right_paddles[idx].VEL + self.right_paddles[idx].height <= SCREEN_HEIGHT:
                self.right_paddles[idx].move(up=False)
                self.sendTo()

class SocketThread(threading.Thread):
    def __init__(self, addr, client, lock):
        threading.Thread.__init__(self)
        self.client: Game_Client = client
        self.lock = lock
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(addr)

    def run(self):
        print('Listening from server...')
        while self.client.is_running:
            with self.lock:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    data = json.loads(data.decode())
                except socket.timeout:
                    continue
                finally:
                    if data is not None:
                        self.client.start_txt = data.get('start_time')
                        self.client.start_game = data.get('start_game')

                        print(data)
                        self.client.left_paddles, self.client.right_paddles = [], []
                        for paddles in data.get('left_paddles'):
                            self.client.left_paddles.append(Paddle(paddles.get('x'), paddles.get('y'), paddles.get('width'), paddles.get('height')))
                        for paddles in data.get('right_paddles'):
                            self.client.right_paddles.append(Paddle(paddles.get('x'), paddles.get('y'), paddles.get('width'), paddles.get('height')))
                        self.client.ball = [Ball(ball.get('x'), ball.get('y'), BALL_RADIUS) for ball in data['ball']]
                        self.client.left_score = data.get('left_score')
                        self.client.right_score = data.get('right_score')
                        self.client.timer = data.get('timer')

                        if data.get('won'):
                            self.client.won = data.get('won')
                            self.client.win_text = data.get('win_text')
        self.socket.close()

if __name__ == "__main__":
    left_paddles = [{"position": 0}, {"position": 1}]
    right_paddles = [{"position": 0}, {"position": 1}]

    parser = argparse.ArgumentParser(description='Pong Game Client')
    parser.add_argument("--port", type=str, required=True, help="client port")
    parser.add_argument("--side", type=str, required=True, help="client side")
    parser.add_argument("--pos", type=str, required=True, help="client position")
    
    args = parser.parse_args()
    port = int(args.port)
    side = args.side
    pos =  int(args.pos)

    Game_Client(("0.0.0.0", port), ('127.0.0.1', 5555), left_paddles, right_paddles, {'idx': pos, 'side': side}).run()