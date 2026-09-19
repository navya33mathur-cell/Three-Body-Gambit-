"""Guided custom-position experiments for THREE-BODY GAMBIT.

These are representative, reproducible starting-position examples rather than
an exhaustive catalogue of all possible three-body outcomes.
"""

from __future__ import annotations

import numpy as np

from physics.presets import get_builtin_presets, load_preset_bodies


def get_guided_outcomes():
    """Return five representative guided custom-position experiments."""
    presets = get_builtin_presets()

    def positions_for(preset_index: int, changes: dict[int, tuple[float, float]]):
        positions = np.array(
            [b.position for b in load_preset_bodies(presets[preset_index])],
            dtype=np.float64,
        )
        for body_index, delta in changes.items():
            positions[body_index] += np.asarray(delta, dtype=np.float64)
        return positions

    return [
        {
            "id": "bounded_periodic",
            "name": "1. BOUNDED / PERIODIC",
            "short": "Figure-eight motion stays bounded",
            "preset_index": 0,
            "positions": positions_for(0, {0: (5e-4, 0.0)}),
        },
        {
            "id": "bounded_rotating",
            "name": "2. BOUNDED / ROTATING",
            "short": "Triangle-like motion stays organised",
            "preset_index": 1,
            "positions": positions_for(1, {1: (0.0, 0.002)}),
        },
        {
            "id": "close_encounter",
            "name": "3. CLOSE ENCOUNTER",
            "short": "A close pass strongly bends trajectories",
            "preset_index": 2,
            "positions": positions_for(2, {0: (0.01, 0.0)}),
        },
        {
            "id": "slingshot_deflection",
            "name": "4. SLINGSHOT / DEFLECTION",
            "short": "A light body is strongly deflected",
            "preset_index": 3,
            "positions": positions_for(3, {2: (0.0, 0.02)}),
        },
        {
            "id": "strong_disruption",
            "name": "5. STRONG DISRUPTION",
            "short": "The three-body arrangement can break apart",
            "preset_index": 4,
            "positions": positions_for(4, {1: (0.0, 0.02)}),
        },
    ]
