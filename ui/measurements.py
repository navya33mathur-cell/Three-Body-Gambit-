"""
Live Measurements Panel modal dialog for Orbital Echo.
Presents clean organized table of real-time physical quantities and conservation metrics.
"""

import pygame
import numpy as np
from ui.manager import UIModal
from ui.widgets import UIButton
from physics.dual_universe import DualUniverseSystem
from physics.diagnostics import ScientificDiagnostics

class MeasurementsModal(UIModal):
    """Live scientific measurements display panel."""
    def __init__(self, screen_width: int, screen_height: int, dual_system: DualUniverseSystem, dt: float):
        super().__init__("MEASUREMENTS PANEL", width=720, height=520)
        self.sw = screen_width
        self.sh = screen_height
        self.dual_system = dual_system
        self.dt = dt

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
        backdrop = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        backdrop.fill((5, 10, 18, 180))
        screen.blit(backdrop, (0, 0))

        x = (self.sw - self.width) // 2
        y = (self.sh - self.height) // 2

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (16, 25, 40, 248), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (70, 110, 170, 230), panel.get_rect(), width=2, border_radius=10)

        f_title = pygame.font.Font(None, 24)
        f_sec = pygame.font.Font(None, 18)
        f_lbl = pygame.font.Font(None, 16)
        f_val = pygame.font.Font(None, 16)

        title_surf = f_title.render("LIVE SCIENTIFIC MEASUREMENTS PANEL", True, (240, 248, 255))
        panel.blit(title_surf, (24, 18))
        pygame.draw.line(panel, (50, 80, 130), (24, 48), (self.width - 24, 48), width=1)

        # Calculate live diagnostics
        diag = ScientificDiagnostics.calculate_all(self.dual_system.universe_A, self.dt)
        div = self.dual_system.get_divergence()
        ftle = self.dual_system.get_ftle()

        col1_data = [
            ("Simulation Time (t)", f"{self.dual_system.universe_A.time:.4f}"),
            ("Timestep (dt)", f"{self.dt:.6f}"),
            ("G Constant", f"{self.dual_system.G:.4f}"),
            ("Kinetic Energy (Ek)", f"{diag['kinetic_energy']:.6f}"),
            ("Potential Energy (Ep)", f"{diag['potential_energy']:.6f}"),
            ("Total Energy (E)", f"{diag['total_energy']:.6f}"),
            ("Angular Momentum (Lz)", f"{diag['angular_momentum']:.6f}")
        ]

        col2_data = [
            ("Linear Momentum P", f"[{diag['linear_momentum'][0]:.4f}, {diag['linear_momentum'][1]:.4f}]"),
            ("Centre of Mass Rcm", f"[{diag['centre_of_mass'][0]:.4f}, {diag['centre_of_mass'][1]:.4f}]"),
            ("Min Separation (rmin)", f"{diag['min_separation']:.6f}"),
            ("Encounter Timescale τ", f"{diag['encounter_timescale']:.6f}"),
            ("Timestep Safety Ratio S", f"{diag['dt_tau_ratio']:.4f}"),
            ("Divergence D(t)", f"{div:.6f}"),
            ("FTLE Rate λ(t)", f"{ftle:.4f} t^-1")
        ]

        # Render Left Column
        panel.blit(f_sec.render("ENERGY & DYNAMICS", True, (120, 190, 255)), (24, 60))
        cy = 90
        for label, val in col1_data:
            ls = f_lbl.render(label, True, (200, 215, 235))
            vs = f_val.render(val, True, (255, 210, 120))
            panel.blit(ls, (24, cy))
            panel.blit(vs, (180, cy))
            cy += 36

        # Render Right Column
        panel.blit(f_sec.render("GEOMETRY & DIVERGENCE", True, (120, 190, 255)), (370, 60))
        cy = 90
        for label, val in col2_data:
            ls = f_lbl.render(label, True, (200, 215, 235))
            vs = f_val.render(val, True, (120, 230, 255))
            panel.blit(ls, (370, cy))
            panel.blit(vs, (535, cy))
            cy += 36

        screen.blit(panel, (x, y))

        font_btn = pygame.font.Font(None, 18)
        self.btn_close.render(screen, font_btn)
