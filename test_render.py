from core.render import Renderer, Cube3D
from core.input import Input  # Your class
import time
import pygame

r = Renderer()
input = Input()
cube = Cube3D(r.ctx)
r.add_3d(cube)

clock = pygame.time.Clock()
last_time = time.time()
running = True

while running:
    dt = time.time() - last_time
    last_time = time.time()
    state = input.update()  # Your input.get_state()

    r.render(dt, state)

    clock.tick(60)