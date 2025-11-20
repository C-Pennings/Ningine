# engine/render_objects.py
"""
NINGINE — Render Objects
Week 1: Mesh + Material system stubs
Purpose: Every 3D object will be a Mesh with a Material
Clean separation: Mesh = geometry, Material = appearance
"""

import moderngl
import numpy as np
from pathlib import Path
from typing import Optional

class Mesh:
    """
    Base class for all 3D geometry (cube, sphere, player model, tree).
    Owns:
    - GPU vertex data (VBO/VAO)
    - Indices (for triangles)
    - Shader program
    """
    
    def __init__(self, ctx: moderngl.Context, shader_name: str = "simple"):
        self.ctx = ctx
        self.program = self._load_shader(shader_name)
        self.vao = None
        self.vertex_count = 0
        self.indexed = False
        
        # Child classes call this to fill geometry
        self._build_geometry()
        
    def _load_shader(self, name: str) -> moderngl.Program:
        """Load vertex + fragment shader from shaders/ folder"""
        shader_path = Path("shaders")
        vert_source = (shader_path / f"{name}.vert").read_text()
        frag_source = (shader_path / f"{name}.frag").read_text()
        return self.ctx.program(vertex_shader=vert_source, fragment_shader=frag_source)

    def _build_geometry(self):
        """Override in child classes to fill vertex data"""
        raise NotImplementedError("Child classes must implement _build_geometry()")

    def _upload_to_gpu(self, vertices: np.ndarray, indices: Optional[np.ndarray] = None):
        """Upload vertex data to GPU once"""
        self.vbo = self.ctx.buffer(vertices.tobytes())
        
        if indices is not None:
            self.index_buffer = self.ctx.buffer(indices.tobytes())
            self.vao = self.ctx.vertex_array(
                self.program, 
                [(self.vbo, '3f', 'in_position')],
                index_buffer=self.index_buffer
            )
            self.vertex_count = len(indices)
            self.indexed = True
        else:
            self.vao = self.ctx.vertex_array(
                self.program, 
                [(self.vbo, '3f', 'in_position')]
            )
            self.vertex_count = len(vertices) // 3  # 3 floats per vertex
            self.indexed = False

    def draw(self):
        """Draw this mesh — called by Renderer"""
        if self.vao:
            self.vao.render(moderngl.TRIANGLES)  # ← CLEANEST AND SAFEST

    def __repr__(self):
        return f"Mesh(vertices={self.vertex_count})"


class CubeMesh(Mesh):
    def __init__(self, ctx: moderngl.Context):
        super().__init__(ctx, shader_name="default")  # ← "default" not "simple"

    def _build_geometry(self):
        vertices = np.array([
            -1,-1,-1,  1,-1,-1,  1, 1,-1, -1, 1,-1,
            -1,-1, 1,  1,-1, 1,  1, 1, 1, -1, 1, 1,
            -1,-1,-1, -1,-1, 1, -1, 1, 1, -1, 1,-1,
             1,-1,-1,  1,-1, 1,  1, 1, 1,  1, 1,-1,
            -1,-1,-1,  1,-1,-1,  1,-1, 1, -1,-1, 1,
            -1, 1,-1,  1, 1,-1,  1, 1, 1, -1, 1, 1,
        ], dtype='f4').reshape(-1, 3)

        indices = np.array([
            0,1,2, 2,3,0, 4,5,6, 6,7,4, 8,9,10, 10,11,8,
            12,13,14, 14,15,12, 16,17,18, 18,19,16, 20,21,22, 22,23,20
        ], dtype='i4')

        self._upload_to_gpu(vertices, indices)
        print("CUBE UPLOADED — YOU WILL SEE IT")

class Material:
    def __init__(self, color=(1.0, 0.2, 0.8)):
        self.color = np.array(color, dtype=np.float32)
        self.emissive = np.array([3.0, 1.0, 3.0], dtype=np.float32)  # NUCLEAR GLOW
        self.alpha = 1.0

    def bind(self, program):
        # BULLETPROOF — uses .value instead of .write()
        if 'u_color' in program:
            program['u_color'].value = tuple(self.color)
        if 'u_emissive' in program:
            program['u_emissive'].value = tuple(self.emissive)
        if 'u_alpha' in program:
            program['u_alpha'].value = self.alpha



    def __repr__(self):
        return f"Material(color={self.color}, metallic={self.metallic:.1f})"


class Default(Material):
    """
    Automatic fallback material — every Mesh gets this if no material specified
    Purple, slightly shiny — looks good on everything
    """
    
    def __init__(self):
        super().__init__(color=(0.8, 0.3, 0.6))  # Purple
        self.metallic = 0.1
        self.roughness = 0.7
        print("[Default] Fallback material ready")