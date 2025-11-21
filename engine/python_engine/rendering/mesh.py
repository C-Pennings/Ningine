#imports
import moderngl

#specfic imports
from abc import ABC, abstractmethod

class AbstractMesh(ABC):
    """This class is not supposted to be called by main program it is used as a template for other mesh classes"""
    def __init__(self, ctx, data, material=None):
        self.ctx = ctx
        self.data = data
        self.material = material
    
    @abstractmethod
    def build(self):
        pass

    def draw(self):
        pass

class Mesh(AbstractMesh):
    def __init__(self, ctx, path, material=None):
        #import data with path
        data = None

        super().__init__(ctx, data, material)
    
    def build(self):
        pass

    def draw(self):
        pass