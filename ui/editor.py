"""
Experiment Editor modal dialog for Orbital Echo.
Allows live interactive customization of gravitational constant G, timestep dt, perturbation settings,
and body initial conditions (positions, velocities, masses, colors).
"""

import pygame
import numpy as np
from typing import Callable, List, Dict, Any
from ui.manager import UIModal
from ui.widgets import UIButton, UINumberInput, UIDropdown
from physics.nbody import Body
from physics.dual_universe import DualUniverseSystem, PerturbationConfig

class ExperimentEditorModal(UIModal):
    """
    Compact graphical panel for configuring three-body experiments.
    Does not fill screen; features APPLY, CANCEL, and CLOSE buttons.
    """
    def __init__(self, screen_width: int, screen_height: int, dual_system: DualUniverseSystem, on_apply_callback: Callable):
        super().__init__("EXPERIMENT EDITOR", width=820, height=580)
        self.sw = screen_width
        self.sh = screen_height
        self.dual_system = dual_system
        self.on_apply_callback = on_apply_callback

        # Working state copies
        self.edit_G = dual_system.G
        self.edit_dt = 0.005
        self.edit_pert = PerturbationConfig(
            body_index=dual_system.perturbation.body_index,
            target=dual_system.perturbation.target,
            magnitude=dual_system.perturbation.magnitude
        )
        self.edit_bodies = [b.copy() for b in dual_system.base_bodies]

        self._init_controls()

    def _init_controls(self):
        """Builds all interactive input widgets."""
        x = (self.sw - self.width) // 2
        y = (self.sh - self.height) // 2

        # 1. Action Buttons
        self.btn_apply = UIButton((x + self.width - 320, y + self.height - 50, 95, 36), "APPLY", self.apply_changes, bg_color=(30, 110, 60), hover_color=(45, 150, 80))
        self.btn_cancel = UIButton((x + self.width - 215, y + self.height - 50, 95, 36), "CANCEL", self.close, bg_color=(110, 40, 40), hover_color=(150, 60, 60))
        self.btn_close = UIButton((x + self.width - 110, y + self.height - 50, 90, 36), "CLOSE", self.close, bg_color=(40, 60, 90), hover_color=(60, 90, 140))

        # 2. General Inputs
        self.input_G = UINumberInput((x + 130, y + 65, 90, 26), self.edit_G, lambda v: setattr(self, 'edit_G', v))
        self.input_dt = UINumberInput((x + 320, y + 65, 90, 26), self.edit_dt, lambda v: setattr(self, 'edit_dt', v))

        # 3. Perturbation Inputs
        self.input_pert_mag = UINumberInput((x + 160, y + 135, 100, 26), self.edit_pert.magnitude, lambda v: setattr(self.edit_pert, 'magnitude', v))
        self.drop_pert_body = UIDropdown(
            (x + 390, y + 135, 110, 26),
            ["Body 1", "Body 2", "Body 3"],
            selected_index=self.edit_pert.body_index,
            callback=lambda idx, val: setattr(self.edit_pert, 'body_index', idx)
        )
        targets = ["pos_x", "pos_y", "vel_x", "vel_y"]
        sel_t = targets.index(self.edit_pert.target) if self.edit_pert.target in targets else 0
        self.drop_pert_coord = UIDropdown(
            (x + 640, y + 135, 110, 26),
            ["X Pos", "Y Pos", "X Vel", "Y Vel"],
            selected_index=sel_t,
            callback=lambda idx, val: setattr(self.edit_pert, 'target', targets[idx])
        )

        # 4. Body Initial Conditions Inputs (3 Bodies x 5 Fields)
        self.body_inputs: List[Dict[str, UINumberInput]] = []
        cy = y + 215
        for i in range(min(3, len(self.edit_bodies))):
            b = self.edit_bodies[i]
            inputs = {
                "mass": UINumberInput((x + 130, cy, 80, 26), b.mass, lambda v, body=b: setattr(body, 'mass', v)),
                "pos_x": UINumberInput((x + 290, cy, 80, 26), b.position[0], lambda v, body=b: body.position.__setitem__(0, v)),
                "pos_y": UINumberInput((x + 420, cy, 80, 26), b.position[1], lambda v, body=b: body.position.__setitem__(1, v)),
                "vel_x": UINumberInput((x + 550, cy, 80, 26), b.velocity[0], lambda v, body=b: body.velocity.__setitem__(0, v)),
                "vel_y": UINumberInput((x + 680, cy, 80, 26), b.velocity[1], lambda v, body=b: body.velocity.__setitem__(1, v))
            }
            self.body_inputs.append(inputs)
            cy += 85

    def apply_changes(self):
        """Applies configured edits to simulation."""
        # Confirm open number field inputs
        self.input_G.confirm()
        self.input_dt.confirm()
        self.input_pert_mag.confirm()
        for b_dict in self.body_inputs:
            for inp in b_dict.values():
                inp.confirm()

        self.on_apply_callback(self.edit_bodies, self.edit_G, self.edit_pert, self.edit_dt)
        self.close()

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Check action buttons
        if self.btn_apply.handle_event(event) or self.btn_cancel.handle_event(event) or self.btn_close.handle_event(event):
            return True

        # Dropdowns
        if self.drop_pert_body.handle_event(event) or self.drop_pert_coord.handle_event(event):
            return True

        # Number inputs
        if self.input_G.handle_event(event) or self.input_dt.handle_event(event) or self.input_pert_mag.handle_event(event):
            return True

        for b_dict in self.body_inputs:
            for inp in b_dict.values():
                if inp.handle_event(event):
                    return True

        return super().handle_event(event)

    def render(self, screen: pygame.Surface):
        backdrop = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        backdrop.fill((5, 10, 18, 190))
        screen.blit(backdrop, (0, 0))

        x = (self.sw - self.width) // 2
        y = (self.sh - self.height) // 2

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (16, 24, 38, 248), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (70, 110, 170, 230), panel.get_rect(), width=2, border_radius=10)

        f_title = pygame.font.Font(None, 24)
        f_sec = pygame.font.Font(None, 18)
        f_lbl = pygame.font.Font(None, 16)

        title_surf = f_title.render("EXPERIMENT CONFIGURATION EDITOR", True, (240, 248, 255))
        panel.blit(title_surf, (24, 16))
        pygame.draw.line(panel, (50, 80, 130), (24, 46), (self.width - 24, 46), width=1)

        # Section 1: General Parameters
        g_sec = f_sec.render("GENERAL PARAMETERS", True, (120, 190, 255))
        panel.blit(g_sec, (24, 55))
        panel.blit(f_lbl.render("G Constant:", True, (200, 215, 235)), (24, 86))
        panel.blit(f_lbl.render("Timestep dt:", True, (200, 215, 235)), (230, 86))

        # Section 2: Perturbation Parameters
        p_sec = f_sec.render("PERTURBATION CONFIGURATION", True, (120, 190, 255))
        panel.blit(p_sec, (24, 125))
        panel.blit(f_lbl.render("Magnitude δ:", True, (200, 215, 235)), (24, 156))
        panel.blit(f_lbl.render("Target Body:", True, (200, 215, 235)), (285, 156))
        panel.blit(f_lbl.render("Coordinate:", True, (200, 215, 235)), (525, 156))

        # Section 3: Body Initial Conditions
        b_sec = f_sec.render("BODY INITIAL CONDITIONS", True, (120, 190, 255))
        panel.blit(b_sec, (24, 200))

        cy = 235
        for i in range(min(3, len(self.edit_bodies))):
            b_title = f_sec.render(f"BODY {i+1}: {self.edit_bodies[i].name}", True, (255, 200, 120))
            panel.blit(b_title, (24, cy))
            panel.blit(f_lbl.render("Mass:", True, (200, 215, 235)), (80, cy + 26))
            panel.blit(f_lbl.render("Pos X:", True, (200, 215, 235)), (235, cy + 26))
            panel.blit(f_lbl.render("Pos Y:", True, (200, 215, 235)), (375, cy + 26))
            panel.blit(f_lbl.render("Vel X:", True, (200, 215, 235)), (505, cy + 26))
            panel.blit(f_lbl.render("Vel Y:", True, (200, 215, 235)), (635, cy + 26))
            cy += 85

        screen.blit(panel, (x, y))

        # Render Widgets
        font_btn = pygame.font.Font(None, 18)
        font_inp = pygame.font.Font(None, 16)

        self.input_G.render(screen, font_inp)
        self.input_dt.render(screen, font_inp)
        self.input_pert_mag.render(screen, font_inp)

        for b_dict in self.body_inputs:
            for inp in b_dict.values():
                inp.render(screen, font_inp)

        self.drop_pert_body.render(screen, font_inp)
        self.drop_pert_coord.render(screen, font_inp)

        self.btn_apply.render(screen, font_btn)
        self.btn_cancel.render(screen, font_btn)
        self.btn_close.render(screen, font_btn)
