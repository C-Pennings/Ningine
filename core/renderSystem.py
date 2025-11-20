# core/render_objects.py
import moderngl
import pygame, os
import numpy as np
from pygame.math import Vector3
from pathlib import Path
from PIL import Image
import time

class Renderer:
    def __init__(self, size=(1280, 720)):
        pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.width, self.height = size
        self.meshes = []

        # Camera setup
        self.camera = Camera(Vector3(0, 1, 10), self.width, self.height, target=Vector3(0, 0, 0), up=Vector3(0, 1, 0))
        self.proj = self.camera.get_proj()
        self.view = self.camera.get_view()
        # Debug overlay (on-screen FPS and info)
        pygame.font.init()
        self._font = pygame.font.SysFont(None, 18)
        self._overlay = DebugOverlay(self.ctx, self.width, self.height, self._font)
        self._fps_clock = pygame.time.Clock()
        # Update overlay text once per second to reduce jitter
        self._overlay_last = 0.0
        self._overlay_interval = 1.0
        self._start_time = time.time()
        self.skybox = None

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

    def set_skybox(self, path='assets/skybox'):
        """Load and attach a skybox from a directory containing 6 cube faces."""
        self.skybox = SkyBox(self.ctx, path)
    
    def set_camera(self, camera):
        """Sets the camera"""
        self.camera = camera

    def begin_frame(self):
        self.ctx.clear(0.2, 0.2, 0.3, 1.0)        # Dark gray background so pink is visible
        self.ctx.enable(moderngl.DEPTH_TEST)

    def draw_scene(self):
        # Update matrices from camera and precompute common state once per frame
        if self.camera:
            self.proj = self.camera.get_proj()
            self.view = self.camera.get_view()
        else:
            pass
            
        proj_bytes = self.proj.T.tobytes()
        view_bytes = self.view.T.tobytes()
        elapsed = time.time() - getattr(self, '_start_time', 0.0)
        # Render skybox first (without depth test) so it's behind all geometry
        if getattr(self, 'skybox', None):
            self.skybox.render(self.ctx, self.proj, self.view)

        # Identity model (rotation handled in shader via u_time)
        model = np.eye(4, dtype='f4')
        model_bytes = model.T.tobytes()

        last_prog = None
        for mesh in self.meshes:
            prog = mesh.program

            if prog is not last_prog:
                try:
                    prog['u_proj'].write(proj_bytes)
                except KeyError:
                    pass
                try:
                    prog['u_view'].write(view_bytes)
                except KeyError:
                    pass
                try:
                    prog['u_time'].value = float(elapsed)
                except KeyError:
                    pass
                last_prog = prog

            try:
                prog['u_model'].write(model_bytes)
            except KeyError:
                pass

            mesh.draw()
        # Update and draw debug overlay (FPS + simple stats)
        # tick internal clock so get_fps() returns a value
        self._fps_clock.tick()
        fps = self._fps_clock.get_fps()
        now = time.time()
        # update the overlay text only once per second
        if now - self._overlay_last >= self._overlay_interval:
            info = f"FPS: {fps:.1f} | Meshes: {len(self.meshes)}"
            self._overlay.update_text(info)
            self._overlay_last = now
        # always render the overlay (uses cached texture)
        self._overlay.render()
        
    def end_frame(self):
        pygame.display.flip()

class Mesh:
    def __init__(self, ctx, shader_name="default", material = None):
        self.ctx = ctx
        self.program = self._load_shader(shader_name)
        self.vao = None
        self.material = material or DefaultMaterial()
        self.build_geometry()

    def _load_shader(self, name):
        # Cache compiled programs per context + shader name
        cache = getattr(self.__class__, '_program_cache', None)
        if cache is None:
            cache = {}
            setattr(self.__class__, '_program_cache', cache)
        key = (id(self.ctx), name)
        if key in cache:
            return cache[key]
        path = Path("shaders")
        vert = (path / f"{name}.vert").read_text()
        frag = (path / f"{name}.frag").read_text()
        prog = self.ctx.program(vertex_shader=vert, fragment_shader=frag)
        cache[key] = prog
        return prog

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
        if hasattr(self, 'vao') and self.vao:
            self.material.bind(program=self.program)
            if hasattr(self, 'index_count'):
                self.vao.render(moderngl.TRIANGLES, indices=self.index_count)
            else:
                self.vao.render(moderngl.TRIANGLES)

