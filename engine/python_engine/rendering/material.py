#Materials contain shaders and different matarial attributes like a smoothness, metalics, color, etc
#materials also contain the textures for a object, so specific materials go with specifc meshes if using a texture.

#imports
import moderngl


class Material:
    def __init__(self, color, shaderName='default', textureImg=None):
        self.color = color

        self.get_shader(shaderName)

    def get_shader(self, name):
        pass

    def get_texture(self, img):
        pass

    def bind(self, program):
        pass

