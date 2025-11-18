# core/render.py
# NINGINE — 3D + 2D Renderer — BLACK SCREEN FIXED

import pygame
import moderngl
import numpy as np
import pyrr
from typing import List


class Camera:
    def __init__(self, position=(0.0, 0.0, 6.0)):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = -90.0
        self.pitch = 0.0
        self._update_vectors()

    def _update_vectors(self):
        yaw = np.radians(self.yaw)
        pitch = np.radians(self.pitch)
        self.forward = np.array([
            np.cos(yaw) * np.cos(pitch),
            np.sin(pitch),
            np.sin(yaw) * np.cos(pitch)
        ], dtype=np.float32)
        self.forward = self.forward / np.linalg.norm(self.forward + 1e-8)
        world_up = np.array([0, 1, 0], dtype=np.float32)
        self.right = np.cross(self.forward, world_up)
        self.right /= np.linalg.norm(self.right + 1e-8)
        self.up = np.cross(self.right, -self.forward)

    def rotate(self, dx: float, dy: float):
        self.yaw += dx * 0.12
        self.pitch = max(-89, min(89, self.pitch - dy * 0.12))
        self._update_vectors()

    @property
    def view(self):
        center = self.position + self.forward
        return pyrr.matrix44.create_look_at(self.position, center, self.up, dtype='f4')

    @property
    def proj(self):
        return pyrr.matrix44.create_perspective_projection_matrix(60.0, 1280/720, 0.1, 1000.0, dtype='f4')


class Renderer:
    def __init__(self, width=1280, height=720):
        pygame.init()

        # CRITICAL: force VSync + double buffer
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        self.screen = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.width, self.height = width, height

        self.camera = Camera()
        self.objects_3d = []
        self.objects_2d = []

        self.mouse_captured = False
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)

        self.ctx.enable(moderngl.DEPTH_TEST)

    def add_3d(self, obj): self.objects_3d.append(obj)
    def add_2d(self, obj): self.objects_2d.append(obj)

    def render(self, dt: float, input_state: dict):
        # Mouse look — fixed with get_rel()
        if input_state['mouse_down'].get(3, False):  # RMB = button 3 in pygame
            if not self.mouse_captured:
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
                self.mouse_captured = True
            dx, dy = pygame.mouse.get_rel()
            if abs(dx) > 0 or abs(dy) > 0:
                self.camera.rotate(dx, dy)
        else:
            if self.mouse_captured:
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                self.mouse_captured = False
                pygame.mouse.get_rel()  # flush

        # 3D PASS
        self.ctx.clear(0.1, 0.1, 0.15, 1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)

        for obj in self.objects_3d:
            obj.draw(self.camera)

        # 2D PASS (ready for GUI)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        ortho = pyrr.matrix44.create_orthogonal_projection_matrix(0, self.width, self.height, 0, -1, 1, dtype='f4')
        for obj in self.objects_2d:
            obj.draw(ortho)

        # NO pygame.display.flip() → ModernGL already swapped


class Cube3D:
    def __init__(self, ctx):
        self.ctx = ctx
        self.rotation = 0.0

        # 36 vertices — CCW cube (fixed order)
        verts = np.array([
            -1,-1,-1,  1,-1,-1,  1, 1,-1,   -1,-1,-1,  1, 1,-1, -1, 1,-1,  # back
            -1,-1, 1,  1, 1, 1,  1,-1, 1,   -1,-1, 1, -1, 1, 1,  1, 1, 1,  # front
            -1,-1,-1, -1, 1,-1, -1, 1, 1,   -1,-1,-1, -1, 1, 1, -1,-1, 1,  # left
             1,-1,-1,  1,-1, 1,  1, 1, 1,    1,-1,-1,  1, 1, 1,  1, 1,-1,  # right
            -1,-1,-1,  1,-1, 1,  1,-1,-1,   -1,-1,-1, -1,-1, 1,  1,-1, 1,  # bottom
            -1, 1,-1,  1, 1,-1,  1, 1, 1,   -1, 1,-1,  1, 1, 1, -1, 1, 1,  # top
        ], dtype=np.float32)

        self.vbo = ctx.buffer(verts.tobytes())
        self.prog = ctx.program(
            vertex_shader='''
                #version 330 core
                layout(location = 0) in vec3 in_pos;
                uniform mat4 m_model;
                uniform mat4 m_view;
                uniform mat4 m_proj;
                void main() {
                    gl_Position = m_proj * m_view * m_model * vec4(in_pos, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330 core
                out vec4 fragColor;
                void main() {
                    fragColor = vec4(0.3, 0.7, 1.0, 1.0);
                }
            ''',
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '3f', 'in_pos')])

    def draw(self, camera):
        self.rotation += 45.0 * (1/60)  # nice slow spin
        angle = np.radians(self.rotation)
        model = pyrr.matrix44.create_from_y_rotation(angle, dtype='f4')

        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_view'].write(camera.view.astype('f4').tobytes())
        self.prog['m_proj'].write(camera.proj.astype('f4').tobytes())

        self.vao.render(moderngl.TRIANGLES)