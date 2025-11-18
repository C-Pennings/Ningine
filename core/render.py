# core/render.py – Universal 2D/3D Renderer (Pygame → GPU + FPS Camera)
import pygame
import moderngl
import numpy as np
import pyrr  # Temporary – NumPy matrices Week 4
from typing import List, Optional

class Camera:
    """FPS Camera – WASD + Mouse."""
    def __init__(self, position=(0.0, 0.0, 6.0), fov=60.0, aspect=16/9, near=0.1, far=1000.0, speed=5.0):
        self.position = np.array(position, dtype='f4')
        self.yaw = -90.0
        self.pitch = 0.0
        self.speed = speed
        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far
        self._update_vectors()
        self._update_proj()

    def _update_proj(self):
        self.proj = pyrr.matrix44.create_perspective_projection(self.fov, self.aspect, self.near, self.far, dtype='f4')

    def _update_vectors(self):
        yaw_rad = np.radians(self.yaw)
        pitch_rad = np.radians(self.pitch)
        self.forward = np.array([
            np.cos(yaw_rad) * np.cos(pitch_rad),
            np.sin(pitch_rad),
            np.sin(yaw_rad) * np.cos(pitch_rad)
        ], dtype='f4')
        self.forward = self.forward / np.linalg.norm(self.forward)
        self.right = np.cross(self.forward, np.array([0,1,0], dtype='f4'))
        self.right /= np.linalg.norm(self.right)
        self.up = np.cross(self.right, -self.forward)

    def rotate(self, dx: float, dy: float, sensitivity: float = 0.15):
        self.yaw += dx * sensitivity
        self.pitch -= dy * sensitivity  # Invert Y
        self.pitch = np.clip(self.pitch, -89, 89)
        self._update_vectors()

    def move(self, direction: np.ndarray, dt: float):
        self.position += direction * (self.speed * dt)

    @property
    def view(self):
        center = self.position + self.forward
        return pyrr.matrix44.create_look_at(self.position, center, self.up, dtype='f4')

class Renderer:
    """3D Depth Pass → 2D Ortho GUI Overlay."""
    def __init__(self, width: int = 1280, height: int = 720):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.width, self.height = width, height
        self.camera = Camera(aspect=width/height)
        self.objects_3d: List['RenderObject3D'] = []
        self.objects_2d: List['RenderObject2D'] = []
        self._setup_gl()

    def _setup_gl(self):
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)

    def add_3d(self, obj: 'RenderObject3D'):
        self.objects_3d.append(obj)

    def add_2d(self, obj: 'RenderObject2D'):
        self.objects_2d.append(obj)

    def render(self, dt: float, input_state: dict):
        """Full frame: 3D → 2D GUI."""
        # Mouse look
        if input_state['mouse_down'][1]:  # RMB for camera
            mx, my = input_state['mouse_pos']
            self.camera.rotate(mx * 0.15, my * 0.15)

        # 3D Pass
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)
        self.ctx.clear(0.12, 0.12, 0.12, 1.0)
        for obj in self.objects_3d:
            obj.draw(self.camera)

        # 2D GUI Pass (Your widgets here)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        ortho = self._ortho_proj()
        for obj in self.objects_2d:
            obj.draw(ortho)

        pygame.display.flip()

    def _ortho_proj(self):
        return pyrr.matrix44.create_orthogonal_projection(
            0, self.width, self.height, 0, -1, 1, dtype='f4'
        )

    def get_surface(self) -> pygame.Surface:
        """For legacy 2D blits → upload as Sprite2D."""
        # FBO for Pygame surface (Week 2)
        pass  # Impl later

class RenderObject3D:
    """Base for cubes, models (instancing Week 4)."""
    def __init__(self, ctx):
        self.ctx = ctx
        self.prog = self._create_prog()
        self.vao = None  # Set in subclasses

    def _create_prog(self):
        return self.ctx.program(
            vertex_shader='''
                #version 330
                in vec3 in_pos;
                uniform mat4 m_model, m_view, m_proj;
                void main() { gl_Position = m_proj * m_view * m_model * vec4(in_pos, 1.0); }
            ''',
            fragment_shader='''
                #version 330
                out vec4 f_color;
                void main() { f_color = vec4(0.2, 0.7, 1.0, 1.0); }
            '''
        )

    def draw(self, camera):
        self.prog['m_view'].write(camera.view.astype('f4').tobytes())
        self.prog['m_proj'].write(camera.proj.astype('f4').tobytes())
        self.vao.render(moderngl.TRIANGLES)

class Cube3D(RenderObject3D):
    """Week 4: JSON AABBs → Instanced Cubes."""
    def __init__(self, ctx):
        super().__init__(ctx)
        verts = np.array([  # 36 verts CCW cube
            [-1,-1,-1, 1,-1,-1, 1,1,-1, -1,-1,-1, 1,1,-1, -1,1,-1],  # Back
            # ... (full 36 from boilerplate)
        ], dtype='f4')
        vbo = ctx.buffer(verts.tobytes())
        self.vao = ctx.vertex_array(self.prog, [(vbo, '3f', 'in_pos')])

    def draw(self, camera, model: np.ndarray = None):
        if model is None:
            model = pyrr.matrix44.create_from_y_rotation(0, dtype='f4')  # Rotate
        self.prog['m_model'].write(model.astype('f4').tobytes())
        super().draw(camera)

class RenderObject2D:
    """Pygame Surface → GPU Sprite (GUI Widgets)."""
    def __init__(self, ctx, surface: pygame.Surface, pos=(0,0), size=None):
        self.ctx = ctx
        self.pos = np.array(pos, dtype='f4')
        self.size = surface.get_size() if size is None else size
        self.tex = self._upload_texture(surface)
        self.vao = self._setup_quad()

    def _upload_texture(self, surf):
        tex = self.ctx.texture(surf.get_size(), 4)
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        tex.swizzle = 'BGRA'
        tex.write(surf.get_view('1'))
        return tex

    def _setup_quad(self):
        quad = np.array([
            [0,0, 0,0], [1,0, 1,0], [0,1, 0,1],  # Tri 1
            [1,0, 1,0], [1,1, 1,1], [0,1, 0,1]   # Tri 2
        ], dtype='f4')
        vbo = self.ctx.buffer(quad.tobytes())
        prog = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_pos; in vec2 in_uv;
                uniform mat4 m_model, m_proj;
                out vec2 v_uv;
                void main() {
                    gl_Position = m_proj * m_model * vec4(in_pos, 0.0, 1.0);
                    v_uv = in_uv;
                }
            ''',
            fragment_shader='''
                #version 330
                in vec2 v_uv; uniform sampler2D tex;
                out vec4 f_color;
                void main() {
                    vec4 c = texture(tex, v_uv);
                    if (c.a < 0.01) discard;
                    f_color = c;
                }
            '''
        )
        return self.ctx.vertex_array(prog, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

    def draw(self, ortho_proj):
        model = pyrr.matrix44.create_from_translation(self.pos) @ \
                pyrr.matrix44.create_from_scale([self.size[0], self.size[1], 1], dtype='f4')
        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_proj'].write(ortho_proj.astype('f4').tobytes())
        self.tex.use(0)
        self.prog['tex'].value = 0
        self.vao.render(moderngl.TRIANGLES)