# core/camera.py — ALL CAMERA TYPES (Base + FPS + Static Top-Down)
from pygame.math import Vector3
import math, pygame
import pyrr
import numpy as np


class BaseCamera:
    def __init__(self, position=(0, 5, 15), target=(0, 0, 0)):
        self.position = Vector3(position)
        self.target = Vector3(target)
        self._needs_update = True
        self.view = np.eye(4, dtype='f4')
        self.proj = pyrr.matrix44.create_perspective_projection_matrix(
            60.0, 1280/720, 0.1, 1000.0, dtype='f4'
        )

    def get_view_matrix(self):
        if self._needs_update:
            up = Vector3(0, 1, 0)
            self.view = pyrr.matrix44.create_look_at(
                self.position, self.target, up, dtype='f4')
            self._needs_update = False
        return self.view

    def look_at(self, target):
        self.target = Vector3(target)
        self._needs_update = True


class FPSCamera(BaseCamera):
    def __init__(self, position=(0, 5, 15)):
        super().__init__(position=position, target=(0, 0, 0))
        self.yaw = -90.0
        self.pitch = 0.0
        self.move_speed = 12.0
        self.sensitivity = 0.15

    def update(self, input_state, dt):
        keys = input_state['keys']
        dx, dy = 0, 0

        # Mouse look (only when RMB held)
        if input_state['mouse_down'].get(3, False):
            dx, dy = pygame.mouse.get_rel()
            self.yaw += dx * self.sensitivity
            self.pitch -= dy * self.sensitivity
            self.pitch = max(-89, min(89, self.pitch))

        # Calculate direction
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        forward = Vector3(
            math.cos(yaw_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad),
            math.sin(yaw_rad) * math.cos(pitch_rad)
        ).normalize()

        right = Vector3(-math.sin(yaw_rad), 0, math.cos(yaw_rad)).normalize()

        # Movement
        move = Vector3(0, 0, 0)
        if keys.get(pygame.K_w): move += forward
        if keys.get(pygame.K_s): move -= forward
        if keys.get(pygame.K_a): move -= right
        if keys.get(pygame.K_d): move += right
        if keys.get(pygame.K_SPACE): move.y += 1
        if keys.get(pygame.K_LCTRL): move.y -= 1

        if move.length_squared() > 0:
            move.normalize_ip()
            self.position += move * (self.move_speed * dt)

        # Update look direction
        self.target = self.position + forward
        self._needs_update = True


class TopDownCamera(BaseCamera):
    def __init__(self):
        # Look straight down from high up
        super().__init__(position=(0, 30, 0.01), target=(0, 0, 0))
        self.look_at((0, 0, 0))