# core/render.py — PURE RENDERER (NO INPUT, NO CAMERA LOGIC)
import pygame
import moderngl
import numpy as np
import pyrr
import math
from pygame.math import Vector3


class Renderer:
    def __init__(self, width=1280, height=720):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        self.screen = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.width, self.height = width, height

        self.camera = None
        self.objects_3d = []
        self.objects_2d = []

        self.ctx.enable(moderngl.DEPTH_TEST)

    def add_3d(self, obj): self.objects_3d.append(obj)
    def add_2d(self, obj): self.objects_2d.append(obj)

    def render(self):
        # 3D PASS
        self.ctx.clear(0.08, 0.08, 0.15, 1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        for obj in self.objects_3d:
            obj.draw(self.camera)

        # 2D PASS
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        ortho = pyrr.matrix44.create_orthogonal_projection_matrix(
            0, self.width, self.height, 0, -1, 1, dtype='f4'
        )
        for obj in self.objects_2d:
            obj.draw(ortho)


class Cube3D:
    def __init__(self, ctx):
        self.ctx = ctx
        self.rotation = 0.0
        verts = np.array([
            -1,-1,-1, 1,-1,-1, 1,1,-1, -1,-1,-1, 1,1,-1, -1,1,-1,
            -1,-1,1, 1,1,1, 1,-1,1, -1,-1,1, -1,1,1, 1,1,1,
            -1,-1,-1, -1,1,-1, -1,1,1, -1,-1,-1, -1,1,1, -1,-1,1,
            1,-1,-1, 1,-1,1, 1,1,1, 1,-1,-1, 1,1,1, 1,1,-1,
            -1,-1,-1, 1,-1,1, 1,-1,-1, -1,-1,-1, -1,-1,1, 1,-1,1,
            -1,1,-1, 1,1,-1, 1,1,1, -1,1,-1, 1,1,1, -1,1,1,
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
                    fragColor = vec4(0.2, 0.8, 1.0, 1.0);
                }
            ''',
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '3f', 'in_pos')])

    def draw(self, camera):
        self.rotation += 30.0 * (1/60)
        model = pyrr.matrix44.create_from_y_rotation(math.radians(self.rotation), dtype='f4')
        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_view'].write(camera.get_view_matrix().astype('f4').tobytes())
        self.prog['m_proj'].write(camera.proj.astype('f4').tobytes())
        self.vao.render(moderngl.TRIANGLES)