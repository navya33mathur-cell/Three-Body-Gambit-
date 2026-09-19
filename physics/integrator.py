"""
Velocity Verlet numerical integrator for N-body Newtonian physics.
Second-order symplectic integration scheme.
"""

import numpy as np
from physics.nbody import NBodySystem

class VelocityVerletIntegrator:
    """
    Implements Velocity Verlet integration algorithm for NBodySystem:
    1. r(t + dt) = r(t) + v(t)*dt + 0.5 * a(t) * dt^2
    2. a(t + dt) = compute_accelerations(r(t + dt))
    3. v(t + dt) = v(t) + 0.5 * (a(t) + a(t + dt)) * dt
    """

    @staticmethod
    def step(system: NBodySystem, dt: float):
        """
        Advances the physical system by one timestep dt using Velocity Verlet.
        """
        positions = system.get_positions()
        velocities = system.get_velocities()

        # Step 1: Compute initial accelerations a(t)
        acc_old = system.compute_accelerations(positions)

        # Step 2: Update positions r(t + dt)
        pos_new = positions + velocities * dt + 0.5 * acc_old * (dt ** 2)
        system.set_positions(pos_new)

        # Step 3: Compute new accelerations a(t + dt)
        acc_new = system.compute_accelerations(pos_new)

        # Step 4: Update velocities v(t + dt)
        vel_new = velocities + 0.5 * (acc_old + acc_new) * dt
        system.set_velocities(vel_new)

        # Advance simulation clock
        system.time += dt
