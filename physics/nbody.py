"""
Core N-body dynamics module for Orbital Echo.
Calculates Newtonian gravitational accelerations with zero artificial softening.
"""

import numpy as np
from typing import List, Dict, Any, Tuple

class Body:
    """Represents a celestial body in the simulation."""
    def __init__(
        self,
        name: str,
        mass: float,
        position: np.ndarray,
        velocity: np.ndarray,
        color: Tuple[int, int, int] = (255, 255, 255),
        radius: float = 80.0
    ):
        self.name = str(name)
        self.mass = float(mass)
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity, dtype=np.float64)
        self.color = tuple(color)
        self.radius = float(radius)

    def copy(self) -> 'Body':
        return Body(
            name=self.name,
            mass=self.mass,
            position=self.position.copy(),
            velocity=self.velocity.copy(),
            color=self.color,
            radius=self.radius
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mass": self.mass,
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "color": list(self.color),
            "radius": self.radius
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Body':
        return cls(
            name=data["name"],
            mass=data["mass"],
            position=np.array(data["position"], dtype=np.float64),
            velocity=np.array(data["velocity"], dtype=np.float64),
            color=tuple(data.get("color", [255, 255, 255])),
            radius=float(data.get("radius", 80.0))
        )


class NBodySystem:
    """
    Simulates a system of N celestial bodies interacting via Newtonian gravity.
    No artificial softening is used (epsilon = 0.0).
    """
    def __init__(self, bodies: List[Body], G: float = 1.0):
        self.bodies = [b.copy() for b in bodies]
        self.G = float(G)
        self.time = 0.0

    def copy(self) -> 'NBodySystem':
        sys = NBodySystem([b.copy() for b in self.bodies], G=self.G)
        sys.time = self.time
        return sys

    def get_positions(self) -> np.ndarray:
        """Returns Nx2 matrix of body positions."""
        return np.array([b.position for b in self.bodies], dtype=np.float64)

    def get_velocities(self) -> np.ndarray:
        """Returns Nx2 matrix of body velocities."""
        return np.array([b.velocity for b in self.bodies], dtype=np.float64)

    def get_masses(self) -> np.ndarray:
        """Returns N-length array of body masses."""
        return np.array([b.mass for b in self.bodies], dtype=np.float64)

    def set_positions(self, pos: np.ndarray):
        for i, b in enumerate(self.bodies):
            b.position = pos[i].copy()

    def set_velocities(self, vel: np.ndarray):
        for i, b in enumerate(self.bodies):
            b.velocity = vel[i].copy()

    def compute_accelerations(self, positions: np.ndarray = None) -> np.ndarray:
        """
        Calculates acceleration vectors for all bodies using Newtonian gravity:
        a_i = G * sum_{j != i} m_j * (r_j - r_i) / |r_j - r_i|^3

        Zero artificial softening (epsilon = 0).
        """
        if positions is None:
            positions = self.get_positions()

        n = len(self.bodies)
        accelerations = np.zeros((n, 2), dtype=np.float64)
        masses = self.get_masses()

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                diff = positions[j] - positions[i]
                dist_sq = np.dot(diff, diff)
                dist = np.sqrt(dist_sq)

                # Direct distance without softening; protect from exact floating point 0
                if dist > 1e-15:
                    accelerations[i] += self.G * masses[j] * diff / (dist_sq * dist)

        return accelerations
