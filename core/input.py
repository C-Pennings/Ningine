from funcs import load_json
import pygame
#A abstracted class for importing input configs and handling inputs.

class Input:
    def __init__(self, path):
        self.path = path

        try:    
            self.config = load_json(path)
        except: #after change config to link actions to constants and use this default for recording values
            self.config = { #keys = constant|bool
                'keys': {},
                'mouse': {
                    'pos': [0,0], #buttons = int|bool
                    'button': {}
                }
            }
    
    def get_all_events(self):
        return self.config
    
    def get_mouse_events(self):
        return self.config['mouse']
    
    def get_keyboard_events(self):
        return self.config['keys']

    def get_mouse_pos(self):
        return self.config['mouse']['pos']
    
    def update(self):
        events = pygame.event.get()
        self.config['mouse']['pos'] = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.config['key'][event.key] = True
            if event.type == pygame.KEYUP:
                self.config['key'][event.key] = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.config['mouse']['button'] = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.config['mouse']['button'] = False

    