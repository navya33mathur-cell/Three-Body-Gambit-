"""THREE-BODY GAMBIT — Scientific three-body gravity experiment."""

from __future__ import annotations

import json
import os

import numpy as np
import pygame

from physics.nbody import Body
from physics.dual_universe import DualUniverseSystem, PerturbationConfig
from physics.presets import get_builtin_presets, load_preset_bodies, load_preset_perturbation
from physics.diagnostics import ScientificDiagnostics

from rendering.camera import Camera
from rendering.background import DeepSpaceBackground
from rendering.trails import TrailBuffer
from rendering.scientific import ScientificRenderer
from guided_outcomes import get_guided_outcomes

from ui.manager import UIManager
from ui.controls import ControlsModal
from ui.editor import ExperimentEditorModal
from ui.measurements import MeasurementsModal
from ui.audit import ScientificAuditModal
from input.controller import InputController


class OrbitalEchoApp:
    """Application controller. The project has one presentation: Scientific Mode."""

    def __init__(self, width: int = 1600, height: int = 900, headless: bool = False):
        self.width = width
        self.height = height
        self.headless = headless
        self.is_running = True
        self.is_paused = False

        self.presets = get_builtin_presets()
        self.current_preset_idx = 0
        self.guided_outcomes = get_guided_outcomes()
        self.active_guided_outcome = None

        p0 = self.presets[0]
        bodies = load_preset_bodies(p0)
        pert = load_preset_perturbation(p0)
        self.dt = float(p0["dt"])
        self.dual_system = DualUniverseSystem(bodies, G=p0["G"], perturbation=pert)
        self._record_baseline_invariants()

        self.show_trails = True
        self.show_labels = True
        self.show_vectors = False

        pygame.init()
        if not headless:
            pygame.display.set_caption("THREE-BODY GAMBIT — Scientific Gravity Experiment")
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE | pygame.DOUBLEBUF)
            self.clock = pygame.time.Clock()
        else:
            self.screen = pygame.Surface((width, height))
            self.clock = None

        self.background = DeepSpaceBackground(width, height)
        self.camera = Camera(width, height)
        self.trail_buffer = TrailBuffer(max_length=800)
        self.scientific_renderer = ScientificRenderer(self.background)
        self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())

        self.ui_manager = UIManager()
        self.input_controller = InputController(self)

    def _record_baseline_invariants(self):
        sys = self.dual_system.universe_A
        self.e0 = ScientificDiagnostics.calculate_total_energy(sys)
        self.p0 = ScientificDiagnostics.calculate_linear_momentum(sys)
        self.l0 = ScientificDiagnostics.calculate_angular_momentum(sys)
        self.com0 = ScientificDiagnostics.calculate_centre_of_mass(sys)

    def on_resize(self, width: int, height: int):
        self.width, self.height = width, height
        if not self.headless:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.background.resize(width, height)
        self.camera.resize(width, height)

    def reset_experiment(self):
        self.dual_system.reset()
        self.trail_buffer.clear()
        self._record_baseline_invariants()
        self.scientific_renderer.help_step = 0
        self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())

    def load_preset(self, index: int):
        if 0 <= index < len(self.presets):
            self.current_preset_idx = index
            self.active_guided_outcome = None
            p = self.presets[index]
            bodies = load_preset_bodies(p)
            pert = load_preset_perturbation(p)
            self.dt = float(p["dt"])
            self.dual_system.set_config(bodies, G=p["G"], perturbation=pert)
            self.trail_buffer.clear()
            self._record_baseline_invariants()
            self.scientific_renderer.help_step = 0
            self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())

    def toggle_help(self):
        self.scientific_renderer.toggle_help()

    def update_initial_positions(self, positions: np.ndarray):
        """Set manual starting positions for Universe B only. Universe A stays at the preset baseline."""
        positions = np.asarray(positions, dtype=np.float64)
        if positions.shape != (3, 2) or not np.all(np.isfinite(positions)):
            self.scientific_renderer.position_message = "Enter finite x/y values for all three bodies."
            self.scientific_renderer.position_message_until = pygame.time.get_ticks() + 3000
            return

        # Reject exact/near-exact overlaps because the unsoftened point-mass force is singular.
        for i in range(3):
            for j in range(i + 1, 3):
                if float(np.linalg.norm(positions[i] - positions[j])) < 1e-6:
                    self.scientific_renderer.position_message = "Two Universe B bodies are too close; choose a larger separation."
                    self.scientific_renderer.position_message_until = pygame.time.get_ticks() + 3000
                    self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())
                    return

        self.dual_system.set_custom_B_positions(positions)
        self.active_guided_outcome = None
        self.trail_buffer.clear()
        self._record_baseline_invariants()
        self.is_paused = False
        self.scientific_renderer.help_step = 0
        self.scientific_renderer.position_message = "Universe B starting positions updated. Universe A remains at the preset baseline."
        self.scientific_renderer.position_message_until = pygame.time.get_ticks() + 3000

    def load_guided_outcome(self, guided_index: int):
        """Load a representative custom-position experiment and reset the run."""
        if not (0 <= guided_index < len(self.guided_outcomes)):
            return
        guided = self.guided_outcomes[guided_index]
        self.current_preset_idx = int(guided["preset_index"])
        p = self.presets[self.current_preset_idx]
        bodies = load_preset_bodies(p)
        pert = load_preset_perturbation(p)
        self.dt = float(p["dt"])
        self.dual_system.set_config(bodies, G=p["G"], perturbation=pert)
        self.dual_system.set_custom_B_positions(guided["positions"])
        self.active_guided_outcome = guided["id"]
        self.trail_buffer.clear()
        self._record_baseline_invariants()
        self.is_paused = False
        self.scientific_renderer.help_step = 0
        self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())
        self.scientific_renderer.position_message = f"Guided outcome loaded: {guided['short']}"
        self.scientific_renderer.position_message_until = pygame.time.get_ticks() + 3500

    def reset_initial_positions(self):
        """Restore the currently selected preset's original starting positions."""
        self.active_guided_outcome = None
        p = self.presets[self.current_preset_idx]
        bodies = load_preset_bodies(p)
        pert = load_preset_perturbation(p)
        self.dual_system.set_config(bodies, G=p["G"], perturbation=pert)
        self.dt = float(p["dt"])
        self.trail_buffer.clear()
        self._record_baseline_invariants()
        self.is_paused = False
        self.scientific_renderer.help_step = 0
        self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())

    def auto_frame_camera(self):
        positions = np.vstack((
            self.dual_system.universe_A.get_positions(),
            self.dual_system.universe_B.get_positions(),
        ))
        self.camera.update_auto_frame(positions)

    def step_single_frame(self):
        try:
            self.dual_system.step(self.dt)
            self.trail_buffer.update(
                self.dual_system.universe_A.get_positions(),
                self.dual_system.universe_B.get_positions(),
            )
        except ZeroDivisionError:
            self.is_paused = True

    def adjust_dt(self, factor: float):
        self.dt = float(np.clip(self.dt * factor, 0.0001, 0.05))

    # --- Existing scientific utility modals ---
    def open_controls_modal(self):
        self.ui_manager.open_modal(ControlsModal(self.width, self.height))

    def open_editor_modal(self):
        def on_apply(bodies, G, pert, dt):
            self.dt = float(dt)
            self.dual_system.set_config(bodies, G, pert)
            self.trail_buffer.clear()
            self._record_baseline_invariants()
            self.scientific_renderer.help_step = 0

        self.ui_manager.open_modal(
            ExperimentEditorModal(self.width, self.height, self.dual_system, on_apply)
        )

    def open_measurements_modal(self):
        self.ui_manager.open_modal(
            MeasurementsModal(self.width, self.height, self.dual_system, self.dt)
        )

    def open_audit_modal(self):
        self.ui_manager.open_modal(
            ScientificAuditModal(
                self.width, self.height, self.dual_system, self.dt,
                self.e0, self.p0, self.l0, self.com0
            )
        )

    # --- Save / load ---
    def save_experiment_json(self, filepath: str = "custom_experiment.json"):
        data = {
            "name": f"Saved Experiment (t={self.dual_system.universe_A.time:.2f})",
            "G": self.dual_system.G,
            "dt": self.dt,
            "duration": 20.0,
            "perturbation": self.dual_system.perturbation.to_dict(),
            "bodies": [b.to_dict() for b in self.dual_system.base_bodies],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_experiment_json(self, filepath: str = "custom_experiment.json"):
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        bodies = [Body.from_dict(bd) for bd in data["bodies"]]
        pert = PerturbationConfig.from_dict(data["perturbation"])
        self.dt = float(data.get("dt", 0.005))
        self.dual_system.set_config(bodies, G=data.get("G", 1.0), perturbation=pert)
        self.trail_buffer.clear()
        self._record_baseline_invariants()
        self.scientific_renderer.help_step = 0
        self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())

    def run(self):
        while self.is_running:
            frame_dt = self.clock.tick(60) / 1000.0 if self.clock else 0.016
            self.input_controller.process_events()

            # Apply click-driven scientific controls after the event queue has been consumed.
            action = self.scientific_renderer.consume_clicked_action()
            if action is not None:
                kind, value = action
                if kind == "preset":
                    self.load_preset(int(value))
                elif kind == "guided_outcome":
                    self.load_guided_outcome(int(value))
                elif kind == "reset_positions":
                    self.reset_initial_positions()
                elif kind == "body_selected":
                    self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())
            position_update = self.scientific_renderer.consume_position_update()
            if position_update is not None:
                self.update_initial_positions(position_update)
                self.scientific_renderer.sync_position_fields(self.dual_system.get_initial_B_positions())

            # Keep modal interaction responsive while the simulation is paused by a modal.
            if not self.is_paused and not self.ui_manager.has_active_modal():
                self.dual_system.step(self.dt)
                self.trail_buffer.update(
                    self.dual_system.universe_A.get_positions(),
                    self.dual_system.universe_B.get_positions(),
                )

            self.ui_manager.update(frame_dt)

            preset = self.presets[self.current_preset_idx]
            self.scientific_renderer.render(
                self.screen,
                self.dual_system,
                self.camera,
                self.trail_buffer,
                show_trails=self.show_trails,
                show_labels=self.show_labels,
                show_vectors=self.show_vectors,
                preset_name=preset["name"],
                preset_description=preset["description"],
                dt=self.dt,
                e0=self.e0,
                p0=self.p0,
                l0=self.l0,
                com0=self.com0,
                current_preset_idx=self.current_preset_idx,
                active_guided_outcome=self.active_guided_outcome,
            )

            self.ui_manager.render(self.screen)
            if not self.headless:
                pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    OrbitalEchoApp().run()