class DebugOverlay:
    """Render a small on-screen text overlay using pygame font -> texture -> moderngl quad."""
    def __init__(self, ctx, screen_w, screen_h, font):
        self.ctx = ctx
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font = font

        # Simple textured quad shader (positions are in NDC)
        vert = '''#version 330 core
        in vec2 in_pos;
        in vec2 in_uv;
        out vec2 v_uv;
        void main() {
            gl_Position = vec4(in_pos, 0.0, 1.0);
            v_uv = in_uv;
        }'''

        frag = '''#version 330 core
        uniform sampler2D u_tex;
        in vec2 v_uv;
        out vec4 frag_color;
        void main() {
            frag_color = texture(u_tex, v_uv);
        }'''

        self.program = self.ctx.program(vertex_shader=vert, fragment_shader=frag)
        self.program['u_tex'] = 0

        # Create an empty texture placeholder; will be resized on first draw
        self.texture = None

    def _create_texture(self, w, h, data=None):
        if self.texture is not None:
            try:
                self.texture.release()
            except Exception:
                pass
        tex = self.ctx.texture((w, h), 4, data=data)
        tex.build_mipmaps = False
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture = tex
        return tex

    def update_text(self, text):
        """Update the overlay texture when the text changes or size changes."""
        if text == getattr(self, '_last_text', None):
            return
        self._last_text = text

        # Render text to a pygame surface with alpha
        lines = str(text).split('\n')
        padding = 6
        line_surfs = [self.font.render(l, True, (255, 255, 255)) for l in lines]
        w = max(s.get_width() for s in line_surfs) + padding * 2
        h = sum(s.get_height() for s in line_surfs) + padding * 2

        surf = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        surf = surf.convert_alpha()
        y = padding
        for s in line_surfs:
            surf.blit(s, (padding, y))
            y += s.get_height()

        # Convert surface to bytes (RGBA) and upload to texture
        buf = pygame.image.tostring(surf, 'RGBA', False)
        if self.texture is None or self.texture.size != (w, h):
            self._create_texture(w, h, buf)
        else:
            self.texture.write(buf)

        # (re)create quad geometry for this texture size
        margin_x = 10
        margin_y = 10
        x0 = (margin_x / self.screen_w) * 2.0 - 1.0
        y0 = 1.0 - (margin_y / self.screen_h) * 2.0
        x1 = ((margin_x + w) / self.screen_w) * 2.0 - 1.0
        y1 = 1.0 - ((margin_y + h) / self.screen_h) * 2.0

        verts = np.array([
            x0, y0, 0.0, 0.0,
            x1, y0, 1.0, 0.0,
            x1, y1, 1.0, 1.0,
            x0, y0, 0.0, 0.0,
            x1, y1, 1.0, 1.0,
            x0, y1, 0.0, 1.0,
        ], dtype='f4')

        # release old buffers if present
        if getattr(self, 'vbo', None) is not None:
            try:
                self.vbo.release()
            except Exception:
                pass
        if getattr(self, 'vao', None) is not None:
            try:
                self.vao.release()
            except Exception:
                pass

        self.vbo = self.ctx.buffer(verts.tobytes())
        self.vao = self.ctx.vertex_array(self.program, [(self.vbo, '2f 2f', 'in_pos', 'in_uv')])

    def render(self):
        """Render the overlay using the current texture and VAO."""
        if self.texture is None or getattr(self, 'vao', None) is None:
            return
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.texture.use(location=0)
        self.vao.render()
        self.ctx.disable(moderngl.BLEND)
        self.ctx.enable(moderngl.DEPTH_TEST)

class Material:
    def __init__(self, color=(0,0,0), tex=None):
        self.color = color
        self.texture = tex
    
    def bind(self, program):
        try:
            if not self.texture:
                program['u_color'].value = tuple(map(float, self.color))
            else:
                pass
        except KeyError:
            pass          

class DefaultMaterial(Material):
    def __init__(self):
        super().__init__(color=(0.5, 0.5, 0.5))

class Camera:
    def __init__(self, pos, width, height, rot=(0,0,0), target=None, up=None, near=0.1, far=100.0, fov=45.0):
        self.position = pos
        self.rotation = rot
        self.target = target if target is not None else Vector3(0, 0, 0)
        self.up = up if up is not None else Vector3(0, 1, 0)
        self.near = float(near)
        self.far = float(far)
        self.fov = float(fov)
        self.aspect = width/height
        self.yaw = 0.0
        self.pitch = 0.0
    
    def get_proj(self):
        fov = np.radians(self.fov)
        f = 1.0 / np.tan(fov / 2.0)
        n, fa = self.near, self.far
        a = self.aspect
        return np.array([
            [f / a, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (fa + n) / (n - fa), (2 * fa * n) / (n - fa)],
            [0.0, 0.0, -1.0, 0.0]
        ], dtype='f4')

    def get_view(self):
        eye = self.position
        target = self.target
        up = self.up
        f = (target - eye).normalize()
        s = f.cross(up).normalize()
        u = s.cross(f)
        return np.array([
            [s.x, s.y, s.z, -s.dot(eye)],
            [u.x, u.y, u.z, -u.dot(eye)],
            [-f.x, -f.y, -f.z, f.dot(eye)],
            [0, 0, 0, 1]
        ], dtype='f4')

    def set_aspect(self, width, height):
        self.aspect = width / height


class Light:
    def __init__(self):
        pass

