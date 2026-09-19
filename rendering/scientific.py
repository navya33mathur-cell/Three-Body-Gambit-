"""Scientific presentation for THREE-BODY GAMBIT.

One non-cinematic interface: the simulation, scientific telemetry, presets,
and a simple step-by-step explanation are visible together.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np
import pygame

from physics.dual_universe import DualUniverseSystem
from physics.diagnostics import ScientificDiagnostics
from rendering.camera import Camera
from rendering.trails import TrailBuffer, TrailRenderer


class ScientificRenderer:
    BG = (8, 14, 25)
    GRID = (25, 35, 52)
    GRID_MAJOR = (32, 44, 64)
    PANEL = (15, 23, 37)
    CARD = (12, 21, 34)
    PANEL_BORDER = (45, 64, 91)
    WHITE = (235, 242, 250)
    MUTED = (150, 165, 185)
    CYAN = (45, 190, 245)
    BLUE = (35, 175, 245)
    PINK = (245, 70, 125)
    GOLD = (255, 190, 45)
    GREEN = (0, 215, 120)
    ORANGE = (255, 170, 70)
    RED = (255, 95, 95)
    BODY_COLORS = [BLUE, PINK, GOLD]

    def __init__(self, background=None):
        self.help_open = False
        self.help_step = 0
        self._last_help_rects: Dict[str, pygame.Rect] = {}
        self._last_ui_rects: Dict[str, object] = {}
        self.selected_body = 0
        self.position_field = None
        self.position_text = [
            {"x": "0.000000", "y": "0.000000"},
            {"x": "0.000000", "y": "0.000000"},
            {"x": "0.000000", "y": "0.000000"},
        ]
        self.position_message = ""
        self.position_message_until = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(
        self,
        screen: pygame.Surface,
        dual_system: DualUniverseSystem,
        camera: Camera,
        trail_buffer: TrailBuffer,
        show_trails: bool = True,
        show_labels: bool = True,
        show_vectors: bool = False,
        preset_name: str = "Three-Body Experiment",
        preset_description: str = "",
        dt: float = 0.001,
        e0: float | None = None,
        p0: np.ndarray | None = None,
        l0: float | None = None,
        com0: np.ndarray | None = None,
        current_preset_idx: int = 0,
        active_guided_outcome: str | None = None,
    ) -> None:
        width, height = screen.get_size()
        panel_width = max(430, min(500, int(width * 0.31)))
        viewport_width = max(600, width - panel_width)

        screen.fill(self.BG)
        self._draw_grid(screen, viewport_width, height)
        self._draw_panel(screen, viewport_width, height, panel_width)

        pos_a = dual_system.universe_A.get_positions()
        pos_b = dual_system.universe_B.get_positions()
        all_positions = np.vstack((pos_a, pos_b))

        camera.resize(viewport_width, height)
        camera.update_auto_frame(all_positions)

        if show_trails:
            TrailRenderer.render_scientific(
                screen, trail_buffer, camera, self.BODY_COLORS
            )

        self._render_bodies(screen, dual_system, camera, show_labels, show_vectors)
        self._render_header(screen, preset_name, preset_description)
        self._render_telemetry(screen, panel_width, dual_system, dt, e0, p0)
        self._render_preset_and_position_controls(screen, dual_system, viewport_width, current_preset_idx, active_guided_outcome)
        if self.help_open:
            self._render_help(screen, panel_width, dual_system, dt, preset_name, active_guided_outcome)

        if self.position_message and pygame.time.get_ticks() < self.position_message_until:
            msg_font = pygame.font.Font(None, 17)
            surf = msg_font.render(self.position_message, True, self.WHITE)
            screen.blit(surf, (22, height - 28))

    def toggle_help(self) -> None:
        self.help_open = not self.help_open
        self.help_step = 0
        self._last_help_rects.clear()

    def handle_event(self, event: pygame.event.Event, dual_system=None) -> bool:
        """Handle scientific-interface controls, including all three B-position rows."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            for i in range(5):
                rect = self._last_ui_rects.get(f"preset_{i}")
                if isinstance(rect, pygame.Rect) and rect.collidepoint(pos):
                    self._last_ui_rects["preset_clicked"] = i
                    return True

            for i in range(3):
                rect = self._last_ui_rects.get(f"field_{i}_x")
                if isinstance(rect, pygame.Rect) and rect.collidepoint(pos):
                    self.position_field = (i, "x")
                    return True
                rect = self._last_ui_rects.get(f"field_{i}_y")
                if isinstance(rect, pygame.Rect) and rect.collidepoint(pos):
                    self.position_field = (i, "y")
                    return True

            for i in range(5):
                guided_rect = self._last_ui_rects.get(f"guided_{i}")
                if isinstance(guided_rect, pygame.Rect) and guided_rect.collidepoint(pos):
                    self._last_ui_rects["guided_clicked"] = i
                    return True

            random_rect = self._last_ui_rects.get("random_positions")
            if isinstance(random_rect, pygame.Rect) and random_rect.collidepoint(pos):
                self._randomize_positions(dual_system)
                return True

            update_rect = self._last_ui_rects.get("update_positions")
            if isinstance(update_rect, pygame.Rect) and update_rect.collidepoint(pos):
                self._apply_all_positions()
                return True

            reset_rect = self._last_ui_rects.get("reset_positions")
            if isinstance(reset_rect, pygame.Rect) and reset_rect.collidepoint(pos):
                self._last_ui_rects["reset_positions_clicked"] = True
                return True

            if self.help_open:
                if self._last_help_rects.get("next", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                    self.help_step += 1
                    return True
                if self._last_help_rects.get("previous", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                    self.help_step = max(0, self.help_step - 1)
                    return True
                if self._last_help_rects.get("close", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                    self.help_open = False
                    self.help_step = 0
                    return True

        if event.type == pygame.KEYDOWN and self.position_field is not None:
            body_index, field = self.position_field
            if event.key == pygame.K_RETURN:
                self._apply_all_positions()
                return True
            if event.key == pygame.K_ESCAPE:
                self.position_field = None
                return True
            if event.key == pygame.K_BACKSPACE:
                self.position_text[body_index][field] = self.position_text[body_index][field][:-1]
                return True
            if event.unicode and (event.unicode.isdigit() or event.unicode in ".-+eE"):
                self.position_text[body_index][field] += event.unicode
                return True

        return False

    def consume_clicked_action(self) -> Tuple[str, object] | None:
        if "preset_clicked" in self._last_ui_rects:
            return "preset", self._last_ui_rects.pop("preset_clicked")
        if self._last_ui_rects.pop("reset_positions_clicked", False):
            return "reset_positions", None
        if "guided_clicked" in self._last_ui_rects:
            return "guided_outcome", self._last_ui_rects.pop("guided_clicked")
        return None

    def sync_position_fields(self, positions) -> None:
        positions = np.asarray(positions, dtype=float)
        if positions.shape != (3, 2):
            return
        self.position_text = [
            {"x": f"{positions[i, 0]:.6f}", "y": f"{positions[i, 1]:.6f}"}
            for i in range(3)
        ]

    def _apply_all_positions(self):
        try:
            positions = np.array([
                [float(row["x"]), float(row["y"])] for row in self.position_text
            ], dtype=float)
            if not np.all(np.isfinite(positions)):
                raise ValueError
            self._last_ui_rects["position_update"] = positions
            self.position_field = None
        except ValueError:
            self.position_message = "Enter valid finite numbers for all three bodies."
            self.position_message_until = pygame.time.get_ticks() + 2500

    def consume_position_update(self):
        return self._last_ui_rects.pop("position_update", None)

    # ------------------------------------------------------------------
    # Main viewport
    # ------------------------------------------------------------------

    def _draw_grid(self, screen, width, height):
        for x in range(0, width, 125):
            pygame.draw.line(screen, self.GRID, (x, 0), (x, height), 1)
        for y in range(0, height, 115):
            pygame.draw.line(screen, self.GRID, (0, y), (width, y), 1)
        pygame.draw.line(screen, self.GRID_MAJOR, (width // 2, 0), (width // 2, height), 1)
        pygame.draw.line(screen, self.GRID_MAJOR, (0, height // 2), (width, height // 2), 1)

    def _draw_panel(self, screen, viewport_width, height, panel_width):
        x = viewport_width
        pygame.draw.rect(screen, self.PANEL, (x, 0, panel_width, height))
        pygame.draw.line(screen, self.PANEL_BORDER, (x, 0), (x, height), 2)

    def _render_header(self, screen, name, description):
        title = pygame.font.Font(None, 32)
        body = pygame.font.Font(None, 19)
        screen.blit(title.render(name, True, self.WHITE), (18, 16))
        if description:
            screen.blit(body.render(description, True, self.MUTED), (18, 48))

    def _render_bodies(self, screen, dual_system, camera, show_labels, show_vectors):
        label_font = pygame.font.Font(None, 18)
        bodies_a = dual_system.universe_A.bodies
        bodies_b = dual_system.universe_B.bodies

        for i, body in enumerate(bodies_a):
            sp = camera.world_to_screen(body.position)
            color = self.BODY_COLORS[i]
            pygame.draw.circle(screen, color, sp, 10)
            pygame.draw.circle(screen, self.WHITE, sp, 10, width=1)
            if show_labels:
                self._draw_label(screen, (sp[0] + 13, sp[1] - 12), f"A{i + 1}", color, label_font)
            if show_vectors:
                self._draw_velocity_vector(screen, sp, body.velocity, camera.current_scale, color)

        for i, body in enumerate(bodies_b):
            sp = camera.world_to_screen(body.position)
            color = self.BODY_COLORS[i]
            pygame.draw.circle(screen, color, sp, 12, width=2)
            pygame.draw.circle(screen, self.WHITE, sp, 2)
            if show_labels:
                self._draw_label(screen, (sp[0] + 13, sp[1] + 6), f"B{i + 1}", color, label_font)
            if show_vectors:
                self._draw_velocity_vector(screen, sp, body.velocity, camera.current_scale, color)

    def _draw_velocity_vector(self, screen, start, velocity, scale, color):
        magnitude = float(np.linalg.norm(velocity))
        if magnitude < 1e-8:
            return
        length = min(80, max(14, magnitude * scale * 0.22))
        direction = velocity / magnitude
        end = (int(start[0] + direction[0] * length), int(start[1] - direction[1] * length))
        pygame.draw.line(screen, color, start, end, 2)

    def _draw_label(self, screen, pos, text, color, font):
        shadow = font.render(text, True, (3, 6, 11))
        screen.blit(shadow, (pos[0] + 1, pos[1] + 1))
        screen.blit(font.render(text, True, color), pos)

    # ------------------------------------------------------------------
    # Presets + custom initial position controls
    # ------------------------------------------------------------------

    def _render_preset_and_position_controls(self, screen, dual_system, viewport_width, current_preset_idx, active_guided_outcome=None):
        # Presets stay in the upper-left simulation area. Custom positions live in
        # the right sidebar above the divergence graph so they never cover the orbit view.
        self._last_ui_rects = {
            k: v for k, v in self._last_ui_rects.items()
            if k in ("preset_clicked", "reset_positions_clicked")
        }

        x0, y0 = 18, 82
        preset_w = 300
        card_h = 145
        font_title = pygame.font.Font(None, 20)
        font_small = pygame.font.Font(None, 14)
        font = pygame.font.Font(None, 17)

        pygame.draw.rect(screen, self.CARD, (x0, y0, preset_w, card_h), border_radius=8)
        pygame.draw.rect(screen, self.PANEL_BORDER, (x0, y0, preset_w, card_h), width=1, border_radius=8)
        self._text(screen, "PRESETS", x0 + 14, y0 + 12, font_title, self.CYAN)
        self._text(screen, "1–5", x0 + 83, y0 + 14, font_small, self.MUTED)
        for i in range(5):
            rect = pygame.Rect(x0 + 14 + i * 54, y0 + 42, 43, 36)
            self._last_ui_rects[f"preset_{i}"] = rect
            active = i == current_preset_idx
            bg = self.BLUE if active else (34, 53, 76)
            txt = (8, 14, 25) if active else self.WHITE
            pygame.draw.rect(screen, bg, rect, border_radius=6)
            pygame.draw.rect(screen, self.CYAN if active else self.PANEL_BORDER, rect, width=1, border_radius=6)
            self._text(screen, str(i + 1), rect.x + 16, rect.y + 9, font, txt)

        # Custom position editor in the sidebar, directly above the divergence graph.
        panel_width = max(430, min(500, int(screen.get_width() * 0.31)))
        x = self._panel_x(screen, panel_width)
        width = panel_width - 40
        graph_y = screen.get_height() - 177
        card_h = 220
        card_y = graph_y - card_h - 14
        card = pygame.Rect(x, card_y, width, card_h)
        pygame.draw.rect(screen, self.CARD, card, border_radius=8)
        pygame.draw.rect(screen, self.PANEL_BORDER, card, width=1, border_radius=8)

        self._text(screen, "CUSTOM INITIAL POSITIONS", x + 12, card_y + 10, font_title, self.CYAN)
        self._text(screen, "Universe B only — Universe A stays unchanged", x + 12, card_y + 30, font_small, self.MUTED)

        # Compact column labels.
        self._text(screen, "Body", x + 12, card_y + 50, font_small, self.MUTED)
        self._text(screen, "X", x + 55, card_y + 50, font_small, self.MUTED)
        self._text(screen, "Y", x + 170, card_y + 50, font_small, self.MUTED)

        for i in range(3):
            row_y = card_y + 67 + i * 24
            self._text(screen, str(i + 1), x + 15, row_y + 4, font, self.BODY_COLORS[i])
            for field, offset in (("x", 38), ("y", 153)):
                rect = pygame.Rect(x + offset, row_y, 104, 22)
                self._last_ui_rects[f"field_{i}_{field}"] = rect
                focused = self.position_field == (i, field)
                pygame.draw.rect(screen, (24, 37, 54) if focused else (10, 17, 28), rect, border_radius=5)
                pygame.draw.rect(screen, self.CYAN if focused else self.PANEL_BORDER, rect, width=1, border_radius=5)
                self._text(screen, self.position_text[i][field], rect.x + 6, rect.y + 3, font_small, self.WHITE)

        # Action buttons: random is a convenience only; Apply is the actual experiment change.
        random_rect = pygame.Rect(x + 268, card_y + 67, width - 280, 22)
        self._last_ui_rects["random_positions"] = random_rect
        pygame.draw.rect(screen, (47, 63, 84), random_rect, border_radius=5)
        pygame.draw.rect(screen, self.PANEL_BORDER, random_rect, width=1, border_radius=5)
        self._text(screen, "RANDOM", random_rect.x + 11, random_rect.y + 4, font_small, self.WHITE)

        update_rect = pygame.Rect(x + 268, card_y + 92, width - 280, 22)
        self._last_ui_rects["update_positions"] = update_rect
        pygame.draw.rect(screen, (28, 76, 112), update_rect, border_radius=5)
        pygame.draw.rect(screen, self.CYAN, update_rect, width=1, border_radius=5)
        self._text(screen, "APPLY", update_rect.x + 14, update_rect.y + 4, font_small, self.WHITE)

        reset_rect = pygame.Rect(x + 268, card_y + 117, width - 280, 22)
        self._last_ui_rects["reset_positions"] = reset_rect
        pygame.draw.rect(screen, (34, 53, 76), reset_rect, border_radius=5)
        pygame.draw.rect(screen, self.PANEL_BORDER, reset_rect, width=1, border_radius=5)
        self._text(screen, "RESET", reset_rect.x + 16, reset_rect.y + 4, font_small, self.WHITE)

        self._text(screen, "Same colour = same body  •  Solid = A  •  Dashed = B", x + 12, card_y + 143, font_small, self.MUTED)

        # Five representative, reproducible outcomes. These are separate from the
        # ordinary preset buttons because they specifically fill Universe B's custom
        # starting-position fields.
        self._text(screen, "GUIDED OUTCOME EXAMPLES", x + 12, card_y + 164, font_small, self.CYAN)
        self._text(screen, "Five representative outcomes — press H for the matching guide", x + 12, card_y + 181, font_small, self.MUTED)
        guided_ids = [
            "bounded_periodic", "bounded_rotating", "close_encounter",
            "slingshot_deflection", "strong_disruption"
        ]
        guided_labels = ["1 BND", "2 ROT", "3 CLOSE", "4 SLING", "5 BREAK"]
        for i in range(5):
            rect = pygame.Rect(x + 12 + i * 88, card_y + 198, 82, 18)
            self._last_ui_rects[f"guided_{i}"] = rect
            active = bool(active_guided_outcome) and active_guided_outcome == guided_ids[i]
            pygame.draw.rect(screen, self.BLUE if active else (34, 53, 76), rect, border_radius=4)
            pygame.draw.rect(screen, self.CYAN if active else self.PANEL_BORDER, rect, width=1, border_radius=4)
            label_surf = font_small.render(guided_labels[i], True, (8, 14, 25) if active else self.WHITE)
            screen.blit(label_surf, label_surf.get_rect(center=rect.center))

    def _randomize_positions(self, dual_system=None):
        """Generate a fresh, readable Universe B starting configuration near the preset baseline."""
        # This method is intentionally independent of the current custom values, so repeated
        # clicks do not cause the positions to drift farther and farther away.
        if dual_system is None:
            # The renderer receives the system through the event path only indirectly; use the
            # currently displayed fields as a safe fallback if no system was supplied.
            base = np.array([[float(r["x"]), float(r["y"])] for r in self.position_text], dtype=float)
        else:
            base = np.array([b.position for b in dual_system.perturbation.apply(dual_system.base_bodies)], dtype=float)

        rng = np.random.default_rng()
        for _ in range(100):
            candidate = base + rng.uniform(-1.25, 1.25, size=base.shape)
            distances = [float(np.linalg.norm(candidate[i] - candidate[j])) for i in range(3) for j in range(i + 1, 3)]
            if min(distances) >= 0.35:
                self.position_text = [
                    {"x": f"{candidate[i, 0]:.4f}", "y": f"{candidate[i, 1]:.4f}"}
                    for i in range(3)
                ]
                self.position_field = None
                self.position_message = "Random Universe B starting positions generated. Click APPLY to use them."
                self.position_message_until = pygame.time.get_ticks() + 3000
                return

        self.position_message = "Random position generation could not find a safely separated setup."
        self.position_message_until = pygame.time.get_ticks() + 2500

    # ------------------------------------------------------------------
    # Telemetry panel
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------

    def _panel_x(self, screen, panel_width):
        return screen.get_width() - panel_width + 20

    def _text(self, screen, text, x, y, font, color):
        screen.blit(font.render(text, True, color), (x, y))

    def _wrap(self, font, text, max_width):
        words = text.split()
        lines, current = [], ""
        for word in words:
            candidate = word if not current else current + " " + word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_wrapped(self, screen, text, x, y, font, color, max_width, gap=2):
        for line in self._wrap(font, text, max_width):
            self._text(screen, line, x, y, font, color)
            y += font.get_linesize() + gap
        return y

    def _render_telemetry(self, screen, panel_width, dual_system, dt, e0, p0):
        x = self._panel_x(screen, panel_width)
        width = panel_width - 40
        title = pygame.font.Font(None, 28)
        section = pygame.font.Font(None, 23)
        mono = pygame.font.Font(None, 18)
        small = pygame.font.Font(None, 15)

        self._text(screen, "SCIENTIFIC TELEMETRY", x, 22, title, self.CYAN)
        y = 61
        sys_a = dual_system.universe_A
        diag = ScientificDiagnostics.calculate_all(sys_a, dt)
        rmin, tau, ratio = diag["min_separation"], diag["encounter_timescale"], diag["dt_tau_ratio"]
        energy = diag["total_energy"]
        energy_drift = abs(energy - e0) / abs(e0) if e0 is not None and abs(e0) > 1e-14 else 0.0
        p_err = float(np.linalg.norm(diag["linear_momentum"] - (p0 if p0 is not None else 0.0)))
        divergence = dual_system.get_divergence()
        ftle = dual_system.get_ftle()

        rows = [
            ("Sim Time t", f"{sys_a.time:.4f}", "elapsed simulation time"),
            ("Time Step dt", f"{dt:.6f}", "time advanced per step"),
            ("Min Sep r_min", f"{rmin:.6f}", "smallest star-to-star distance"),
            ("Encounter tau", f"{tau:.6f}", "estimated close-encounter timescale"),
            ("Safety dt/tau", f"{ratio:.4f}", "numerical resolution ratio; <= 0.10"),
        ]
        for label, value, meaning in rows:
            self._text(screen, f"{label:<18}", x, y, mono, self.WHITE)
            self._text(screen, value, x + 165, y, mono, self.WHITE)
            self._text(screen, f"({meaning})", x, y + 14, small, self.MUTED)
            y += 35

        safe = bool(diag["is_resolved"])
        box = pygame.Rect(x, y + 4, width, 34)
        pygame.draw.rect(screen, (5, 145, 78) if safe else (125, 45, 45), box, border_radius=5)
        self._text(screen, "VALIDATED under current safety criterion" if safe else "NEEDS SMALLER TIMESTEP", box.x + 10, box.y + 9, small, self.WHITE)
        y = box.bottom + 17

        self._text(screen, f"Divergence D(t): {divergence:.4e}", x, y, mono, self.ORANGE)
        self._text(screen, "(combined position difference between A and B)", x, y + 14, small, self.MUTED)
        y += 35
        self._text(screen, f"FTLE lambda(t):  {ftle:.4f} time^-1", x, y, mono, self.ORANGE)
        self._text(screen, "(finite-time logarithmic growth rate of D)", x, y + 14, small, self.MUTED)
        y += 35
        d0 = dual_system.divergence_history[0] if dual_system.divergence_history else 0.0
        summary = "The two trajectories remain close in this interval." if divergence <= max(10.0 * d0, 1e-8) else "The two trajectories show growing sensitivity to the initial perturbation."
        y = self._draw_wrapped(screen, summary, x, y, small, self.MUTED, width)
        y += 9
        self._text(screen, f"Rel Energy Drift: {energy_drift:.4e}", x, y, mono, self.WHITE)
        self._text(screen, "(relative change in total energy from the baseline)", x, y + 14, small, self.MUTED)
        y += 35
        self._text(screen, f"Linear Mom Error:  {p_err:.4e}", x, y, mono, self.WHITE)
        self._text(screen, "(difference from initial total momentum)", x, y + 14, small, self.MUTED)
        y += 35

        self._text(screen, "CONTROLS", x, y, section, self.CYAN)
        y += 27
        controls = [
            "[SPACE] Pause / Resume     [R] Reset",
            "[1–5] Select Preset        [T] Trails",
            "[V] Vectors                 [L] Labels",
            "[H] Step-by-Step Physics Guide",
            "[A] Verification Audit",
        ]
        for line in controls:
            self._text(screen, line, x, y, small, self.MUTED)
            y += 21

        self._render_divergence_graph(screen, dual_system, x, screen.get_height() - 177, width)

    def _render_legend(self, screen, x, y, width):
        box_h = 122
        pygame.draw.rect(screen, self.CARD, (x, y, width, box_h), border_radius=6)
        pygame.draw.rect(screen, self.PANEL_BORDER, (x, y, width, box_h), width=1, border_radius=6)
        small = pygame.font.Font(None, 15)
        self._text(screen, "HOW TO READ A1 / B1", x + 10, y + 10, small, self.CYAN)
        self._text(screen, "A1 and B1 are the same physical body in two copies of the experiment.", x + 10, y + 29, small, self.WHITE)
        self._text(screen, "A = original starting state   •   B = tiny-change comparison", x + 10, y + 47, small, self.MUTED)
        self._text(screen, "Same colour = same body.   Solid = A.   Dashed = B.", x + 10, y + 65, small, self.MUTED)
        self._text(screen, "We label them this way so you can track the same star", x + 10, y + 83, small, self.MUTED)
        self._text(screen, "across both experiments and see exactly how its path changes.", x + 10, y + 100, small, self.MUTED)

    # ------------------------------------------------------------------
    # Step-by-step help
    # ------------------------------------------------------------------

    def _preset_key(self, name):
        n = name.lower()
        if "figure" in n:
            return "figure_eight"
        if "triangle" in n:
            return "triangle_orbit"
        if "unstable" in n or "encounter" in n:
            return "unstable_encounter"
        if "slingshot" in n:
            return "gravity_slingshot"
        return "straight_line"

    def _help_steps(self, preset_name, dual_system, dt, active_guided_outcome=None):
        key = active_guided_outcome or self._preset_key(preset_name)
        t = dual_system.universe_A.time
        d = dual_system.get_divergence()
        d0 = dual_system.divergence_history[0] if dual_system.divergence_history else d
        diag = ScientificDiagnostics.calculate_all(dual_system.universe_A, dt)
        ratio = diag["dt_tau_ratio"]
        rmin = diag["min_separation"]

        common = [
            ("WHY TWO UNIVERSES?", "We run two copies of the same three-star experiment. Universe A is the original. Universe B starts almost the same, but with a small change. Comparing them shows what that small change can do."),
            ("WHY A1 AND B1?", "A1 means Body 1 in Universe A. B1 means Body 1 in Universe B. They have the same number because they represent the same star in the two copies. The letter tells you which copy you are looking at."),
            ("WHY DO THE TRAILS SEPARATE?", f"The trails show where the stars actually moved. Right now D(t) = {d:.3e}, starting from D(0) = {d0:.3e}. If the trails separate, the two copies have ended up in different positions."),
            ("WHAT SHOULD I WATCH?", f"Watch the matching colours, the trails and the D(t) graph. A growing D(t) means the two copies are becoming more different. It shows sensitivity to the starting conditions; it does not by itself prove chaos."),
        ]

        specific = {
            "figure_eight": [
                ("1. THE START", "Three equal-mass stars begin in a special figure-eight arrangement. Their starting speeds are chosen so the pattern can repeat."),
                ("2. GRAVITY TAKES OVER", "Every star pulls on the other two. Those pulls change their speeds and directions, creating the curved figure-eight paths you see."),
                ("3. ONE TINY CHANGE", "Universe B gets a very small change to one starting position. Everything else is kept the same so we can make a fair comparison."),
                ("4. WATCH THE DIFFERENCE", "At first the two copies can look almost identical. If the paths slowly pull apart, that tiny starting change has been amplified by the motion of the three stars."),
                ("5. WHAT THIS TELLS US", "The original figure-eight is designed to repeat. The comparison lets us see how sensitive that motion is to a small change. The graph gives us a number for the difference, not just a visual impression."),
            ],
            "triangle_orbit": [
                ("1. THE START", "The three stars begin at the corners of a triangle. Their starting speeds are chosen so the whole shape can rotate together."),
                ("2. GRAVITY BALANCES", "Each star is pulled toward the other two. In this special arrangement, those pulls work together to keep the three-star pattern organised."),
                ("3. ONE TINY CHANGE", "Universe B starts with a tiny position change for one star. Universe A keeps the original triangle."),
                ("4. COMPARE THE PATHS", "Look at the matching colours and the D(t) graph. If the paths stay close, the two copies are behaving similarly. If D(t) grows, their positions are becoming more different."),
                ("5. READ THE RESULT", "This experiment shows how long the organised motion stays similar after a small change. A measured growth rate describes this setup and time interval; it is not automatically a label for every triangle orbit."),
            ],
            "unstable_encounter": [
                ("1. THE START", "The three stars have different masses and start relatively close together. Their motion is not a simple repeating pattern."),
                ("2. THREE-WAY GRAVITY", "All three stars pull on each other at the same time. As they move, the direction and strength of those pulls keep changing."),
                ("3. ONE TINY CHANGE", "Universe B gets a tiny change to one starting position. We then watch whether that small difference becomes larger during the interaction."),
                ("4. CLOSE PASS", "When two stars get very close, gravity becomes much stronger. That can bend their paths quickly, which is why the simulation also checks whether the timestep is small enough."),
                ("5. COMPARE CAREFULLY", "The two copies may end up on very different paths. Use the trails, D(t), energy drift and timestep-safety indicator together rather than judging the result from appearance alone."),
            ],
            "gravity_slingshot": [
                ("1. THE SETUP", "Two heavier stars form a close pair while a lighter star approaches them. All three still pull on each other."),
                ("2. A GRAVITY BOOST", "When the lighter star passes near the pair, the strong gravitational interaction can bend its path dramatically. Energy and momentum are exchanged between the stars."),
                ("3. ONE TINY CHANGE", "Universe B starts with a tiny change to the incoming star's starting velocity. That slightly changes where it meets the pair."),
                ("4. COMPARE THE DEFLECTION", "A small change in the approach can lead to a noticeably different path after the encounter. Watch the matching colours and D(t)."),
                ("5. CHECK THE NUMBERS", "A close encounter needs a small enough timestep to be trustworthy. If the safety indicator turns red, reduce dt before interpreting the fine details."),
            ],
            "straight_line": [
                ("1. THE START", "The three stars begin lined up along one direction. This gives the experiment a very simple starting shape."),
                ("2. GRAVITY CHANGES THINGS", "Each star is pulled by the other two, so the simple starting arrangement quickly develops into motion."),
                ("3. ONE TINY CHANGE", "Universe B receives a small change to one starting position. Universe A remains unchanged."),
                ("4. WATCH D(t)", "As the two copies evolve, their paths can become different. D(t) adds up the position differences between the matching stars."),
                ("5. WHAT TO LEARN", "This setup makes the main idea easy to see: two systems can start almost the same and still develop different motion because their starting conditions are not exactly identical."),
            ],
        }
        # Keep the guide short: two shared orientation steps, three preset-specific steps,
        # then one interpretation step. This keeps it understandable for a Year 10 audience.
        specific_short = {
            "figure_eight": [
                ("THE START", "Three equal-mass stars begin in a special figure-eight arrangement. Their starting speeds are chosen so the pattern can repeat."),
                ("GRAVITY MAKES THE PATH", "Each star pulls on the other two. Those pulls constantly change the stars' directions and speeds, producing the curved paths."),
                ("THE TINY CHANGE", "Universe B gets a very small change to one starting position. Universe A keeps the original starting position, so the comparison is fair."),
            ],
            "triangle_orbit": [
                ("THE START", "The three stars begin at the corners of a triangle. Their starting speeds are chosen so the whole shape can rotate together."),
                ("WHY IT CAN STAY TOGETHER", "Each star is pulled toward the other two. In this special setup, those pulls work together to keep the pattern organised."),
                ("THE TINY CHANGE", "Universe B gets a tiny change to one starting position. Universe A keeps the original triangle."),
            ],
            "unstable_encounter": [
                ("THE START", "The three stars have different masses and begin fairly close together. Their motion is not a simple repeating pattern."),
                ("THREE-WAY GRAVITY", "All three stars pull on each other at once. When two come close, their paths can change quickly."),
                ("THE TINY CHANGE", "Universe B gets a tiny change to one starting position. We watch whether the later motion becomes noticeably different."),
            ],
            "gravity_slingshot": [
                ("THE START", "Two heavier stars form a close pair while a lighter star approaches them. All three still pull on each other."),
                ("THE FLY-BY", "When the lighter star passes near the pair, gravity can bend its path strongly. This is the basic idea behind a gravitational slingshot."),
                ("THE TINY CHANGE", "Universe B gets a tiny change to the incoming star's starting position. We then compare the two fly-bys."),
            ],
            "straight_line": [
                ("THE START", "The three stars begin lined up along one direction. This gives the experiment a simple starting shape."),
                ("GRAVITY CHANGES THINGS", "Each star is pulled by the other two, so the simple starting arrangement quickly turns into motion."),
                ("THE TINY CHANGE", "Universe B receives a small change to one starting position. Universe A stays unchanged."),
            ],
        }
        guided = {
            "bounded_periodic": [
                ("GUIDED 1: BOUNDED / PERIODIC", "Universe B starts almost exactly on the figure-eight solution. The three stars remain in a compact, repeating-style configuration rather than flying away."),
                ("GRAVITY REPEATS THE CHOREOGRAPHY", "Each star is continuously accelerated by the other two. The special starting positions and velocities keep the motion organised."),
                ("WHY A AND B LOOK SIMILAR", "Only a tiny position change separates the copies. Their paths can stay close for a long time, so D(t) may grow slowly compared with more strongly disrupted cases."),
                ("WHAT TO WATCH", "Watch the repeated shape, matching colours and the D(t) graph. Small visual differences are expected even when the overall motion remains bounded."),
                ("WHAT IT TEACHES", "Not every small change immediately destroys an organised orbit. The response depends on the particular initial conditions and the time interval studied."),
            ],
            "bounded_rotating": [
                ("GUIDED 2: BOUNDED / ROTATING", "Universe B uses the triangular three-body configuration with a small position change. The three stars remain in a compact, rotating pattern."),
                ("BALANCED GRAVITY", "The three equal masses pull toward one another. The initial velocities are chosen so the whole configuration rotates rather than simply collapsing."),
                ("THE PERTURBATION", "Universe A keeps the exact preset triangle while Universe B moves one starting position slightly. This lets you compare two nearly identical rotating systems."),
                ("WATCH THE SHAPE", "Track the matching colours. The important question is whether the triangle-like organisation persists while D(t) measures the separation between the copies."),
                ("WHAT IT TEACHES", "A bounded three-body motion can remain organised even though every star is constantly accelerating. Stability and sensitivity are properties of the specific orbit, not just the word 'three-body'."),
            ],
            "close_encounter": [
                ("GUIDED 3: CLOSE ENCOUNTER", "This setup brings the three stars into a much stronger interaction. One or more pairs can pass very close together, making the gravitational acceleration change rapidly."),
                ("WHY CLOSE PASSES MATTER", "Newtonian gravity scales as 1/r² for acceleration. As r becomes small, the acceleration becomes much larger, so the paths can bend sharply."),
                ("WATCH THE TIMESTEP", f"The current dt is {dt:.6f}. The Safety dt/tau value compares that timestep with the local encounter timescale. A large ratio means the numerical step is too coarse for fine details."),
                ("COMPARE A AND B", "The two universes can separate rapidly after the close interaction. A large D(t) is evidence that the trajectories have become different, but it is not by itself proof of mathematical chaos."),
                ("WHAT IT TEACHES", "Close encounters are where three-body motion becomes especially sensitive and numerically demanding. Use the safety indicator and conservation diagnostics before trusting the fine structure."),
            ],
            "slingshot_deflection": [
                ("GUIDED 4: SLINGSHOT / DEFLECTION", "Two heavier stars form a compact pair while a lighter star approaches. The lighter body's path is strongly affected by the gravitational field of the pair."),
                ("THE FLY-BY", "As the light body passes near the binary, gravity changes its velocity vector. The path can bend substantially even though no engine or collision is involved."),
                ("THE SMALL CHANGE", "Universe B starts with a slightly different incoming position. That changes the geometry of the fly-by and therefore the later trajectory."),
                ("WATCH THE EXIT", "Compare the direction and distance travelled by the matching light bodies after the encounter. D(t) records the total positional difference across all three stars."),
                ("WHAT IT TEACHES", "A gravitational encounter can transfer energy and momentum between bodies and redirect a trajectory. The exact outcome depends sensitively on the encounter geometry."),
            ],
            "strong_disruption": [
                ("GUIDED 5: STRONG DISRUPTION", "This collinear setup is deliberately easy to disturb. A small change to one starting position breaks the exact symmetry between the two copies."),
                ("SYMMETRY BREAKS", "Gravity acts along changing lines between the stars. Once the two copies are not perfectly symmetric, their accelerations are no longer identical."),
                ("THE DIFFERENCE GROWS", "The small geometric difference can alter later close approaches. That can produce a much larger separation between the A and B trajectories."),
                ("WATCH FOR BREAK-UP", "Some runs can send one body much farther from the others. If a close encounter occurs, check the Safety dt/tau and energy drift before treating the apparent ejection as quantitatively reliable."),
                ("WHAT IT TEACHES", "Three-body systems can move from a simple initial arrangement to complicated motion because the force on each body continually depends on the other two positions."),
            ],
        }
        if active_guided_outcome in guided:
            return guided[active_guided_outcome]

        final = [
            common[0],
            specific_short[key][0],
            specific_short[key][1],
            specific_short[key][2],
            common[1],
            common[2],
            common[3],
        ]
        return final

    def _render_help(self, screen, panel_width, dual_system, dt, preset_name, active_guided_outcome=None):
        x = self._panel_x(screen, panel_width)
        width = panel_width - 40
        card_h = 270
        card_y = screen.get_height() - 445
        title = pygame.font.Font(None, 24)
        heading = pygame.font.Font(None, 19)
        body = pygame.font.Font(None, 16)
        small = pygame.font.Font(None, 14)

        steps = self._help_steps(preset_name, dual_system, dt, active_guided_outcome)
        self.help_step = max(0, min(self.help_step, len(steps) - 1))
        step_title, step_text = steps[self.help_step]

        card = pygame.Rect(x, card_y, width, card_h)
        pygame.draw.rect(screen, self.CARD, card, border_radius=8)
        pygame.draw.rect(screen, self.PANEL_BORDER, card, width=1, border_radius=8)
        self._text(screen, "WHAT IS HAPPENING?", x + 12, card_y + 12, title, self.CYAN)
        self._text(screen, f"{self.help_step + 1} / {len(steps)}", x + width - 48, card_y + 16, small, self.MUTED)
        self._text(screen, step_title, x + 12, card_y + 47, heading, self.CYAN)
        self._draw_wrapped(screen, step_text, x + 12, card_y + 73, body, self.WHITE, width - 24, gap=2)

        button_y = card.bottom - 48
        prev = pygame.Rect(x + 10, button_y, 105, 32)
        nxt = pygame.Rect(x + width - 115, button_y, 105, 32)
        close = pygame.Rect(x + width // 2 - 45, button_y + 35, 90, 18)
        self._last_help_rects = {"previous": prev, "next": nxt, "close": close}
        self._button(screen, prev, "← PREVIOUS", self.help_step > 0)
        self._button(screen, nxt, "NEXT →", self.help_step < len(steps) - 1)
        self._text(screen, "[H] Close explanation", close.x + 7, close.y + 1, small, self.MUTED)

    def _button(self, screen, rect, label, enabled):
        bg = (36, 61, 91) if enabled else (27, 38, 53)
        border = self.CYAN if enabled else self.PANEL_BORDER
        text = self.WHITE if enabled else (95, 108, 125)
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, width=1, border_radius=5)
        f = pygame.font.Font(None, 17)
        screen.blit(f.render(label, True, text), f.render(label, True, text).get_rect(center=rect.center))

    # ------------------------------------------------------------------
    # Divergence graph
    # ------------------------------------------------------------------

    def _render_divergence_graph(self, screen, dual_system, x, y, width):
        height = 140
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 14, 24, 245), panel.get_rect(), border_radius=6)
        pygame.draw.rect(panel, self.PANEL_BORDER, panel.get_rect(), width=1, border_radius=6)
        title = pygame.font.Font(None, 17)
        small = pygame.font.Font(None, 14)
        self._text(panel, "POSITIONAL DIVERGENCE D(t)", 10, 8, title, self.WHITE)
        gx, gy = 10, 30
        gw, gh = width - 20, height - 40
        pygame.draw.rect(panel, (6, 10, 18), (gx, gy, gw, gh))
        for frac in (0.25, 0.5, 0.75):
            yy = gy + int(gh * frac)
            pygame.draw.line(panel, (22, 30, 43), (gx, yy), (gx + gw, yy), 1)
        history = dual_system.divergence_history
        if len(history) >= 2:
            max_val = max(max(history), 1e-12)
            points = []
            for i, value in enumerate(history):
                px = gx + int(gw * i / (len(history) - 1))
                py = gy + gh - int(gh * min(1.0, value / max_val))
                points.append((px, py))
            pygame.draw.lines(panel, self.ORANGE, False, points, 2)
        screen.blit(panel, (x, y))
