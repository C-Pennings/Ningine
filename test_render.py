# test_render.py
from core.render import Renderer, Cube3D
from core.input import Input
import pygame

r = Renderer(1280, 720)
input_sys = Input()

cube = Cube3D(r.ctx)
r.add_3d(cube)

clock = pygame.time.Clock()

print("Hold RIGHT MOUSE BUTTON to look around")
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    state = input_sys.update()
    r.render(0.016, state)   # ~60 FPS
    clock.tick(60)
    pygame.display.flip()