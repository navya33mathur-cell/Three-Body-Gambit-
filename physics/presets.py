"""
Presets module for Orbital Echo.
Contains 5 scientifically curated initial three-body configurations.
"""

from typing import List, Dict, Any
from physics.nbody import Body
from physics.dual_universe import PerturbationConfig

def get_builtin_presets() -> List[Dict[str, Any]]:
    """Returns the 5 built-in experiment presets."""
    return [
        {
            "id": "figure_eight",
            "name": "1. Figure-Eight Dance",
            "description": "Classic stable three-body periodic choreography discovered by Chenciner & Montgomery (2000).",
            "G": 1.0,
            "dt": 0.005,
            "duration": 20.0,
            "perturbation": {
                "body_index": 0,
                "target": "pos_x",
                "magnitude": 1e-4
            },
            "bodies": [
                {
                    "name": "Alpha",
                    "mass": 1.0,
                    "position": [-0.97000436, 0.24308753],
                    "velocity": [0.46620531, 0.43236573],
                    "color": [80, 160, 255], # Blue-white star
                    "radius": 90.0
                },
                {
                    "name": "Beta",
                    "mass": 1.0,
                    "position": [0.97000436, -0.24308753],
                    "velocity": [0.46620531, 0.43236573],
                    "color": [255, 240, 200], # Yellow-white star
                    "radius": 90.0
                },
                {
                    "name": "Gamma",
                    "mass": 1.0,
                    "position": [0.0, 0.0],
                    "velocity": [-0.93241062, -0.86473146],
                    "color": [255, 255, 255], # White star
                    "radius": 90.0
                }
            ]
        },
        {
            "id": "triangle_orbit",
            "name": "2. Triangle Orbit",
            "description": "Lagrange equilateral triangular setup with balanced angular velocity.",
            "G": 1.0,
            "dt": 0.005,
            "duration": 25.0,
            "perturbation": {
                "body_index": 1,
                "target": "pos_y",
                "magnitude": 1e-4
            },
            "bodies": [
                {
                    "name": "Sol-A",
                    "mass": 1.0,
                    "position": [1.0, 0.0],
                    "velocity": [0.0, 0.57735],
                    "color": [100, 180, 255],
                    "radius": 90.0
                },
                {
                    "name": "Sol-B",
                    "mass": 1.0,
                    "position": [-0.5, 0.866025],
                    "velocity": [-0.5, -0.288675],
                    "color": [255, 230, 180],
                    "radius": 90.0
                },
                {
                    "name": "Sol-C",
                    "mass": 1.0,
                    "position": [-0.5, -0.866025],
                    "velocity": [0.5, -0.288675],
                    "color": [255, 255, 255],
                    "radius": 90.0
                }
            ]
        },
        {
            "id": "unstable_encounter",
            "name": "3. Unstable Three-Body Encounter",
            "description": "Highly chaotic triple interaction exhibiting extreme sensitivity to initial conditions.",
            "G": 1.0,
            "dt": 0.002,
            "duration": 15.0,
            "perturbation": {
                "body_index": 0,
                "target": "pos_x",
                "magnitude": 1e-5
            },
            "bodies": [
                {
                    "name": "Ignis",
                    "mass": 1.2,
                    "position": [-1.2, 0.1],
                    "velocity": [0.15, -0.1],
                    "color": [255, 220, 150],
                    "radius": 110.0
                },
                {
                    "name": "Pyra",
                    "mass": 0.9,
                    "position": [1.1, -0.2],
                    "velocity": [-0.1, 0.25],
                    "color": [120, 200, 255],
                    "radius": 80.0
                },
                {
                    "name": "Vortex",
                    "mass": 1.0,
                    "position": [0.0, 0.8],
                    "velocity": [-0.05, -0.15],
                    "color": [255, 255, 255],
                    "radius": 90.0
                }
            ]
        },
        {
            "id": "gravity_slingshot",
            "name": "4. Gravity Slingshot",
            "description": "A light star falls towards a tight binary pair, resulting in a intense gravitational catapult.",
            "G": 1.0,
            "dt": 0.002,
            "duration": 20.0,
            "perturbation": {
                "body_index": 2,
                "target": "vel_y",
                "magnitude": 1e-5
            },
            "bodies": [
                {
                    "name": "Binary Core A",
                    "mass": 2.0,
                    "position": [-0.4, 0.0],
                    "velocity": [0.0, -0.7],
                    "color": [90, 170, 255],
                    "radius": 130.0
                },
                {
                    "name": "Binary Core B",
                    "mass": 2.0,
                    "position": [0.4, 0.0],
                    "velocity": [0.0, 0.7],
                    "color": [255, 240, 190],
                    "radius": 130.0
                },
                {
                    "name": "Passerby",
                    "mass": 0.2,
                    "position": [-2.5, -1.8],
                    "velocity": [0.65, 0.55],
                    "color": [255, 255, 255],
                    "radius": 60.0
                }
            ]
        },
        {
            "id": "straight_line",
            "name": "5. Straight-Line Setup",
            "description": "Collinear three-body alignment demonstrating instability along the line of centers.",
            "G": 1.0,
            "dt": 0.002,
            "duration": 15.0,
            "perturbation": {
                "body_index": 1,
                "target": "pos_y",
                "magnitude": 1e-4
            },
            "bodies": [
                {
                    "name": "Left Star",
                    "mass": 1.0,
                    "position": [-1.5, 0.0],
                    "velocity": [0.0, 0.3],
                    "color": [130, 210, 255],
                    "radius": 90.0
                },
                {
                    "name": "Center Star",
                    "mass": 1.0,
                    "position": [0.0, 0.0],
                    "velocity": [0.0, -0.6],
                    "color": [255, 255, 255],
                    "radius": 90.0
                },
                {
                    "name": "Right Star",
                    "mass": 1.0,
                    "position": [1.5, 0.0],
                    "velocity": [0.0, 0.3],
                    "color": [255, 230, 170],
                    "radius": 90.0
                }
            ]
        }
    ]

def load_preset_bodies(preset_dict: Dict[str, Any]) -> List[Body]:
    """Converts preset dictionary into a list of Body objects."""
    return [Body.from_dict(b) for b in preset_dict["bodies"]]

def load_preset_perturbation(preset_dict: Dict[str, Any]) -> PerturbationConfig:
    """Converts preset dictionary perturbation into PerturbationConfig."""
    return PerturbationConfig.from_dict(preset_dict.get("perturbation", {}))
