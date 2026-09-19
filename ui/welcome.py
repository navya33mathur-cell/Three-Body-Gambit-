"""
Welcome Screen modal dialog for Orbital Echo.
Renders on startup to introduce the three-body experiment concept.
"""

import pygame
from ui.manager import UIModal
from ui.widgets import UIButton

class WelcomeModal(UIModal):
    """Polished startup modal introducing Orbital Echo."""
    def __init__(self, screen_width: int, screen_height: int):
        super().__init__("ORBITAL ECHO", width=640, height=440)
        self.sw = screen_width
        self.sh = screen_height

        btn_w, btn_h = 220, 48
        btn_x = (screen_width - btn_w) // 2
        btn_y = (screen_height + self.height) // 2 - 70

        self.btn_enter = UIButton(
            rect=(btn_x, btn_y, btn_w, btn_h),
            text="ENTER EXPERIMENT",
            callback=self.close,
            bg_color=(50, 90, 150),
            hover_color=(70, 120, 200)
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.btn_enter.handle_event(event):
            return True
        return super().handle_event(event)

    def render(self, screen: pygame.Surface):
        # Semi-transparent dark screen backdrop
        backdrop = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        backdrop.fill((5, 10, 18, 210))
        screen.blit(backdrop, (0, 0))

        # Modal Window Panel
        x = (self.sw - self.width) // 2
        y = (self.sh - self.height) // 2

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 24, 38, 245), panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, (70, 110, 170, 220), panel.get_rect(), width=2, border_radius=12)

        # Typography
        f_title = pygame.font.Font(None, 32)
        f_subtitle = pygame.font.Font(None, 20)
        f_body = pygame.font.Font(None, 18)

        title_surf = f_title.render("ORBITAL ECHO", True, (240, 248, 255))
        sub_surf = f_subtitle.render("A THREE-BODY EXPERIMENT", True, (120, 180, 255))

        panel.blit(title_surf, ((self.width - title_surf.get_width()) // 2, 35))
        panel.blit(sub_surf, ((self.width - sub_surf.get_width()) // 2, 75))

        # Divider line
        pygame.draw.line(panel, (50, 80, 130), (50, 110), (self.width - 50, 110), width=1)

        # Body explanation text lines
        lines = [
            "You are running the same three-star system twice.",
            "",
            "UNIVERSE A is the original gravitational system.",
            "UNIVERSE B starts almost identical, but with a tiny perturbation.",
            "",
            "Observe how their orbits evolve and test how starting differences",
            "impact long-term gravitational trajectories."
        ]

        ly = 135
        for line in lines:
            if line:
                ts = f_body.render(line, True, (210, 225, 245))
                panel.blit(ts, ((self.width - ts.get_width()) // 2, ly))
            ly += 24

        screen.blit(panel, (x, y))

        # Render Button
        font_btn = pygame.font.Font(None, 20)
        self.btn_enter.render(screen, font_btn)
