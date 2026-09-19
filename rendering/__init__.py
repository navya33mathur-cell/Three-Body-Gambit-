"""Rendering package for THREE-BODY GAMBIT."""

from rendering.camera import Camera
from rendering.stars import ProceduralStarRenderer
from rendering.background import DeepSpaceBackground
from rendering.trails import TrailRenderer, TrailBuffer
from rendering.scientific import ScientificRenderer

__all__ = [
    "Camera",
    "ProceduralStarRenderer",
    "DeepSpaceBackground",
    "TrailRenderer",
    "TrailBuffer",
    "ScientificRenderer",
]
