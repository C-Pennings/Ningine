from .renderSystem import Mesh
import numpy as np
import moderngl

class CubeMesh(Mesh):
    def __init__(self, ctx):
        super().__init__(ctx, "default")

    def build_geometry(self):
        # Share static geometry buffers across all CubeMesh instances per-context
        cache = getattr(CubeMesh, '_geom_cache', None)
        if cache is None:
            cache = {}
            setattr(CubeMesh, '_geom_cache', cache)
        key = id(self.ctx)
        if key not in cache:
            v = np.array([
                -1,-1,-1, 1,-1,-1, 1,1,-1, -1,1,-1,
                -1,-1,1, 1,-1,1, 1,1,1, -1,1,1,
                -1,-1,-1, -1,-1,1, -1,1,1, -1,1,-1,
                1,-1,-1, 1,-1,1, 1,1,1, 1,1,-1,
                -1,-1,-1, 1,-1,-1, 1,-1,1, -1,-1,1,
                -1,1,-1, 1,1,-1, 1,1,1, -1,1,1
            ], dtype='f4').reshape(-1, 3)

            i = np.array([
                0,1,2,2,3,0, 4,5,6,6,7,4, 8,9,10,10,11,8,
                12,13,14,14,15,12, 16,17,18,18,19,16, 20,21,22,22,23,20
            ], dtype='i4')

            vbo = self.ctx.buffer(v.tobytes())
            ibo = self.ctx.buffer(i.tobytes())
            cache[key] = (vbo, ibo)
        vbo, ibo = cache[key]
        # Build a VAO referencing the shared buffers
        self.vao = self.ctx.vertex_array(self.program, [(vbo, '3f', 'in_position')], index_buffer=ibo)

# core/render_objects.py → Replace your MeshObject with this
class MeshObject(Mesh):
    def __init__(self, ctx, data, tag, shader='default', material=None):
        self.data = data
        self.tag = tag
        super().__init__(ctx, shader, material)

    def build_geometry(self):
        # Cache per model tag + context
        cache = getattr(MeshObject, self.tag, None)
        if cache is None:
            cache = {}
            setattr(MeshObject, self.tag, cache)

        key = id(self.ctx)
        if key not in cache:
            v = self.data['v'].astype(np.float32)
            i = self.data['i'].ravel().astype(np.uint32)  # ← FLATTENED

            vbo = self.ctx.buffer(v.tobytes())
            ibo = self.ctx.buffer(i.tobytes())
            cache[key] = (vbo, ibo, len(i))  # store index count too

        vbo, ibo, index_count = cache[key]

        self.vao = self.ctx.vertex_array(
            self.program,
            [(vbo, '3f', 'in_position')],
            index_buffer=ibo,
            index_element_size=4  # uint32
        )
        self.index_count = index_count  # for draw call

    def draw(self):
        if self.vao:
            self.material.bind(program=self.program)
            self.vao.render(moderngl.TRIANGLES)
