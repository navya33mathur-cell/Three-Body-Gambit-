"""
Layered Procedural Star Renderer for Orbital Echo.
Renders realistic 6-layer luminous stars with plasma texturing, radial glow, atmospheric halos, and core heat.
"""

import pygame
import numpy as np
from typing import Tuple, Dict

class ProceduralStarRenderer:
    """
    Renders realistic luminous stellar bodies procedurally.
    Utilizes 6 distinct radial layers:
      1. Outer Corona Glow (very large, soft alpha radial falloff)
      2. Atmospheric Stellar Halo
      3. Diffuse Luminous Envelope
      4. Textured Plasma Surface (procedural turbulent noise)
      5. Inner Convection Zone
      6. White-Hot Central Core
    """
    _cache: Dict[Tuple[int, Tuple[int, int, int]], pygame.Surface] = {}

    @classmethod
    def get_star_surface(cls, radius_px: int, color: Tuple[int, int, int]) -> pygame.Surface:
        """
        Retrieves or generates a cached surface containing the rendered star.
        Surface dimensions are 4 * radius_px to fit the extensive outer glow corona.
        """
        radius_px = int(max(10, radius_px))
        color_key = tuple(color)
        key = (radius_px, color_key)

        if key in cls._cache:
            return cls._cache[key]

        surface = cls._generate_star_surface(radius_px, color_key)
        cls._cache[key] = surface
        return surface

    @classmethod
    def _generate_star_surface(cls, radius: int, color: Tuple[int, int, int]) -> pygame.Surface:
        """Generates a 6-layer procedural star surface vectorized with NumPy."""
        canvas_size = int(radius * 4)
        center = canvas_size // 2
        surface = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)

        r, g, b = color

        # --- Layer 1: Outer Corona Glow (Radius ~ 2.0x) ---
        corona_radius = int(radius * 2.0)
        for rad in range(corona_radius, int(radius * 1.2), -3):
            factor = (1.0 - (rad - radius * 1.2) / (corona_radius - radius * 1.2)) ** 2
            alpha = int(35 * factor)
            if alpha > 0:
                pygame.draw.circle(surface, (r, g, b, alpha), (center, center), rad)

        # --- Layer 2: Atmospheric Stellar Halo (Radius ~ 1.3x) ---
        halo_radius = int(radius * 1.3)
        for rad in range(halo_radius, radius, -2):
            factor = (1.0 - (rad - radius) / (halo_radius - radius)) ** 1.5
            alpha = int(70 * factor)
            if alpha > 0:
                pygame.draw.circle(surface, (min(255, r + 40), min(255, g + 40), min(255, b + 40), alpha), (center, center), rad)

        # --- Layer 3: Diffuse Luminous Envelope (Radius ~ 1.0x) ---
        for rad in range(radius, int(radius * 0.8), -2):
            factor = (rad - radius * 0.8) / (radius * 0.2)
            alpha = int(180 + 75 * factor)
            cr = min(255, int(r * 0.9 + 25 * factor))
            cg = min(255, int(g * 0.9 + 25 * factor))
            cb = min(255, int(b * 0.9 + 25 * factor))
            pygame.draw.circle(surface, (cr, cg, cb, alpha), (center, center), rad)

        # --- Layer 4: Textured Plasma Surface (Radius ~ 0.8x) Vectorized ---
        surf_r = int(radius * 0.8)
        surf_diameter = surf_r * 2
        if surf_r > 2:
            y, x = np.ogrid[-surf_r:surf_r, -surf_r:surf_r]
            dist_grid = np.sqrt(x**2 + y**2)
            mask = dist_grid <= surf_r

            noise = (
                np.sin(x * 0.15) * np.cos(y * 0.15) * 0.4 +
                np.sin(x * 0.3 + y * 0.2) * 0.3 +
                np.cos(dist_grid * 0.2) * 0.3
            )
            brightness = 0.85 + 0.3 * (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)

            rgba_array = np.zeros((surf_diameter, surf_diameter, 4), dtype=np.uint8)
            rgba_array[:, :, 0] = np.clip(r * brightness, 0, 255).astype(np.uint8)
            rgba_array[:, :, 1] = np.clip(g * brightness, 0, 255).astype(np.uint8)
            rgba_array[:, :, 2] = np.clip(b * brightness, 0, 255).astype(np.uint8)
            rgba_array[:, :, 3] = (mask * 255).astype(np.uint8)

            plasma_surf = pygame.image.frombuffer(
                rgba_array.tobytes(), (surf_diameter, surf_diameter), "RGBA"
            )
            surface.blit(plasma_surf, (center - surf_r, center - surf_r))

        # --- Layer 5: Inner Convection Zone (Radius ~ 0.5x) ---
        conv_radius = int(radius * 0.5)
        for rad in range(conv_radius, int(radius * 0.25), -2):
            factor = (rad - radius * 0.25) / (radius * 0.25)
            cr = min(255, int(r + (255 - r) * (1.0 - factor) * 0.6))
            cg = min(255, int(g + (255 - g) * (1.0 - factor) * 0.6))
            cb = min(255, int(b + (255 - b) * (1.0 - factor) * 0.6))
            pygame.draw.circle(surface, (cr, cg, cb, 230), (center, center), rad)

        # --- Layer 6: White-Hot Central Core (Radius ~ 0.25x) ---
        core_radius = max(2, int(radius * 0.25))
        for rad in range(core_radius, 0, -1):
            factor = 1.0 - (rad / core_radius)
            cr = min(255, int(220 + 35 * factor))
            cg = min(255, int(235 + 20 * factor))
            cb = 255
            pygame.draw.circle(surface, (cr, cg, cb, 255), (center, center), rad)

        return surface

    @classmethod
    def render_star(cls, screen: pygame.Surface, screen_pos: Tuple[int, int], radius_px: float, color: Tuple[int, int, int]):
        """Renders a star at specified screen position."""
        star_surf = cls.get_star_surface(int(radius_px), color)
        rect = star_surf.get_rect(center=screen_pos)
        screen.blit(star_surf, rect, special_flags=pygame.BLEND_ALPHA_SDL2)
