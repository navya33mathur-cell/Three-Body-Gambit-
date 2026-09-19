"""
Procedural Deep-Space Background Generator for Orbital Echo.
Renders layered starfields, multi-depth stellar background, and faint galactic haze.
"""

import pygame
import numpy as np
from typing import Tuple

class DeepSpaceBackground:
    """
    Renders a rich procedural deep-space background.
    Includes:
      - Multi-depth starfields (micro stars, distant stars, bright stars)
      - Faint galactic haze / Milky Way dust structure
      - Subtle brightness variations across deep space
    """
    def __init__(self, width: int = 1600, height: int = 900):
        self.width = width
        self.height = height
        self.background_surface = self._generate_background(width, height)

    def resize(self, width: int, height: int):
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self.background_surface = self._generate_background(width, height)

    def _generate_background(self, w: int, h: int) -> pygame.Surface:
        """Generates a high-quality static deep space surface."""
        surface = pygame.Surface((w, h))
        # Deep space dark radial gradient background
        bg_array = np.zeros((h, w, 3), dtype=np.uint8)

        # Subtle dark space color base: dark navy / deep void [4, 6, 14]
        y_grid, x_grid = np.ogrid[0:h, 0:w]
        center_x, center_y = w * 0.5, h * 0.5
        norm_dist = np.sqrt((x_grid - center_x)**2 + (y_grid - center_y)**2) / np.sqrt(center_x**2 + center_y**2)

        # Core radial glow
        bg_array[:, :, 0] = np.clip(12 - norm_dist * 8, 2, 20).astype(np.uint8) # R
        bg_array[:, :, 1] = np.clip(16 - norm_dist * 10, 4, 25).astype(np.uint8) # G
        bg_array[:, :, 2] = np.clip(28 - norm_dist * 14, 8, 40).astype(np.uint8) # B

        # --- Faint Galactic Dust Haze / Band ---
        # Angle band across screen
        angle_grid = (x_grid * 0.4 + y_grid * 0.6) / np.sqrt(w**2 + h**2)
        haze = np.exp(-((angle_grid - 0.5) ** 2) / 0.04) * 18.0

        bg_array[:, :, 0] = np.clip(bg_array[:, :, 0] + haze * 0.6, 0, 255).astype(np.uint8)
        bg_array[:, :, 1] = np.clip(bg_array[:, :, 1] + haze * 0.7, 0, 255).astype(np.uint8)
        bg_array[:, :, 2] = np.clip(bg_array[:, :, 2] + haze * 1.0, 0, 255).astype(np.uint8)

        pygame.surfarray.blit_array(surface, np.transpose(bg_array, (1, 0, 2)))

        # --- Layer 1: Distant Micro-Stars (approx 400 tiny dots) ---
        np.random.seed(42) # Deterministic background
        num_micro = 400
        micro_x = np.random.randint(0, w, num_micro)
        micro_y = np.random.randint(0, h, num_micro)
        micro_b = np.random.randint(40, 160, num_micro)

        for x, y, b in zip(micro_x, micro_y, micro_b):
            surface.set_at((x, y), (b, b, min(255, b + 30)))

        # --- Layer 2: Medium Stars (approx 120 stars with slight radius) ---
        num_med = 120
        med_x = np.random.randint(0, w, num_med)
        med_y = np.random.randint(0, h, num_med)
        med_b = np.random.randint(140, 230, num_med)

        for x, y, b in zip(med_x, med_y, med_b):
            color = (min(255, b - 10), b, min(255, b + 25))
            pygame.draw.circle(surface, color, (x, y), 1)

        # --- Layer 3: Bright Stars with subtle glow (approx 25 stars) ---
        num_bright = 25
        bright_x = np.random.randint(0, w, num_bright)
        bright_y = np.random.randint(0, h, num_bright)

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        for x, y in zip(bright_x, bright_y):
            r_glow = np.random.randint(3, 7)
            pygame.draw.circle(overlay, (200, 220, 255, 30), (x, y), r_glow)
            pygame.draw.circle(overlay, (240, 245, 255, 220), (x, y), 2)

        surface.blit(overlay, (0, 0))
        return surface

    def render(self, screen: pygame.Surface):
        """Renders the static deep space background onto the target surface."""
        screen.blit(self.background_surface, (0, 0))
