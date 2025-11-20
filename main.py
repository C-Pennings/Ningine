# main.py
import pygame
from core.render import Renderer
from core.render_objects import CubeMesh

pygame.init()
renderer = Renderer((1280, 720))

cube = CubeMesh(renderer.ctx)
renderer.add_mesh(cube)

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            quit()

    renderer.begin_frame()
    renderer.draw_scene()
    renderer.end_frame()
    pygame.time.wait(16)