"""
Physics package for Orbital Echo three-body simulation.
"""

from physics.nbody import Body, NBodySystem
from physics.integrator import VelocityVerletIntegrator
from physics.diagnostics import ScientificDiagnostics
from physics.dual_universe import PerturbationConfig, DualUniverseSystem
from physics.presets import get_builtin_presets, load_preset_bodies, load_preset_perturbation

__all__ = [
    "Body",
    "NBodySystem",
    "VelocityVerletIntegrator",
    "ScientificDiagnostics",
    "PerturbationConfig",
    "DualUniverseSystem",
    "get_builtin_presets",
    "load_preset_bodies",
    "load_preset_perturbation"
]
