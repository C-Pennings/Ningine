# demo_3d_2d_ortho_fixed.py
import sys
import math
import time
from array import array

import pygame
import moderngl
import pyrr
import numpy as np

# -------------------------
# Window / Context
# -------------------------
class Window:
    def __init__(self, title="3D + 2D (Ortho) Demo - Fixed", size=(1280, 720)):
        pygame.init()
        pygame.display.set_caption(title)
        self.width, self.height = size
        # create an OpenGL double-buffered screen
        self.screen = pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)
        # create moderngl context from current context
        self.ctx = moderngl.create_context()
        self.clock = pygame.time.Clock()
        self.size = size

# -------------------------
# Camera (FPS-style)
# -------------------------
class Camera:
    def __init__(self, position=(0.0, 0.0, 6.0), yaw=-90.0, pitch=0.0,
                 fov=60.0, aspect=16/9, near=0.1, far=1000.0,
                 speed=5.0, sensitivity=0.15):
        self.position = pyrr.Vector3(position, dtype='f4')
        self.yaw = yaw
        self.pitch = pitch
        self.speed = speed
        self.sensitivity = sensitivity

        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far

        self.forward = pyrr.Vector3([0.0, 0.0, -1.0], dtype='f4')
        self.up = pyrr.Vector3([0.0, 1.0, 0.0], dtype='f4')
        self.right = pyrr.Vector3([1.0, 0.0, 0.0], dtype='f4')

        self._update_vectors()
        self._update_proj()

    def _update_proj(self):
        self.proj = pyrr.matrix44.create_perspective_projection(
            self.fov, self.aspect, self.near, self.far, dtype='f4'
        )

    def _update_vectors(self):
        cy = math.cos(math.radians(self.yaw))
        sy = math.sin(math.radians(self.yaw))
        cp = math.cos(math.radians(self.pitch))
        sp = math.sin(math.radians(self.pitch))

        fx = cy * cp
        fy = sp
        fz = sy * cp

        f = pyrr.Vector3([fx, fy, fz], dtype='f4')
        self.forward = pyrr.vector.normalize(f)
        self.right = pyrr.vector.normalize(pyrr.vector3.cross(self.forward, [0.0, 1.0, 0.0]))
        self.up = pyrr.vector.normalize(pyrr.vector3.cross(self.right, self.forward * -1.0))

    def rotate(self, dx, dy):
        self.yaw += dx * self.sensitivity
        self.pitch -= dy * self.sensitivity  # invert Y
        self.pitch = max(-89.0, min(89.0, self.pitch))
        self._update_vectors()

    def move_forward(self, dt=1.0):
        self.position += self.forward * (self.speed * dt)

    def move_backward(self, dt=1.0):
        self.position -= self.forward * (self.speed * dt)

    def move_right(self, dt=1.0):
        self.position += self.right * (self.speed * dt)

    def move_left(self, dt=1.0):
        self.position -= self.right * (self.speed * dt)

    def move_up(self, dt=1.0):
        self.position += pyrr.Vector3([0.0, 1.0, 0.0], dtype='f4') * (self.speed * dt)

    def move_down(self, dt=1.0):
        self.position -= pyrr.Vector3([0.0, 1.0, 0.0], dtype='f4') * (self.speed * dt)

    @property
    def view(self):
        eye = np.array(self.position, dtype='f4')
        center = np.array(self.position + self.forward, dtype='f4')
        up = np.array(self.up, dtype='f4')
        return pyrr.matrix44.create_look_at(eye, center, up, dtype='f4')

# -------------------------
# Renderer
# -------------------------
class Renderer:
    def __init__(self, ctx, screen_size):
        self.ctx = ctx
        self.width, self.height = screen_size
        self.objects_3d = []
        self.objects_2d = []

        # general GL state
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        # ensure CCW is treated as front face (this is default but explicit)
        try:
            self.ctx.front_face = 'ccw'
        except Exception:
            # older moderngl versions may not have front_face property; ignore
            pass

    def add_3d(self, obj):
        self.objects_3d.append(obj)

    def add_2d(self, obj):
        self.objects_2d.append(obj)

    def render(self, camera: Camera, ortho_proj_2d):
        # 1) 3D pass
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)
        self.ctx.clear(0.12, 0.12, 0.12, 1.0)

        for obj in self.objects_3d:
            obj.draw(camera)

        # 2) 2D pass (orthographic)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        for obj in self.objects_2d:
            obj.draw(ortho_proj_2d)

