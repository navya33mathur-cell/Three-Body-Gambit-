"""Trajectory history and scientific trail rendering."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pygame

from rendering.camera import Camera


class TrailBuffer:
    def __init__(self, max_length: int = 800):
        self.max_length = max_length
        self.history_A: Dict[int, List[np.ndarray]] = {}
        self.history_B: Dict[int, List[np.ndarray]] = {}

    def clear(self):
        self.history_A.clear()
        self.history_B.clear()

    def update(self, pos_A: np.ndarray, pos_B: np.ndarray):
        for history, positions in ((self.history_A, pos_A), (self.history_B, pos_B)):
            for i, pos in enumerate(positions):
                history.setdefault(i, []).append(pos.copy())
                if len(history[i]) > self.max_length:
                    history[i].pop(0)


class TrailRenderer:
    @staticmethod
    def render_scientific(screen: pygame.Surface, trail_buffer: TrailBuffer, camera: Camera, body_colors: List[Tuple[int, int, int]]):
        """Draw A and B trails in the exact same colour for each corresponding body.

        Universe A is a solid path; Universe B is a dashed path. The colour always
        identifies the physical body, while line style identifies the universe.
        """
        overlay = pygame.Surface((camera.screen_width, camera.screen_height), pygame.SRCALPHA)

        def draw_path(points, color, dashed=False):
            if len(points) < 2:
                return
            screen_pts = [camera.world_to_screen(p) for p in points]
            if not dashed:
                for j in range(1, len(screen_pts)):
                    alpha = int(210 * j / len(screen_pts))
                    pygame.draw.line(overlay, (*color, alpha), screen_pts[j - 1], screen_pts[j], 2)
                return

            dash = 7.0
            gap = 5.0
            distance = 0.0
            for j in range(1, len(screen_pts)):
                p1 = np.asarray(screen_pts[j - 1], dtype=float)
                p2 = np.asarray(screen_pts[j], dtype=float)
                vec = p2 - p1
                length = float(np.linalg.norm(vec))
                if length < 1e-8:
                    continue
                direction = vec / length
                cursor = 0.0
                while cursor < length:
                    cycle = (distance + cursor) % (dash + gap)
                    take = min(length - cursor, (dash + gap) - cycle)
                    if cycle < dash:
                        a = p1 + direction * cursor
                        b = p1 + direction * (cursor + take)
                        alpha = int(225 * j / len(screen_pts))
                        pygame.draw.line(overlay, (*color, alpha), tuple(a.astype(int)), tuple(b.astype(int)), 2)
                    cursor += take
                distance += length

        for i, points in trail_buffer.history_A.items():
            color = body_colors[i] if i < len(body_colors) else (200, 200, 255)
            draw_path(points, color, dashed=False)
        for i, points in trail_buffer.history_B.items():
            color = body_colors[i] if i < len(body_colors) else (200, 200, 255)
            draw_path(points, color, dashed=True)

        screen.blit(overlay, (0, 0))
