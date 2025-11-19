# main.py
import pygame
from core.render import Renderer

pygame.init()
renderer = Renderer()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); quit()
            
    renderer.begin_frame(None)      # camera not ready yet
    renderer.draw_scene(None)       # scene not ready yet
    renderer.end_frame()