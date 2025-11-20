# main.py
import pygame, sys
from core.renderSystem import Renderer, CubeMesh

pygame.init()
renderer = Renderer((1280, 720))
renderer.set_skybox('assets/skybox')

# Create one cube
for i in range(10000):
    renderer.add_mesh((CubeMesh(renderer.ctx)))


clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    renderer.begin_frame()
    renderer.draw_scene()
    renderer.end_frame()
    clock.tick(144)