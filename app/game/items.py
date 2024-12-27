import pygame, time, threading
from .constants import *

class Paddle:
    VEL = 4

    def __init__(self, x, y, width, height):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.width = width
        self.height = height

    def draw(self, win, color=WHITE):
        pygame.draw.rect(win, color, (self.x, self.y, self.width, self.height))

    def move(self, up=True):
        if up:
            self.y -= self.VEL
        else:
            self.y += self.VEL

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y


class Ball:
    MAX_VEL = 5

    def __init__(self, x, y, radius):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.radius = radius
        self.x_vel = self.MAX_VEL
        self.y_vel = 0

    def draw(self, win):
        pygame.draw.circle(win, WHITE, (self.x, self.y), self.radius)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y
        self.y_vel = 0
        self.x_vel *= -1

class Timer:
    def __init__(self, countdown_seconds):
        self.countdown_seconds = countdown_seconds
        self.running = False
        self.start_time = None

    def start(self):
        self.running = True
        self.start_time = time.time()

    def stop(self):
        self.running = False

    def get_remaining_time(self):
        if not self.running:
            return self.countdown_seconds
        
        elapsed_time = int(time.time() - self.start_time)
        remaining_time = self.countdown_seconds - elapsed_time
        return remaining_time

    def reset(self):
        self.start_time = time.time()