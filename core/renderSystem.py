# core/render_objects.py
import moderngl
import pygame
import numpy as np
from pygame.math import Vector3
from pathlib import Path
import time

class Renderer:
    def __init__(self, size=(1280, 720)):
        pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.width, self.height = size
        self.meshes = []

        # Fixed camera that shows the cube
        self.proj = self._perspective()
        self.view = self._look_at(Vector3(0, -3, 15), Vector3(0, 0, 0), Vector3(0, 1, 0))

    def _perspective(self):
        # Proper OpenGL perspective matrix (right-handed, -1 to 1 depth)
        fov = np.radians(45)
        aspect = self.width / self.height
        near, far = 0.1, 100.0
        f = 1.0 / np.tan(fov / 2.0)
        
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0.0, 0.0, -1.0, 0.0]
        ], dtype='f4')

    def _look_at(self, eye, target, up):
        f = (target - eye).normalize()
        s = f.cross(up).normalize()
        u = s.cross(f)
        return np.array([
            [s.x, s.y, s.z, -s.dot(eye)],
            [u.x, u.y, u.z, -u.dot(eye)],
            [-f.x, -f.y, -f.z, f.dot(eye)],
            [0, 0, 0, 1]
        ], dtype='f4')

    def add_mesh(self, mesh):
        self.meshes.append(mesh)

    def begin_frame(self):
        self.ctx.clear(0.2, 0.2, 0.3, 1.0)        # Dark gray background so pink is visible
        self.ctx.enable(moderngl.DEPTH_TEST)

    def draw_scene(self):
        for mesh in self.meshes:
            prog = mesh.program
            
            # Upload matrices
            # OpenGL expects column-major matrices; transpose our row-major numpy arrays
            prog['u_proj'].write(self.proj.T.tobytes())
            prog['u_view'].write(self.view.T.tobytes())

            # SPINNING CUBE
            angle = time.time() * 0.5
            c, s = np.cos(angle), np.sin(angle)
            model = np.array([
                [c, 0, s, 0],
                [0, 1, 0, 0],
                [-s, 0, c, 0],
                [0, 0, 0, 1]
            ], dtype='f4')
            prog['u_model'].write(model.T.tobytes())

            mesh.draw()

    def end_frame(self):
        pygame.display.flip()

class Mesh:
    def __init__(self, ctx, shader_name="default"):
        self.ctx = ctx
        self.program = self._load_shader(shader_name)
        self.vao = None
        self.build_geometry()

    def _load_shader(self, name):
        path = Path("shaders")
        vert = (path / f"{name}.vert").read_text()
        frag = (path / f"{name}.frag").read_text()
        return self.ctx.program(vertex_shader=vert, fragment_shader=frag)

    def build_geometry(self):
        raise NotImplementedError

    def _upload(self, verts, indices=None):
        vbo = self.ctx.buffer(verts.tobytes())
        if indices is not None:
            ibo = self.ctx.buffer(indices.tobytes())
            self.vao = self.ctx.vertex_array(self.program, [(vbo, '3f', 'in_position')], index_buffer=ibo)
        else:
            self.vao = self.ctx.vertex_array(self.program, [(vbo, '3f', 'in_position')])

    def draw(self):
        if self.vao:
            self.vao.render(moderngl.TRIANGLES)

class CubeMesh(Mesh):
    def __init__(self, ctx):
        super().__init__(ctx, "default")

    def build_geometry(self):
        v = np.array([
            -1,-1,-1, 1,-1,-1, 1,1,-1, -1,1,-1,
            -1,-1,1, 1,-1,1, 1,1,1, -1,1,1,
            -1,-1,-1, -1,-1,1, -1,1,1, -1,1,-1,
            1,-1,-1, 1,-1,1, 1,1,1, 1,1,-1,
            -1,-1,-1, 1,-1,-1, 1,-1,1, -1,-1,1,
            -1,1,-1, 1,1,-1, 1,1,1, -1,1,1
        ], dtype='f4').reshape(-1, 3) * 2.0

        i = np.array([
            0,1,2,2,3,0, 4,5,6,6,7,4, 8,9,10,10,11,8,
            12,13,14,14,15,12, 16,17,18,18,19,16, 20,21,22,22,23,20
        ], dtype='i4')

        self._upload(v, i)