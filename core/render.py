# engine/renderer.py
"""
NINGINE Renderer – Handles 2D + 3D + Instancing
Week 1 Goal: One class that can draw anything
"""

import moderngl
import pygame
import numpy as np
from typing import List
from core.camera import Camera
from core.scene import Scene

class Renderer:
    """
    Single renderer for the entire engine.
    Responsibilities:
    1. Own the ModernGL context
    2. Draw 3D objects (regular + instanced)
    3. Draw 2D UI on top
    4. Manage render passes (skybox first, UI last)
    """
    
    def __init__(self, screen_size=(1280, 720)):
        # 1. Create window + ModernGL context
        pygame.display.set_mode(screen_size, pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND)
        self.width, self.height = screen_size
        
        # For additive blending (lights, particles)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Collections we will fill later
        self.instanced_meshes = []   # 50k grass, trees
        self.regular_meshes = []     # Player, enemies
        
        print("[Renderer] Ready – ModernGL context created")

    # ------------------------------------------------------------------
    # PUBLIC API – These are the only functions your game code will call
    # ------------------------------------------------------------------
    def begin_frame(self, camera: Camera):
        """Call at start of every frame"""
        self.camera = camera
        self.ctx.clear(0.1, 0.15, 0.25, 1.0)  # Dark sky blue
        
    def draw_scene(self, scene: Scene):
        """Draw everything in the scene"""
        # Pass 1: Skybox (first, depth ignored)
        self.draw_skybox()
        
        # Pass 2: 3D opaque objects (regular + instanced)
        self.draw_3d_opaque(scene)
        
        # Pass 3: 3D transparent objects (later)
        # self.draw_3d_transparent(scene)
        
        # Pass 4: 2D overlay (UI, health bars)
        self.draw_2d_overlay(scene)
        
    def end_frame(self):
        """Swap buffers – show what we drew"""
        pygame.display.flip()

    # ------------------------------------------------------------------
    # STUBS – You will fill these one per week
    # ------------------------------------------------------------------
    def draw_skybox(self):
        """Week 2 – draw infinite sky"""
        pass

    def draw_3d_opaque(self, scene: Scene):
        """Week 1–4 – draw cubes, instanced grass, etc."""
        # Example stub for one spinning cube (Week 1 test)
        self._draw_test_cube()

    def draw_2d_overlay(self, scene: Scene):
        """Week 6 – draw health bar, inventory, etc."""
        pass

    # ------------------------------------------------------------------
    # PRIVATE HELPERS – You will replace these as we go
    # ------------------------------------------------------------------
    def _draw_test_cube(self):
        """Temporary spinning cube so you see something immediately"""
        # This will be replaced with real PBR cube in ~2 days
        pass

    # Future methods you will add:
    # - add_instanced_mesh(mesh, instances)
    # - upload_lights(lights)
    # - set_2d_mode() / set_3d_mode()