class SkyBox:
    """
    Loads a cubemap from a folder and renders a cube as the skybox.
    Expected file naming includes tokens per face, e.g.:
      - right/left/top/bottom/front/back
      - or px/nx/py/ny/pz/nz
    """
    def __init__(self, ctx, path='assets/skybox', face_map=None):
        self.ctx = ctx
        self.texture = self._load_cubemap(ctx, path, face_map)

        # Skybox shaders embedded to avoid external file dependency
        vert = '''#version 330 core
        layout(location=0) in vec3 in_position;
        out vec3 v_dir;
        uniform mat4 u_proj;
        uniform mat4 u_view; // with zeroed translation
        void main() {
            v_dir = in_position;
            vec4 pos = u_proj * u_view * vec4(in_position, 1.0);
            gl_Position = pos.xyww; // keep at far depth
        }'''

        frag = '''#version 330 core
        in vec3 v_dir;
        uniform samplerCube u_cube;
        out vec4 frag_color;
        void main() {
            frag_color = texture(u_cube, normalize(v_dir));
        }'''

        self.program = ctx.program(vertex_shader=vert, fragment_shader=frag)
        self.program['u_cube'] = 0

        # Cube geometry (positions only), reuse same layout as regular cube
        v = np.array([
            -1,-1,-1, 1,-1,-1, 1,1,-1, -1,1,-1,
            -1,-1, 1, 1,-1, 1, 1,1, 1, -1,1, 1,
            -1,-1,-1, -1,-1, 1, -1,1, 1, -1,1,-1,
             1,-1,-1,  1,-1, 1,  1,1, 1,  1,1,-1,
            -1,-1,-1,  1,-1,-1,  1,-1, 1, -1,-1, 1,
            -1, 1,-1,  1, 1,-1,  1, 1, 1, -1, 1, 1
        ], dtype='f4').reshape(-1, 3)

        i = np.array([
            0,1,2,2,3,0, 4,5,6,6,7,4, 8,9,10,10,11,8,
            12,13,14,14,15,12, 16,17,18,18,19,16, 20,21,22,22,23,20
        ], dtype='i4')

        self.vbo = ctx.buffer(v.tobytes())
        self.ibo = ctx.buffer(i.tobytes())
        self.vao = ctx.vertex_array(self.program, [(self.vbo, '3f', 'in_position')], index_buffer=self.ibo)

    def _load_cubemap(self, ctx, folder, face_map=None):
        def list_images(d):
            if not os.path.isdir(d):
                return []
            files = []
            for entry in os.listdir(d):
                p = os.path.join(d, entry)
                if os.path.isfile(p) and entry.lower().endswith(('.png','.jpg','.jpeg','.bmp','.tga')):
                    files.append(p)
            return files

        files = list_images(folder)
        if not files:
            # Create a 1x1 blue cubemap as a fallback
            tex = ctx.texture_cube((1,1), 3, data=None)
            tex.write(0, bytes([0,0,255]))
            tex.write(1, bytes([0,0,255]))
            tex.write(2, bytes([0,0,255]))
            tex.write(3, bytes([0,0,255]))
            tex.write(4, bytes([0,0,255]))
            tex.write(5, bytes([0,0,255]))
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            try:
                tex.repeat_x = False
                tex.repeat_y = False
                tex.repeat_z = False
            except Exception:
                pass
            return tex

        # Resolve faces
        tokens = face_map or {
            'right': ['right','px','posx'],
            'left':  ['left','nx','negx'],
            'top':   ['top','up','py','posy'],
            'bottom':['bottom','down','ny','negy'],
            'front': ['front','pz','posz'],
            'back':  ['back','nz','negz'],
        }
        order = ['right','left','top','bottom','front','back']

        resolved = {}
        lower_map = {p: os.path.basename(p).lower() for p in files}
        for face in order:
            for p, name in lower_map.items():
                if any(tok in name for tok in tokens[face]):
                    resolved[face] = p
                    break

        # Fallback: if not all faces found, just sort and pick first 6
        if len(resolved) < 6 and len(files) >= 6:
            files_sorted = sorted(files)
            resolved = dict(zip(order, files_sorted[:6]))

        # Load images and upload to cubemap
        tex = None
        for idx, face in enumerate(order):
            fp = resolved.get(face)
            if not fp:
                # fallback to first available image
                fp = files[0]
            img = Image.open(fp)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Flip Y to match GL origin if needed
            #img = img.transpose(Image.FLIP_TOP_BOTTOM)
            w, h = img.size
            if tex is None:
                tex = ctx.texture_cube((w, h), 3, data=None)
                tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
                try:
                    tex.repeat_x = False
                    tex.repeat_y = False
                    tex.repeat_z = False
                except Exception:
                    pass
            tex.write(idx, img.tobytes())
        return tex

    def render(self, ctx, proj, view):
        # Remove translation from the view matrix
        view_nt = view.copy()
        view_nt[0,3] = 0.0
        view_nt[1,3] = 0.0
        view_nt[2,3] = 0.0

        # Render skybox without depth test so it always draws behind
        ctx.disable(moderngl.DEPTH_TEST)
        self.program['u_proj'].write(proj.T.tobytes())
        self.program['u_view'].write(view_nt.T.tobytes())
        self.texture.use(location=0)
        self.vao.render(moderngl.TRIANGLES)
        ctx.enable(moderngl.DEPTH_TEST)

 