# main.py
import pygame, sys
import numpy as np
from core.renderSystem import Renderer
from core.renderObjects import MeshObject
from core.funcs import import_obj

pygame.init()
renderer = Renderer((1280, 720))
renderer.set_skybox()

# Load and display monkey correctly
data = import_obj('assets/models/test.obj')
monkey = MeshObject(renderer.ctx, data, 'monkey')

for _ in range(1000):
    renderer.add_mesh(monkey)

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

# Simple fly cam
from pygame.math import Vector3

cam = renderer.camera
cam.position = Vector3(0, 0, 10)

clock = pygame.time.Clock()
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            quit()
        
        
    
    # Inside the while loop, after event handling
    if pygame.mouse.get_focused():
        pygame.mouse.set_pos(640, 360)  # center of 1280x720

    # Simple mouse look
    mx, my = pygame.mouse.get_rel()
    cam.yaw -= mx * 0.1
    cam.pitch -= my * 0.1
    cam.pitch = max(-89, min(89, cam.pitch))

    # Simple WASD
    keys = pygame.key.get_pressed()
    forward = Vector3(
        np.sin(np.radians(cam.yaw)), 0, np.cos(np.radians(cam.yaw))
    )
    right = Vector3(-forward.z, 0, forward.x)
    
    move = Vector3(0,0,0)
    if keys[pygame.K_w]: move += forward
    if keys[pygame.K_s]: move -= forward
    if keys[pygame.K_a]: move -= right
    if keys[pygame.K_d]: move += right
    if keys[pygame.K_SPACE]: move.y += 1
    if keys[pygame.K_LCTRL]: move.y -= 1
    if keys[pygame.K_ESCAPE]: 
        pygame.quit(); sys.exit()
    
    if move.length() > 0:
        cam.position += move.normalize() * 0.1

    cam.target = cam.position + forward

    renderer.begin_frame()
    renderer.draw_scene()
    renderer.end_frame()
    clock.tick(160)