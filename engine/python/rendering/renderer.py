import moderngl
import pygame

class Renderer:
    def __init__(self, width, height, title='Test Window'):
        #start pygame
        pygame.init()

        #define variables
        self.width = width
        self.height = height

        #setup pygame window with moderngl context
        self.window = pygame.display.set_mode((self.width, self.height), flags = pygame.OPENGL | pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()

        #setup render data
        self.meshes = []
    
    def render(self):
        #get camera matrix information with rust

        for mesh in self.meshes:
            #bind mesh material

            #draw mesh
            mesh.draw()
