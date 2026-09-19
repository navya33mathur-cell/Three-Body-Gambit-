"""
Dual Universe simulation manager for Orbital Echo.
Runs Universe A (unperturbed) and Universe B (perturbed) independently and measures divergence D(t) and FTLE growth rate.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from physics.nbody import NBodySystem, Body
from physics.integrator import VelocityVerletIntegrator

class PerturbationConfig:
    """Configures a small controlled perturbation applied to Universe B."""
    def __init__(
        self,
        body_index: int = 0,
        target: str = "pos_x", # "pos_x", "pos_y", "vel_x", "vel_y"
        magnitude: float = 1e-4
    ):
        self.body_index = int(body_index)
        self.target = str(target)
        self.magnitude = float(magnitude)

    def apply(self, bodies: List[Body]) -> List[Body]:
        """Returns a copy of bodies with the perturbation applied."""
        new_bodies = [b.copy() for b in bodies]
        if 0 <= self.body_index < len(new_bodies):
            b = new_bodies[self.body_index]
            if self.target == "pos_x":
                b.position[0] += self.magnitude
            elif self.target == "pos_y":
                b.position[1] += self.magnitude
            elif self.target == "vel_x":
                b.velocity[0] += self.magnitude
            elif self.target == "vel_y":
                b.velocity[1] += self.magnitude
        return new_bodies

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body_index": self.body_index,
            "target": self.target,
            "magnitude": self.magnitude
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerturbationConfig':
        return cls(
            body_index=int(data.get("body_index", 0)),
            target=str(data.get("target", "pos_x")),
            magnitude=float(data.get("magnitude", 1e-4))
        )


class DualUniverseSystem:
    """
    Manages Universe A and Universe B.
    Integrates both using Velocity Verlet and records history of Euclidean divergence D(t).
    """
    def __init__(self, base_bodies: List[Body], G: float = 1.0, perturbation: PerturbationConfig = None):
        if perturbation is None:
            perturbation = PerturbationConfig()

        self.base_bodies = [b.copy() for b in base_bodies]
        self.G = float(G)
        self.perturbation = perturbation

        # Universe A (original)
        self.universe_A = NBodySystem(self.base_bodies, G=self.G)

        # Universe B (perturbed)
        perturbed_bodies = self.perturbation.apply(self.base_bodies)
        self.universe_B = NBodySystem(perturbed_bodies, G=self.G)

        # History tracking
        self.time_history: List[float] = []
        self.divergence_history: List[float] = []
        self.ftle_history: List[float] = []
        # Optional manual starting positions for Universe B only.
        # Universe A always remains the preset baseline.
        self.custom_B_positions = None

        # Record initial condition (t=0)
        self._record_history()

    def reset(self):
        """Resets both universes to their initial states."""
        self.universe_A = NBodySystem(self.base_bodies, G=self.G)
        perturbed_bodies = self.perturbation.apply(self.base_bodies)
        self.universe_B = NBodySystem(perturbed_bodies, G=self.G)
        if self.custom_B_positions is not None:
            self.universe_B.set_positions(self.custom_B_positions)

        self.time_history.clear()
        self.divergence_history.clear()
        self.ftle_history.clear()
        self._record_history()

    def set_config(self, base_bodies: List[Body], G: float, perturbation: PerturbationConfig):
        """Updates setup and resets the simulation state."""
        self.base_bodies = [b.copy() for b in base_bodies]
        self.G = float(G)
        self.perturbation = perturbation
        self.custom_B_positions = None
        self.reset()

    def set_custom_B_positions(self, positions: np.ndarray):
        """Set manual starting positions for Universe B only and reset both runs."""
        positions = np.asarray(positions, dtype=np.float64)
        if positions.shape != (len(self.base_bodies), 2):
            raise ValueError("Custom Universe B positions must have shape (3, 2).")
        if not np.all(np.isfinite(positions)):
            raise ValueError("Custom Universe B positions must be finite.")
        self.custom_B_positions = positions.copy()
        self.reset()

    def clear_custom_B_positions(self):
        """Return Universe B to its preset perturbation-based initial positions."""
        self.custom_B_positions = None
        self.reset()

    def get_initial_B_positions(self) -> np.ndarray:
        """Return the actual initial positions used by Universe B."""
        if self.custom_B_positions is not None:
            return self.custom_B_positions.copy()
        return np.array([b.position for b in self.perturbation.apply(self.base_bodies)], dtype=np.float64)

    def step(self, dt: float):
        """Advances Universe A and Universe B by timestep dt."""
        VelocityVerletIntegrator.step(self.universe_A, dt)
        VelocityVerletIntegrator.step(self.universe_B, dt)
        self._record_history()

    def get_divergence(self) -> float:
        """
        Calculates positional divergence D(t) = sqrt( sum_i |r_A,i - r_B,i|^2 )
        """
        pos_A = self.universe_A.get_positions()
        pos_B = self.universe_B.get_positions()
        diff = pos_A - pos_B
        return float(np.sqrt(np.sum(diff ** 2)))

    def get_ftle(self) -> float:
        """
        Calculates Finite-Time Lyapunov Exponent / growth rate:
        lambda(t) = (1 / t) * ln( D(t) / D(0) ) in units of time^-1.
        """
        if not self.divergence_history or self.universe_A.time <= 1e-12:
            return 0.0

        d0 = max(self.divergence_history[0], 1e-15)
        dt_curr = max(self.divergence_history[-1], 1e-15)
        t = self.universe_A.time

        return float((1.0 / t) * np.log(dt_curr / d0))

    def _record_history(self):
        """Records current time, divergence, and FTLE."""
        d = self.get_divergence()
        t = self.universe_A.time
        self.time_history.append(t)
        self.divergence_history.append(d)
        ftle = self.get_ftle()
        self.ftle_history.append(ftle)
