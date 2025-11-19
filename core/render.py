# engine/renderer.py
"""
NINGINE — Renderer (Week 1 Final Version)
Purpose: Draws any Mesh with any Material
Supports:
- 3D meshes (CubeMesh, etc.)
- Per-mesh model matrix (position/rotation/scale)
- Material colors + emissive glow
- Clean render loop
"""

import moderngl
import pygame
import numpy as np
from pygame.math import Vector3
from typing import List, Optional
from core.render_objects import Mesh

class Renderer:
    """The single class that draws everything in the game."""
    
    def __init__(self, screen_size=(1280, 720)):
        pygame.display.set_mode(screen_size, pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        self.width, self.height = screen_size
        self.meshes: List[Mesh] = []           # All meshes to draw
        self.camera_pos = Vector3(4, 3, 5)     # Temporary camera
        self.proj = self._make_projection_matrix()
        self.view = self._make_view_matrix()

        print("[Renderer] Ready — PBR-ready, Material system active")

    # ─────────────────────────────── MATRIX HELPERS ───────────────────────────────
    def _make_projection_matrix(self):
        """Perspective projection matrix"""
        f = 1.0 / np.tan(np.radians(45) / 2)
        return np.array([
            [f / (self.width/self.height), 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (0.1+100)/(0.1-100), (2*0.1*100)/(0.1-100)],
            [0, 0, -1, 0]
        ], dtype='f4')

    def _make_view_matrix(self):
        """Look-at matrix (camera)"""
        eye = self.camera_pos
        target = Vector3(0, 0, 0)
        up = Vector3(0, 1, 0)
        f = (target - eye).normalize()
        s = f.cross(up).normalize()
        u = s.cross(f)
        return np.array([
            [ s.x,  s.y,  s.z, -s.dot(eye)],
            [ u.x,  u.y,  u.z, -u.dot(eye)],
            [-f.x, -f.y, -f.z,  f.dot(eye)],
            [   0,    0,    0,           1]
        ], dtype='f4')

    # ─────────────────────────────── PUBLIC API ───────────────────────────────
    def add_mesh(self, mesh: Mesh):
        """Add a mesh to be drawn every frame"""
        self.meshes.append(mesh)
        return mesh  # for chaining

    def begin_frame(self):
        """Clear screen"""
        self.ctx.clear(0.1, 0.15, 0.25, 1.0)

    def draw_scene(self):
        """Draw all meshes with their materials"""
        for mesh in self.meshes:
            if not mesh.vao:
                continue

            program = mesh.program
            
            # Upload camera matrices
            program['u_proj'].write(self.proj.tobytes())
            program['u_view'].write(self.view.tobytes())
            
            # Upload model matrix (per-mesh transform — coming next week)
            model = np.identity(4, dtype='f4')  # identity for now
            program['u_model'].write(model.tobytes())
            
            # Upload camera position (for PBR later)
            program['u_cam_pos'].value = (self.camera_pos.x, self.camera_pos.y, self.camera_pos.z)
            
            # Let material send its colors
            if hasattr(mesh, 'material') and mesh.material:
                mesh.material.bind(program)
            else:
                # Fallback white if no material
                program['u_color'].value = (1.0, 1.0, 1.0)
                program['u_emissive'].value = (0.0, 0.0, 0.0)
            
            # DRAW!
            mesh.draw()

    def end_frame(self):
        pygame.display.flip()