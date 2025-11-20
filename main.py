# main.py
import pygame
from core.renderSystem import Renderer, CubeMesh

pygame.init()
renderer = Renderer((1280, 720))

# Create one cube
cube = CubeMesh(renderer.ctx)
renderer.add_mesh(cube)

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    renderer.begin_frame()
    renderer.draw_scene()
    renderer.end_frame()
    clock.tick(60)