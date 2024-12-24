import pygame
import socket
import json, threading
from game.item import *

WIDTH, HEIGHT = 700, 500
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PADDLE_WIDTH, PADDLE_HEIGHT = 20, 100
BALL_RADIUS = 7
WINNING_SCORE = 10
clock = pygame.time.Clock()

class Game_Client():
    def __init__(self, client_port, server_address, left_players, right_players):
        pygame.init()
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.settimeout(1)
        self.client_address = ("0.0.0.0", client_port)
        self.server_listener = SocketThread(self.client_address, self, threading.Lock())
        self.server_listener.start()
        self.server_address = server_address

        self.is_running = True
        self.SCORE_FONT = pygame.font.SysFont("comicsans", 50)
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        self.ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_RADIUS)
        self.left_score = 0
        self.right_score = 0
        self.player_action = []
        pygame.display.set_caption("Pong Client")
        self.left_paddle: list[Paddle] = []
        self.right_paddle: list[Paddle] = []

        for player in left_players:
            self.left_paddle.append(Paddle(10, HEIGHT// 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))
        
        for player in right_players:
            self.right_paddle.append(Paddle(WIDTH - 10 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT))

    def run(self):
        while self.is_running:
            clock.tick(FPS)
            self.poll_events()
            self.update()
            self.draw(self.win)
        pygame.quit()

    def poll_events(self):
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.is_running = False
                return
            
        if keys[pygame.K_w]:
            self.player_action.append("MOVE_LEFT_UP".encode())
        if keys[pygame.K_s]:
            self.player_action.append("MOVE_LEFT_DOWN".encode())
        if keys[pygame.K_UP]:
            self.player_action.append("MOVE_RIGHT_UP".encode())
        if keys[pygame.K_DOWN]:
            self.player_action.append("MOVE_RIGHT_DOWN".encode())

    def update(self): 
        if len(self.player_action):
            self.client.sendto(self.player_action, self.server_address)
            self.player_action = []

    def draw(self):
        self.win.fill(BLACK)
        left_score_text = self.SCORE_FONT.render(f"{self.left_score}", 1, WHITE)
        right_score_text = self.SCORE_FONT.render(f"{self.right_score}", 1, WHITE)
        self.win.blit(left_score_text, (WIDTH//4 - left_score_text.get_width()//2, 20))
        self.win.blit(right_score_text, (WIDTH * (3/4) - right_score_text.get_width()//2, 20))

        if self.ball.x < 0:
            right_score += 1
            self.ball.reset()
        elif self.ball.x > WIDTH:
            left_score += 1
            self.ball.reset()

        won = False
        if left_score >= WINNING_SCORE:
            won = True
            win_text = "Left Player Won!"
        elif right_score >= WINNING_SCORE:
            won = True
            win_text = "Right Player Won!"

        if won:
            text = self.SCORE_FONT.render(win_text, 1, WHITE)
            self.win.blit(text, (WIDTH//2 - text.get_width() //
                            2, HEIGHT//2 - text.get_height()//2))
            pygame.display.update()
            pygame.time.delay(5000)
            self.ball.reset()
            for paddle in self.left_paddle + self.right_paddle:
                paddle.reset()
            left_score = 0
            right_score = 0
            self.is_running = False

        for paddle in self.left_paddle + self.right_paddle:
            paddle.draw(self.win)

        for i in range(10, HEIGHT, HEIGHT//20):
            if i % 2 == 1:
                continue
            pygame.draw.rect(self.win, WHITE, (WIDTH//2 - 5, i, 10, HEIGHT//20))

        self.ball.draw(self.win)
        pygame.display.update()

class SocketThread(threading.Thread):
    def __init__(self, addr, client, lock):
        threading.Thread.__init__(self)
        self.client: Game_Client = client
        self.lock = lock
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(addr)

    def run(self):
        while True:
            try:
                data = self.socket.recvfrom(1024)
                game_state = json.loads(data.decode())
                print(game_state)
                self.client.ball.x, self.client.ball.y = game_state['ball']
                self.client.left_paddle = game_state['left_paddles']
                self.client.right_paddle = game_state['right_paddles']
                self.client.left_score = game_state['left_score']
                self.client.right_score = game_state['right_score']
            except socket.timeout:
                print("[INFO] Timeout waiting for server response.")
            except Exception as e:
                print(f"[ERROR] {e}")
                break