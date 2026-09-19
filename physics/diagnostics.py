"""
Scientific diagnostics module for calculating physical invariants, conservation metrics,
minimum separations, encounter timescales, and timestep safety ratios.
"""

import numpy as np
from typing import Dict, Any, Tuple
from physics.nbody import NBodySystem

class ScientificDiagnostics:
    """Calculates diagnostics and conservation quantities for an N-body system."""

    @staticmethod
    def calculate_kinetic_energy(system: NBodySystem) -> float:
        """E_k = 0.5 * sum(m_i * |v_i|^2)"""
        velocities = system.get_velocities()
        masses = system.get_masses()
        v_sq = np.sum(velocities ** 2, axis=1)
        return float(0.5 * np.sum(masses * v_sq))

    @staticmethod
    def calculate_potential_energy(system: NBodySystem) -> float:
        """E_p = -G * sum_{i < j} (m_i * m_j / |r_i - r_j|)"""
        positions = system.get_positions()
        masses = system.get_masses()
        n = len(system.bodies)
        ep = 0.0

        for i in range(n):
            for j in range(i + 1, n):
                diff = positions[i] - positions[j]
                dist = np.linalg.norm(diff)
                if dist > 1e-15:
                    ep -= system.G * masses[i] * masses[j] / dist

        return float(ep)

    @staticmethod
    def calculate_total_energy(system: NBodySystem) -> float:
        """E_total = E_k + E_p"""
        return (
            ScientificDiagnostics.calculate_kinetic_energy(system) +
            ScientificDiagnostics.calculate_potential_energy(system)
        )

    @staticmethod
    def calculate_linear_momentum(system: NBodySystem) -> np.ndarray:
        """P = sum(m_i * v_i)"""
        velocities = system.get_velocities()
        masses = system.get_masses()
        return np.sum(masses[:, np.newaxis] * velocities, axis=0)

    @staticmethod
    def calculate_centre_of_mass(system: NBodySystem) -> np.ndarray:
        """R_cm = sum(m_i * r_i) / sum(m_i)"""
        positions = system.get_positions()
        masses = system.get_masses()
        total_mass = np.sum(masses)
        if total_mass < 1e-15:
            return np.zeros(2)
        return np.sum(masses[:, np.newaxis] * positions, axis=0) / total_mass

    @staticmethod
    def calculate_angular_momentum(system: NBodySystem) -> float:
        """L_z = sum(m_i * (x_i * v_y,i - y_i * v_x,i))"""
        positions = system.get_positions()
        velocities = system.get_velocities()
        masses = system.get_masses()

        # 2D cross product r x v = x * vy - y * vx
        cross = positions[:, 0] * velocities[:, 1] - positions[:, 1] * velocities[:, 0]
        return float(np.sum(masses * cross))

    @staticmethod
    def calculate_closest_encounter(system: NBodySystem) -> Tuple[float, float, Tuple[int, int]]:
        """
        Calculates minimum pairwise separation r_min, corresponding encounter timescale tau,
        and body pair indices (i, j).

        tau = sqrt( r_min^3 / [ G * (m_i + m_j) ] )
        """
        positions = system.get_positions()
        masses = system.get_masses()
        n = len(system.bodies)

        min_dist = float('inf')
        pair = (0, 1)
        pair_mass_sum = masses[0] + masses[1] if n >= 2 else 1.0

        for i in range(n):
            for j in range(i + 1, n):
                dist = float(np.linalg.norm(positions[i] - positions[j]))
                if dist < min_dist:
                    min_dist = dist
                    pair = (i, j)
                    pair_mass_sum = float(masses[i] + masses[j])

        if min_dist < 1e-15 or system.G <= 0:
            tau = 1e-15
        else:
            tau = float(np.sqrt((min_dist ** 3) / (system.G * pair_mass_sum)))

        return min_dist, tau, pair

    @classmethod
    def calculate_all(cls, system: NBodySystem, dt: float) -> Dict[str, Any]:
        """Returns comprehensive diagnostic dictionary."""
        ek = cls.calculate_kinetic_energy(system)
        ep = cls.calculate_potential_energy(system)
        e_total = ek + ep
        momentum = cls.calculate_linear_momentum(system)
        com = cls.calculate_centre_of_mass(system)
        ang_mom = cls.calculate_angular_momentum(system)
        r_min, tau, (i, j) = cls.calculate_closest_encounter(system)
        dt_tau_ratio = dt / tau if tau > 0 else float('inf')
        is_resolved = dt_tau_ratio <= 0.10

        return {
            "kinetic_energy": ek,
            "potential_energy": ep,
            "total_energy": e_total,
            "linear_momentum": momentum,
            "momentum_magnitude": float(np.linalg.norm(momentum)),
            "centre_of_mass": com,
            "angular_momentum": ang_mom,
            "min_separation": r_min,
            "encounter_timescale": tau,
            "closest_pair": (i, j),
            "dt_tau_ratio": dt_tau_ratio,
            "is_resolved": is_resolved,
            "resolution_status": "RESOLVED" if is_resolved else "UNRESOLVED / NEEDS SMALLER TIMESTEP"
        }