# -------------------------
# Mesh3D (36-vertex CCW cube)
# -------------------------
class Mesh3D:
    def __init__(self, ctx):
        self.ctx = ctx
        # 36 vertices (12 triangles * 3) - positions only - CCW winding
        # Each face is two triangles, vertices listed CCW looking at the face
        verts = [
            # back face (z = -1)
            -1.0, -1.0, -1.0,
             1.0, -1.0, -1.0,
             1.0,  1.0, -1.0,
            -1.0, -1.0, -1.0,
             1.0,  1.0, -1.0,
            -1.0,  1.0, -1.0,

            # front face (z = +1)
            -1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,
             1.0, -1.0,  1.0,
            -1.0, -1.0,  1.0,
            -1.0,  1.0,  1.0,
             1.0,  1.0,  1.0,

            # left face (x = -1)
            -1.0, -1.0, -1.0,
            -1.0,  1.0, -1.0,
            -1.0,  1.0,  1.0,
            -1.0, -1.0, -1.0,
            -1.0,  1.0,  1.0,
            -1.0, -1.0,  1.0,

            # right face (x = +1)
             1.0, -1.0, -1.0,
             1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,
             1.0, -1.0, -1.0,
             1.0,  1.0,  1.0,
             1.0,  1.0, -1.0,

            # bottom face (y = -1)
            -1.0, -1.0, -1.0,
             1.0, -1.0,  1.0,
             1.0, -1.0, -1.0,
            -1.0, -1.0, -1.0,
            -1.0, -1.0,  1.0,
             1.0, -1.0,  1.0,

            # top face (y = +1)
            -1.0,  1.0, -1.0,
             1.0,  1.0, -1.0,
             1.0,  1.0,  1.0,
            -1.0,  1.0, -1.0,
             1.0,  1.0,  1.0,
            -1.0,  1.0,  1.0,
        ]
        self.vbo = ctx.buffer(array('f', verts).tobytes())

        self.prog = ctx.program(
            vertex_shader='''
                #version 330 core
                in vec3 in_pos;
                uniform mat4 m_model;
                uniform mat4 m_view;
                uniform mat4 m_proj;
                void main() {
                    gl_Position = m_proj * m_view * m_model * vec4(in_pos, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330 core
                out vec4 f_color;
                void main() {
                    f_color = vec4(0.2, 0.7, 1.0, 1.0);
                }
            '''
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '3f', 'in_pos')])

        self.rotation = 0.0
        self.scale = 1.0

    def draw(self, camera: Camera):
        # rotate over time
        self.rotation += 1.2 * (1.0/60.0)  # a small increment
        s = pyrr.matrix44.create_from_scale([self.scale]*3, dtype='f4')
        ry = pyrr.matrix44.create_from_y_rotation(self.rotation, dtype='f4')
        rx = pyrr.matrix44.create_from_x_rotation(self.rotation * 0.5, dtype='f4')
        model = pyrr.matrix44.multiply(ry, s)
        model = pyrr.matrix44.multiply(rx, model)

        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_view'].write(camera.view.astype('f4').tobytes())
        self.prog['m_proj'].write(camera.proj.astype('f4').tobytes())

        self.vao.render(mode=moderngl.TRIANGLES)

