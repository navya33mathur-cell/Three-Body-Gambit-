"""
Controls & Shortcuts modal dialog for Orbital Echo.
Displays draggable keyboard shortcut reference panel.
"""

import pygame
from ui.manager import UIModal
from ui.widgets import UIButton

class ControlsModal(UIModal):
    """Draggable keyboard shortcuts and controls reference window."""
    def __init__(self, screen_width: int, screen_height: int):
        super().__init__("CONTROLS & SHORTCUTS", width=620, height=540)
        self.sw = screen_width
        self.sh = screen_height

        self.btn_close = UIButton(
            rect=((screen_width + self.width) // 2 - 110, (screen_height + self.height) // 2 - 50, 90, 34),
            text="CLOSE",
            callback=self.close,
            bg_color=(40, 60, 90),
            hover_color=(60, 90, 140)
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.btn_close.handle_event(event):
            return True
        return super().handle_event(event)

    def render(self, screen: pygame.Surface):
        backdrop = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        backdrop.fill((5, 10, 18, 180))
        screen.blit(backdrop, (0, 0))

        x = (self.sw - self.width) // 2
        y = (self.sh - self.height) // 2

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (16, 25, 40, 245), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (70, 110, 170, 220), panel.get_rect(), width=2, border_radius=10)

        f_title = pygame.font.Font(None, 24)
        f_key = pygame.font.Font(None, 18)
        f_desc = pygame.font.Font(None, 18)

        title_surf = f_title.render("CONTROLS & KEYBOARD SHORTCUTS", True, (240, 248, 255))
        panel.blit(title_surf, (24, 18))
        pygame.draw.line(panel, (50, 80, 130), (24, 48), (self.width - 24, 48), width=1)

        keymaps = [
            ("SPACE", "Pause / Resume simulation"),
            ("R", "Reset current experiment to t=0"),
            ("S", "Advance single simulation timestep while paused"),
            ("F", "Auto-frame camera center and scale"),
            ("T", "Toggle orbital trail paths"),
            ("V", "Toggle velocity vector arrows"),
            ("L", "Toggle body labels"),
            ("1 - 5", "Load Built-in Presets 1 to 5"),
            ("[ / ]", "Decrease / Increase timestep dt"),
            ("E", "Open Experiment Editor panel"),
            ("M", "Open Live Measurements panel"),
            ("A", "Open Scientific Audit panel"),
            ("H", "Open step-by-step physics guide for current preset"),
            ("TAB", "Open Controls & Shortcuts menu"),
            ("F5 / F9", "Save / Load experiment to JSON file"),
            ("ESC", "Close current modal / menu window")
        ]

        cy = 58
        for key, desc in keymaps:
            ks = f_key.render(f"{key:<10}", True, (255, 190, 100))
            ds = f_desc.render(desc, True, (220, 230, 245))
            panel.blit(ks, (28, cy))
            panel.blit(ds, (130, cy))
            cy += 25

        screen.blit(panel, (x, y))

        font_btn = pygame.font.Font(None, 18)
        self.btn_close.render(screen, font_btn)
