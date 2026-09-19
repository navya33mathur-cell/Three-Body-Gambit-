"""
Camera system for Orbital Echo.
Handles screen transformation, smooth auto-framing, follow center-of-mass, and smooth zoom interpolation.
"""

import numpy as np
from typing import Tuple

class Camera:
    """
    Translates physical world coordinates (dimensionless) to screen coordinates (pixels).
    Smoothly tracks the center of mass and adjusts zoom scale to keep all bodies comfortably in view.
    """
    def __init__(self, screen_width: int = 1600, screen_height: int = 900):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # World focus target (center of mass)
        self.target_center = np.array([0.0, 0.0], dtype=np.float64)
        self.current_center = np.array([0.0, 0.0], dtype=np.float64)

        # Zoom / Scale (pixels per world unit)
        self.target_scale = 200.0  # default pixels per unit
        self.current_scale = 200.0

        # Smoothing factors
        self.center_lerp = 0.08
        self.zoom_lerp = 0.08

        # Minimum / Maximum bounds
        self.min_scale = 20.0
        self.max_scale = 800.0
        self.padding_factor = 1.4

    def resize(self, width: int, height: int):
        self.screen_width = width
        self.screen_height = height

    def update_auto_frame(self, positions: np.ndarray, com: np.ndarray = None, dt: float = 0.016):
        """
        Calculates optimal camera center and zoom scale based on current body positions.
        """
        if len(positions) == 0:
            return

        if com is not None:
            self.target_center = com.copy()
        else:
            self.target_center = np.mean(positions, axis=0)

        # Compute bounding extent relative to target center
        diffs = positions - self.target_center
        max_dist_x = np.max(np.abs(diffs[:, 0])) if len(diffs) > 0 else 1.0
        max_dist_y = np.max(np.abs(diffs[:, 1])) if len(diffs) > 0 else 1.0

        # Prevent division by zero
        max_dist_x = max(max_dist_x, 0.2)
        max_dist_y = max(max_dist_y, 0.2)

        # Available screen space with padding
        half_w = (self.screen_width * 0.5) / self.padding_factor
        half_h = (self.screen_height * 0.5) / self.padding_factor

        scale_x = half_w / max_dist_x
        scale_y = half_h / max_dist_y
        self.target_scale = float(np.clip(min(scale_x, scale_y), self.min_scale, self.max_scale))

        # Smooth interpolation (lerp)
        self.current_center += (self.target_center - self.current_center) * self.center_lerp
        self.current_scale += (self.target_scale - self.current_scale) * self.zoom_lerp

    def world_to_screen(self, world_pos: np.ndarray) -> Tuple[int, int]:
        """Converts physical world position (x, y) to screen pixel coordinates (px, py)."""
        rel_x = world_pos[0] - self.current_center[0]
        rel_y = world_pos[1] - self.current_center[1]

        # Invert Y for screen coordinates (screen Y increases downward)
        px = self.screen_width * 0.5 + rel_x * self.current_scale
        py = self.screen_height * 0.5 - rel_y * self.current_scale
        return int(round(px)), int(round(py))

    def screen_to_world(self, screen_pos: Tuple[int, int]) -> np.ndarray:
        """Converts screen pixel coordinates (px, py) to physical world position (x, y)."""
        rel_x = (screen_pos[0] - self.screen_width * 0.5) / self.current_scale
        rel_y = (self.screen_height * 0.5 - screen_pos[1]) / self.current_scale
        return np.array([rel_x + self.current_center[0], rel_y + self.current_center[1]], dtype=np.float64)

    def world_distance_to_screen(self, dist: float) -> int:
        """Converts a world distance length to screen pixels."""
        return max(1, int(round(dist * self.current_scale)))
