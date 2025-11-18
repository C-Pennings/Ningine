# demo_3d_2d_ortho.py
import sys
import math
from array import array
import time

import pygame
import moderngl
import pyrr
import numpy as np

# -------------------------
# Window / Context
# -------------------------
class Window:
    def __init__(self, title="3D + 2D (Ortho) Demo", size=(1280, 720)):
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
# Camera (FPS-style, customizable)
# -------------------------
class Camera:
    def __init__(self, position=(0.0, 0.0, 3.0), yaw=-90.0, pitch=0.0,
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
        # yaw/pitch are degrees
        cy = math.cos(math.radians(self.yaw))
        sy = math.sin(math.radians(self.yaw))
        cp = math.cos(math.radians(self.pitch))
        sp = math.sin(math.radians(self.pitch))

        fx = cy * cp
        fy = sp
        fz = sy * cp

        f = pyrr.Vector3([fx, fy, fz], dtype='f4')
        self.forward = pyrr.vector.normalize(f)
        # world up is (0,1,0)
        self.right = pyrr.vector.normalize(pyrr.vector3.cross(self.forward, [0.0, 1.0, 0.0]))
        self.up = pyrr.vector.normalize(pyrr.vector3.cross(self.right, self.forward * -1.0))

    def rotate(self, dx, dy):
        self.yaw += dx * self.sensitivity
        self.pitch -= dy * self.sensitivity  # invert Y so mouse feels normal
        # clamp pitch
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
        # look_at(position, position + forward, up)
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
        # disable depth (UI on top) and enable alpha blending
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        # basic blend func (src alpha, one minus src alpha)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        for obj in self.objects_2d:
            obj.draw(ortho_proj_2d)

# -------------------------
# Mesh3D (rotating cube)
# -------------------------
class Mesh3D:
    def __init__(self, ctx):
        self.ctx = ctx
        # cube vertices (positions only)
        # 8 unique vertices, use indices
        verts = [
            -1.0, -1.0, -1.0,
             1.0, -1.0, -1.0,
             1.0,  1.0, -1.0,
            -1.0,  1.0, -1.0,
            -1.0, -1.0,  1.0,
             1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,
            -1.0,  1.0,  1.0,
        ]
        # indices (12 triangles)
        idx = [
            0,1,2, 2,3,0,  # back
            4,5,6, 6,7,4,  # front
            0,1,5, 5,4,0,  # bottom
            3,2,6, 6,7,3,  # top
            1,2,6, 6,5,1,  # right
            3,0,4, 4,7,3   # left
        ]
        self.vbo = ctx.buffer(array('f', verts).tobytes())
        self.ibo = ctx.buffer(array('I', idx).tobytes())

        self.prog = ctx.program(
            vertex_shader='''
                #version 330
                in vec3 in_pos;
                uniform mat4 m_model;
                uniform mat4 m_view;
                uniform mat4 m_proj;
                void main() {
                    gl_Position = m_proj * m_view * m_model * vec4(in_pos, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                out vec4 f_color;
                void main() {
                    f_color = vec4(0.2, 0.7, 1.0, 1.0);
                }
            '''
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '3f', 'in_pos')], self.ibo)

        self.rotation = 0.0
        self.position = pyrr.Vector3([0.0, 0.0, 0.0], dtype='f4')
        self.scale = 1.0

    def draw(self, camera: Camera):
        # simple rotation animation
        self.rotation += 0.6 * (1.0/60.0)  # radians per frame approx (scaled by frame)
        model = pyrr.matrix44.create_from_scale([self.scale, self.scale, self.scale], dtype='f4')
        rot_y = pyrr.matrix44.create_from_y_rotation(self.rotation, dtype='f4')
        rot_x = pyrr.matrix44.create_from_x_rotation(self.rotation * 0.5, dtype='f4')
        # model = T * R * S (here we only rotate/scale)
        model = pyrr.matrix44.multiply(rot_y, model)
        model = pyrr.matrix44.multiply(rot_x, model)

        # write uniforms (matrices as bytes)
        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_view'].write(camera.view.astype('f4').tobytes())
        self.prog['m_proj'].write(camera.proj.astype('f4').tobytes())

        self.vao.render()

