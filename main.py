# main.py
import pygame
from core.render_objects import CubeMesh
from core.render import Renderer

pygame.init()
renderer = Renderer()

# Create one cube
cube = CubeMesh(renderer.ctx)
renderer.meshes = [cube]  # We'll make this cleaner later

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    renderer.begin_frame()
    for mesh in renderer.meshes:
        mesh.draw()
    renderer.end_frame()
    clock.tick(60)

pygame.quit()