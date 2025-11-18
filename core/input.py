# core/input.py
# NINGINE — Universal Input System (Week 2 Day 1 Complete)

import pygame
from typing import Dict, Any
from .funcs import load_json  # your existing helper


class Input:
    """
    Data-driven input manager.
    - Supports future input_config.json (action bindings)
    - Tracks held / pressed / released for mouse + keyboard
    - Returns clean immutable state dict every frame
    """

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path

        # Default structure (will be overridden by JSON later)
        default = {
            'keys': {},  # pygame.K_w: True/False
            'mouse': {
                'pos': [0, 0],
                'buttons': {1: False, 2: False, 3: False},     # LMB, RMB, MMB held
                'pressed': {1: False, 2: False, 3: False},     # one-frame down
                'released': {1: False, 2: False, 3: False}    # one-frame up
            }
        }

        if config_path:
            try:
                self.config = load_json(config_path)
                print(f"[Input] Loaded config from {config_path}")
            except Exception as e:
                print(f"[Input] Failed to load {config_path} → using default ({e})")
                self.config = default
        else:
            self.config = default

        # Ensure mouse sub-dicts exist even if JSON is incomplete
        mouse = self.config.setdefault('mouse', {})
        mouse.setdefault('pos', [0, 0])
        mouse.setdefault('buttons', {1: False, 2: False, 3: False})
        mouse.setdefault('pressed', {1: False, 2: False, 3: False})
        mouse.setdefault('released', {1: False, 2: False, 3: False})

    def _reset_one_frame_events(self):
        """Clear pressed/released every frame."""
        for btn in self.config['mouse']['pressed']:
            self.config['mouse']['pressed'][btn] = False
            self.config['mouse']['released'][btn] = False

    def update(self) -> Dict[str, Any]:
        """
        Call once per frame.
        Returns immutable snapshot for GUI / game logic.
        """
        self._reset_one_frame_events()

        # Update mouse position every frame
        self.config['mouse']['pos'] = list(pygame.mouse.get_pos())

        for event in pygame.event.get():
            # Global quit
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit("Window closed")

            # Keyboard
            elif event.type == pygame.KEYDOWN:
                self.config['keys'][event.key] = True
            elif event.type == pygame.KEYUP:
                self.config['keys'][event.key] = False

            # Mouse buttons
            elif event.type == pygame.MOUSEBUTTONDOWN:
                btn = event.button
                if btn in (1, 2, 3):
                    self.config['mouse']['buttons'][btn] = True
                    # held
                    self.config['mouse']['pressed'][btn] = True                     # one-frame

            elif event.type == pygame.MOUSEBUTTONUP:
                btn = event.button
                if btn in (1, 2, 3):
                    self.config['mouse']['buttons'][btn] = False                   # no longer held
                    self.config['mouse']['released'][btn] = True                    # one-frame

        # Return clean snapshot
        return self.get_state()

    # ——— PUBLIC ACCESSORS ———

    def get_state(self) -> Dict[str, Any]:
        """Immutable snapshot used by GUI, camera, game logic."""
        return {
            'mouse_pos': tuple(self.config['mouse']['pos']),
            'mouse_down': self.config['mouse']['buttons'].copy(),
            'mouse_pressed': self.config['mouse']['pressed'].copy(),
            'mouse_released': self.config['mouse']['released'].copy(),
            'keys': self.config['keys'].copy()
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