"""
Scientific Audit modal dialog for Orbital Echo.
Evaluates physical conservation integrity and encounter timescale resolution safety (dt/tau <= 0.10).
"""

import pygame
import numpy as np
from ui.manager import UIModal
from ui.widgets import UIButton
from physics.dual_universe import DualUniverseSystem
from physics.diagnostics import ScientificDiagnostics

class ScientificAuditModal(UIModal):
    """Scientific Audit & Timestep Safety Verification Panel."""
    def __init__(self, screen_width: int, screen_height: int, dual_system: DualUniverseSystem, dt: float, e0: float, p0: np.ndarray, l0: float, com0: np.ndarray):
        super().__init__("SCIENTIFIC AUDIT", width=740, height=540)
        self.sw = screen_width
        self.sh = screen_height
        self.dual_system = dual_system
        self.dt = dt
        self.e0 = e0
        self.p0 = p0
        self.l0 = l0
        self.com0 = com0

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
        backdrop.fill((5, 10, 18, 190))
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
        f_warn = pygame.font.Font(None, 16)

        title_surf = f_title.render("SCIENTIFIC CONSERVATION & NUMERICAL RESOLUTION AUDIT", True, (240, 248, 255))
        panel.blit(title_surf, (24, 18))
        pygame.draw.line(panel, (50, 80, 130), (24, 48), (self.width - 24, 48), width=1)

        # Calculate current invariants & drift
        diag = ScientificDiagnostics.calculate_all(self.dual_system.universe_A, self.dt)
        ef = diag["total_energy"]
        e_drift = abs(ef - self.e0) / abs(self.e0) if abs(self.e0) > 1e-12 else 0.0

        pf = diag["linear_momentum"]
        p_drift = float(np.linalg.norm(pf - self.p0))

        lf = diag["angular_momentum"]
        l_drift = abs(lf - self.l0)

        comf = diag["centre_of_mass"]
        com_drift = float(np.linalg.norm(comf - self.com0))

        ratio = diag["dt_tau_ratio"]
        is_resolved = diag["is_resolved"]

        # Audit Sections
        panel.blit(f_sec.render("1. PHYSICAL CONSERVATION LAWS", True, (120, 190, 255)), (24, 60))

        audit_items = [
            ("Energy Conservation Drift |(E - E0)/E0|", f"{e_drift:.2e}", e_drift < 1e-3),
            ("Linear Momentum Conservation Drift |P - P0|", f"{p_drift:.2e}", p_drift < 1e-6),
            ("Angular Momentum Drift |Lz - Lz0|", f"{l_drift:.2e}", l_drift < 1e-6),
            ("Centre-of-Mass Motion Drift |Rcm - Rcm0|", f"{com_drift:.2e}", com_drift < 1e-6)
        ]

        cy = 88
        for label, val, passed in audit_items:
            ls = f_lbl.render(label, True, (200, 215, 235))
            vs = f_val.render(val, True, (120, 230, 255) if passed else (255, 100, 100))
            ps = f_warn.render("PASS" if passed else "WARN", True, (100, 240, 140) if passed else (255, 100, 100))
            panel.blit(ls, (24, cy))
            panel.blit(vs, (430, cy))
            panel.blit(ps, (650, cy))
            cy += 32

        # Section 2: Timestep Resolution Safety Ratio
        panel.blit(f_sec.render("2. TIMESTEP RESOLUTION SAFETY RATIO (S = dt / τ <= 0.10)", True, (120, 190, 255)), (24, 225))

        r_min = diag["min_separation"]
        tau = diag["encounter_timescale"]

        panel.blit(f_lbl.render("Minimum Pairwise Separation (rmin):", True, (200, 215, 235)), (24, 255))
        panel.blit(f_val.render(f"{r_min:.6f}", True, (255, 210, 120)), (320, 255))

        panel.blit(f_lbl.render("Closest Encounter Timescale (τ):", True, (200, 215, 235)), (24, 285))
        panel.blit(f_val.render(f"{tau:.6f}", True, (255, 210, 120)), (320, 285))

        panel.blit(f_lbl.render("Safety Ratio (S = dt / τ):", True, (200, 215, 235)), (24, 315))
        panel.blit(f_val.render(f"{ratio:.4f}", True, (120, 230, 255) if is_resolved else (255, 100, 100)), (320, 315))

        # Resolution Status Box
        status_box_y = 355
        box_color = (20, 50, 35, 220) if is_resolved else (60, 20, 20, 220)
        border_color = (60, 180, 100, 240) if is_resolved else (220, 70, 70, 240)

        pygame.draw.rect(panel, box_color, (24, status_box_y, self.width - 48, 85), border_radius=6)
        pygame.draw.rect(panel, border_color, (24, status_box_y, self.width - 48, 85), width=1, border_radius=6)

        status_txt = "RESOLUTION STATUS: RESOLVED" if is_resolved else "RESOLUTION STATUS: UNRESOLVED / NEEDS SMALLER TIMESTEP"
        status_surf = f_sec.render(status_txt, True, (100, 240, 140) if is_resolved else (255, 120, 120))
        panel.blit(status_surf, (36, status_box_y + 12))

        if is_resolved:
            expl_str = "The current timestep (dt) adequately resolves the closest encounter dynamics according to S <= 0.10."
        else:
            expl_str = "The current timestep may be too large relative to the closest encounter timescale."
        expl_surf = f_lbl.render(expl_str, True, (220, 230, 245))
        panel.blit(expl_surf, (36, status_box_y + 44))

        screen.blit(panel, (x, y))

        font_btn = pygame.font.Font(None, 18)
        self.btn_close.render(screen, font_btn)
