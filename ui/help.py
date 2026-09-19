"""
Beginner Guide modal dialog for Orbital Echo.
Explains gravity, three-body dynamics, dual universes, perturbations, and divergence in accessible 5th-grade English.
"""

import pygame
from ui.manager import UIModal
from ui.widgets import UIButton

class BeginnerGuideModal(UIModal):
    """Beginner-friendly educational guide."""
    def __init__(self, screen_width: int, screen_height: int):
        super().__init__("BEGINNER GUIDE", width=720, height=520)
        self.sw = screen_width
        self.sh = screen_height

        self.btn_close = UIButton(
            rect=((screen_width + self.width) // 2 - 120, (screen_height + self.height) // 2 - 50, 100, 36),
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
        # Backdrop
        backdrop = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        backdrop.fill((5, 10, 18, 190))
        screen.blit(backdrop, (0, 0))

        # Panel
        x = (self.sw - self.width) // 2
        y = (self.sh - self.height) // 2

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (16, 25, 40, 245), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (60, 100, 160, 220), panel.get_rect(), width=2, border_radius=10)

        # Title
        f_title = pygame.font.Font(None, 24)
        f_header = pygame.font.Font(None, 18)
        f_body = pygame.font.Font(None, 17)

        title_surf = f_title.render("BEGINNER GUIDE — THREE-BODY PHYSICS", True, (240, 248, 255))
        panel.blit(title_surf, (24, 20))
        pygame.draw.line(panel, (50, 80, 130), (24, 52), (self.width - 24, 52), width=1)

        sections = [
            ("WHAT IS GRAVITY?", "Every star pulls on every other star in space with an invisible gravitational force."),
            ("WHAT IS A THREE-BODY SYSTEM?", "Three stars pulling on each other all at the exact same time."),
            ("WHAT IS UNIVERSE A?", "The original experiment running with baseline starting positions."),
            ("WHAT IS UNIVERSE B?", "The exact same experiment, but with one tiny starting tweak."),
            ("WHAT IS THE PERTURBATION?", "A tiny nudge to one star's position or velocity before the simulation begins."),
            ("WHAT IS D(t)?", "A measurement of how far apart the paths of Universe A and Universe B become over time."),
            ("WHY DOES THIS MATTER?", "In some three-body setups, tiny initial differences can grow over time into very different paths.")
        ]

        cur_y = 65
        for heading, text in sections:
            hs = f_header.render(heading, True, (120, 190, 255))
            bs = f_body.render(text, True, (215, 225, 240))
            panel.blit(hs, (24, cur_y))
            panel.blit(bs, (24, cur_y + 18))
            cur_y += 58

        screen.blit(panel, (x, y))

        font_btn = pygame.font.Font(None, 18)
        self.btn_close.render(screen, font_btn)