# -------------------------
# Sprite2D (ortho pass, uses true MVP)
# -------------------------
class Sprite2D:
    def __init__(self, ctx, surf: pygame.Surface, pos=(20,20), size=(128,128)):
        """
        surf: pygame.Surface (RGBA or RGB)
        pos: (x,y) in pixels from top-left
        size: (w,h) in pixels
        """
        self.ctx = ctx
        self.pos = pos
        self.size = size

        # upload texture
        self.tex = ctx.texture(surf.get_size(), 4)
        self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex.swizzle = 'BGRA'
        self.tex.write(surf.get_view('1'))
        self.tex.build_mipmaps()

        # Quad in local space [0..1] x [0..1] (two triangles)
        # pos.x pos.y are pixel coordinates we will convert in model matrix
        # Vertex layout: vec2 pos, vec2 uv
        quad = [
            0.0, 0.0,  0.0, 0.0,  # top-left
            1.0, 0.0,  1.0, 0.0,  # top-right
            0.0, 1.0,  0.0, 1.0,  # bottom-left
            1.0, 1.0,  1.0, 1.0,  # bottom-right
        ]
        self.vbo = ctx.buffer(array('f', quad).tobytes())

        self.prog = ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_pos;    // 0..1 local quad
                in vec2 in_uv;
                uniform mat4 m_model;   // maps from local (0..1) to screen pixel coords
                uniform mat4 m_proj;    // ortho projection (pixel to NDC)
                out vec2 v_uv;
                void main() {
                    vec4 world_pos = m_model * vec4(in_pos, 0.0, 1.0); // now in pixel coords with z=0
                    gl_Position = m_proj * world_pos;
                    v_uv = in_uv;
                }
            ''',
            fragment_shader='''
                #version 330
                in vec2 v_uv;
                uniform sampler2D tex;
                out vec4 f_color;
                void main() {
                    vec4 c = texture(tex, v_uv);
                    f_color = c;
                }
            '''
        )
        self.vao = ctx.vertex_array(self.prog, [(self.vbo, '2f 2f', 'in_pos', 'in_uv')])

    def draw(self, ortho_proj_2d):
        # m_model should map local quad [0..1] to pixel coordinates (x,y) top-left origin
        x, y = self.pos
        w, h = self.size

        # we want top-left origin in pixel space (0,0 top-left), ortho projection will be built accordingly
        # model: translate(x, y, 0) * scale(w, h, 1)
        translate = pyrr.matrix44.create_from_translation([x, y, 0.0], dtype='f4')
        scale = pyrr.matrix44.create_from_scale([w, h, 1.0], dtype='f4')
        model = pyrr.matrix44.multiply(translate, scale)  # T * S

        # set uniforms (matrices as bytes)
        self.prog['m_model'].write(model.astype('f4').tobytes())
        self.prog['m_proj'].write(ortho_proj_2d.astype('f4').tobytes())

        # bind texture
        self.tex.use(location=0)
        self.prog['tex'].value = 0

        # render quad (triangle strip)
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

# -------------------------
# Main
# -------------------------
def main():
    # settings
    WIN_SIZE = (1280, 720)
    win = Window("3D + 2D (Ortho) Demo", WIN_SIZE)
    ctx = win.ctx
    width, height = WIN_SIZE

    # create renderer and camera
    renderer = Renderer(ctx, WIN_SIZE)
    camera = Camera(position=(0.0, 0.0, 6.0), aspect=width / float(height))
    # lock mouse initially
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    # create a rotating cube
    cube = Mesh3D(ctx)
    renderer.add_3d(cube)

    # create a 2D sprite surface (simple orange square)
    sprite_surf = pygame.Surface((128, 128), flags=pygame.SRCALPHA)
    sprite_surf.fill((250, 100, 0, 255))
    # draw a simple circle inside so it's visually distinct
    pygame.draw.circle(sprite_surf, (255, 255, 255, 200), (64, 64), 32)

    sprite = Sprite2D(ctx, sprite_surf, pos=(20, 20), size=(128, 128))
    renderer.add_2d(sprite)

    # build ortho projection for 2D (pixel coordinates with top-left origin)
    # create_orthogonal_projection(left, right, bottom, top, near, far)
    # we choose left=0, right=width, bottom=height, top=0 -> so y grows downward
    ortho_proj_2d = pyrr.matrix44.create_orthogonal_projection(0.0, float(width),
                                                               float(height), 0.0,
                                                               -1.0, 1.0,
                                                               dtype='f4')

    # timing
    last_time = time.time()
    running = True

    # simple instructions printed to console
    print("WASD to move, SPACE/Ctrl to move up/down, mouse to look. ESC toggles mouse capture. Close window to exit.")

    while running:
        now = time.time()
        dt = now - last_time
        last_time = now

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    # toggle mouse capture
                    grabbed = pygame.event.get_grab()
                    pygame.event.set_grab(not grabbed)
                    pygame.mouse.set_visible(grabbed)
            # you can add more event handling here

        # mouse look (only when grabbed)
        if pygame.event.get_grab():
            mx, my = pygame.mouse.get_rel()
            camera.rotate(mx, my)
        else:
            # reset relative movement so next grab doesn't have a giant jump
            pygame.mouse.get_rel()

        # keyboard movement
        keys = pygame.key.get_pressed()
        move_dt = dt  # scale movement by dt for framerate independence
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

        # render (3D then 2D ortho)
        # update camera projection if window resized or aspect changed (not handled here)
        renderer.render(camera, ortho_proj_2d)

        pygame.display.flip()
        win.clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
