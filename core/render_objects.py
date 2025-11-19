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
            if self.indexed:
                self.vao.render(index_count=self.vertex_count)
            else:
                self.vao.render(count=self.vertex_count)

    def __repr__(self):
        return f"Mesh(vertices={self.vertex_count})"


class CubeMesh(Mesh):
    """
    Simple cube geometry — 8 vertices, 12 triangles (36 indices)
    Purple by default — material changes color later
    """
    
    def __init__(self, ctx: moderngl.Context):
        super().__init__(ctx, shader_name="simple")
        print("[CubeMesh] Purple cube ready")

    def _build_geometry(self):
        """Create cube vertices + triangle indices"""
        # 8 unique corner positions
        vertices = np.array([
            # Back face (-Z)
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            # Front face (+Z)
            [-1, -1, 1],  [1, -1, 1],  [1, 1, 1],  [-1, 1, 1]
        ], dtype='f4')

        # 36 indices = 12 triangles
        indices = np.array([
            # Back face
            0, 1, 2,  2, 3, 0,
            # Front face  
            4, 6, 5,  4, 7, 6,
            # Left face
            0, 4, 7,  7, 3, 0,
            # Right face
            1, 5, 6,  6, 2, 1,
            # Bottom face
            0, 1, 5,  5, 4, 0,
            # Top face
            3, 2, 6,  6, 7, 3
        ], dtype='i4')

        self._upload_to_gpu(vertices, indices)


class Material:
    """
    Controls how a Mesh looks (color, texture, shader).
    Default materials make everything look good automatically.
    """
    
    def __init__(self, color: tuple = (0.8, 0.3, 0.6)):
        self.color = np.array(color, dtype='f4')
        self.texture = None
        self.emissive = np.array([0.0, 0.0, 0.0], dtype='f4')
        self.metallic = 0.0
        self.roughness = 0.8

    def bind(self, program: moderngl.Program):
        """Send material data to shader"""
        program['u_albedo'].write(self.color.tobytes())
        program['u_metallic'].value = self.metallic
        program['u_roughness'].value = self.roughness
        program['u_emissive'].write(self.emissive.tobytes())

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