# test_render.py — FINAL WORKING: C switches camera, no RMB, proper ground
import pygame
import pyrr, sys
import numpy as np
from core.render import Renderer, Cube3D
from core.camera import FPSCamera, TopDownCamera
from core.input import Input

# Setup
r = Renderer(1280, 720)
input_sys = Input()

# === FIXED GROUND PLANE (proper winding, flat, dark green) ===
class GroundPlane:
    def __init__(self, ctx):
        self.ctx = ctx
        self.scale = 100.0
        self.y = -0.5

        # Two large triangles forming a flat plane on XZ
        verts = np.array([
            -1, 0, -1,
             1, 0, -1,
             1, 0,  1,
            -1, 0, -1,
             1, 0,  1,
            -1, 0,  1,
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
                    fragColor = vec4(0.08, 0.38, 0.12, 1.0);
                }
            ''',
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '3f', 'in_pos')])

    def draw(self, camera):
        model = pyrr.matrix44.create_from_scale((self.scale, 1, self.scale), dtype='f4')
        model = pyrr.matrix44.multiply(
            model,
            pyrr.matrix44.create_from_translation((0, self.y, 0), dtype='f4')
        )
        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_view'].write(camera.get_view_matrix().astype('f4').tobytes())
        self.prog['m_proj'].write(camera.proj.astype('f4').tobytes())
        self.vao.render()

# Objects
cube = Cube3D(r.ctx)
ground = GroundPlane(r.ctx)
r.add_3d(ground)
r.add_3d(cube)

# Cameras
fps_cam = FPSCamera(position=(0, 3, 10))
topdown_cam = TopDownCamera()
r.camera = fps_cam

# State
current_camera = "fps"
c_pressed = False  # Simple debounce
clock = pygame.time.Clock()

print("FPS MODE (mouse look always on) | Press C = Top-Down | WASD/Space/Ctrl = Move")

# Hide cursor and grab mouse at start
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

while True:
    dt = clock.tick(60) / 1000.0
    state = input_sys.update()

    if state['keys'].get(pygame.K_ESCAPE, False):
        pygame.quit()
        sys.exit()

    # === CAMERA SWITCH WITH C (FIXED) ===
    if state['keys'].get(pygame.K_c, False):
        if not c_pressed:
            c_pressed = True
            if current_camera == "fps":
                r.camera = topdown_cam
                current_camera = "topdown"
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                print("→ TOP-DOWN CAMERA (mouse free)")
            else:
                r.camera = fps_cam
                current_camera = "fps"
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
                print("→ FPS CAMERA (mouse captured)")
    else:
        c_pressed = False

    # === UPDATE CURRENT10 CAMERA ===
    if current_camera == "fps":
        fps_cam.update(state, dt)

    # Render
    r.render()
    pygame.display.flip()