# core/input.py
import pygame
from typing import Dict, Any
from funcs import load_json  # Your JSON loader

class Input:
    """
    Data-driven input system.
    - Loads config from JSON (future: bind actions to keys)
    - Tracks pressed/down/released for GUI + games
    - Immutable state snapshot per frame
    """
    def __init__(self, path: str = None):
        self.path = path
        self.config = self._load_config(path)
        self._reset_frame_state()

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load JSON or fallback to default."""
        if path:
            try:
                return load_json(path)
            except Exception as e:
                print(f"[Input] Failed to load {path}: {e}")
        
        # Default structure – future: bind "jump" → pygame.K_SPACE
        return {
            'keys': {},           # pygame.K_w: True
            'mouse': {
                'pos': [0, 0],
                'buttons': {1: False, 2: False, 3: False},  # LMB, RMB, MMB
                'pressed': {1: False, 2: False, 3: False},
                'released': {1: False, 2: False, 3: False}
            }
        }

    def _reset_frame_state(self):
        """Reset one-frame events."""
        for btn in self.config['mouse']['pressed']:
            self.config['mouse']['pressed'][btn] = False
            self.config['mouse']['released'][btn] = False

    def update(self) -> None:
        """Poll events, update state. Call once per frame."""
        self._reset_frame_state()
        events = pygame.event.get()

        # Update mouse pos
        self.config['mouse']['pos'] = list(pygame.mouse.get_pos())

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            elif event.type == pygame.KEYDOWN:
                self.config['keys'][event.key] = True

            elif event.type == pygame.KEYUP:
                self.config['keys'][event.key] = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                btn = event.button
                if btn in (1, 2, 3):
                    self.config['mouse']['buttons'][btn] = True
                    self.config['mouse']['pressed'][btn] = True

            elif event.type == pygame.MOUSEBUTTONUP:
                btn = event.button
                if btn in (1, 2, 3):
                    self.config['mouse']['buttons'][btn] = False
                    self.config['mouse']['released'][btn] = True

    # ——— ACCESSORS ———

    def get_state(self) -> Dict[str, Any]:
        """Immutable snapshot for GUI/game logic."""
        return {
            'mouse_pos': tuple(self.config['mouse']['pos']),
            'mouse_down': {k: v for k, v in self.config['mouse']['buttons'].items()},
            'mouse_pressed': {k: v for k, v in self.config['mouse']['pressed'].items()},
            'mouse_released': {k: v for k, v in self.config['mouse']['released'].items()},
            'keys': {k: v for k, v in self.config['keys'].items()}
        }

    def get_mouse_pos(self) -> tuple[int, int]:
        return tuple(self.config['mouse']['pos'])

    def is_key_down(self, key: int) -> bool:
        return self.config['keys'].get(key, False)

    def is_mouse_down(self, button: int = 1) -> bool:
        return self.config['mouse']['buttons'].get(button, False)

    def was_mouse_pressed(self, button: int = 1) -> bool:
        return self.config['mouse']['pressed'].get(button, False)

    def was_mouse_released(self, button: int = 1) -> bool:
        return self.config['mouse']['released'].get(button, False)