# -------------------------
# Sprite2D (ortho pass, true MVP)
# -------------------------
class Sprite2D:
    def __init__(self, ctx, surf: pygame.Surface, pos=(20,20), size=(128,128)):
        self.ctx = ctx
        self.pos = pos
        self.size = size

        # upload texture
        w, h = surf.get_size()
        self.tex = ctx.texture((w, h), 4)
        self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex.swizzle = 'BGRA'
        self.tex.write(surf.get_view('1'))
        self.tex.build_mipmaps()

        # Quad in local space [0..1] x [0..1] using 6 vertices (two triangles)
        quad = [
            # x, y, u, v
            0.0, 0.0,  0.0, 0.0,  # top-left
            1.0, 0.0,  1.0, 0.0,  # top-right
            0.0, 1.0,  0.0, 1.0,  # bottom-left

            1.0, 0.0,  1.0, 0.0,  # top-right
            1.0, 1.0,  1.0, 1.0,  # bottom-right
            0.0, 1.0,  0.0, 1.0,  # bottom-left
        ]
        self.vbo = ctx.buffer(array('f', quad).tobytes())

        self.prog = ctx.program(
            vertex_shader='''
                #version 330 core
                in vec2 in_pos;    // 0..1 local quad
                in vec2 in_uv;
                uniform mat4 m_model;   // maps local (0..1) to pixel coords
                uniform mat4 m_proj;    // ortho projection (pixel to NDC)
                out vec2 v_uv;
                void main() {
                    vec4 pixel_pos = m_model * vec4(in_pos, 0.0, 1.0); // pixel coords (x,y,0,1)
                    gl_Position = m_proj * pixel_pos;
                    v_uv = in_uv;
                }
            ''',
            fragment_shader='''
                #version 330 core
                in vec2 v_uv;
                uniform sampler2D tex;
                out vec4 f_color;
                void main() {
                    vec4 c = texture(tex, v_uv);
                    if (c.a < 0.01) discard;
                    f_color = c;
                }
            '''
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '2f 2f', 'in_pos', 'in_uv')])

    def draw(self, ortho_proj_2d):
        x, y = self.pos
        w, h = self.size

        # model: translate(x,y,0) * scale(w,h,1)
        translate = pyrr.matrix44.create_from_translation([x, y, 0.0], dtype='f4')
        scale = pyrr.matrix44.create_from_scale([w, h, 1.0], dtype='f4')
        model = pyrr.matrix44.multiply(translate, scale)

        # pass matrices as bytes
        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_proj'].write(ortho_proj_2d.astype('f4').tobytes())

        # bind texture and set sampler
        self.tex.use(location=0)
        self.prog['tex'].value = 0

        self.vao.render(mode=moderngl.TRIANGLES)

# -------------------------
# Main
# -------------------------
def main():
    WIN_SIZE = (1280, 720)
    win = Window("3D + 2D (Ortho) Demo - Fixed", WIN_SIZE)
    ctx = win.ctx
    width, height = WIN_SIZE

    renderer = Renderer(ctx, WIN_SIZE)
    camera = Camera(position=(0.0, 0.0, 6.0), aspect=width/float(height))

    # start with mouse grabbed
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    # add cube
    cube = Mesh3D(ctx)
    renderer.add_3d(cube)

    # build sprite surface (orange square with a white circle)
    sprite_surf = pygame.Surface((128, 128), flags=pygame.SRCALPHA)
    sprite_surf.fill((250, 100, 0, 255))
    pygame.draw.circle(sprite_surf, (255, 255, 255, 220), (64, 64), 32)

    sprite = Sprite2D(ctx, sprite_surf, pos=(20, 20), size=(128, 128))
    renderer.add_2d(sprite)

    # ortho projection: left=0, right=width, bottom=height, top=0 (y down)
    ortho_proj_2d = pyrr.matrix44.create_orthogonal_projection(
        0.0, float(width), float(height), 0.0, -1.0, 1.0, dtype='f4'
    )

    last_time = time.time()
    running = True
    print("WASD to move, SPACE/Ctrl to move up/down, mouse to look. ESC toggles mouse capture.")

    while running:
        now = time.time()
        dt = now - last_time
        last_time = now

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    grabbed = pygame.event.get_grab()
                    pygame.event.set_grab(not grabbed)
                    pygame.mouse.set_visible(grabbed)

        # mouse look only when grabbed
        if pygame.event.get_grab():
            mx, my = pygame.mouse.get_rel()
            camera.rotate(mx, my)
        else:
            # flush large rel movements if ungrabbed
            pygame.mouse.get_rel()

        # movement (frame-rate independent)
        keys = pygame.key.get_pressed()
        move_dt = dt
        if keys[pygame.K_w]:
            camera.move_forward(move_dt)
        if keys[pygame.K_s]:
            camera.move_backward(move_dt)
        if keys[pygame.K_a]:
            camera.move_left(move_dt)
        if keys[pygame.K_d]:
            camera.move_right(move_dt)
        if keys[pygame.K_SPACE]:
            camera.move_up(move_dt)
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            camera.move_down(move_dt)

        # render
        renderer.render(camera, ortho_proj_2d)

        pygame.display.flip()
        win.clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
