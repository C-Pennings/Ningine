import pygame

class GUIManager:
    def __init__(self, path):
        self.objs = {} # type or id | object

    def get_gui(self, id):
        return self.objs[id]
    
    def add(self, type, obj):
        self.objs[type] = obj
    
    def delete(self, type):
        if type in self.objs:
            del self.objs[type]

    def update(self, input_events): #updates the gui state and 
        pass

    def render(self, renderObject): #Renders the gui
        pass

    def get_active_events(self): #for example this returns all active buttons (buttons that are being clicked)
        pass