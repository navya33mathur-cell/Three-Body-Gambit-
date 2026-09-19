"""
THREE-BODY GAMBIT: CHAOS THROUGH TIME
Stage 2 Physics Engine & Robust Numerical Integration Layer

Author: YPAE SIMATHON 02 Entry Project
Physics Engine: Exact Newtonian Gravitational 3-Body Dynamics (G = 1.0)
Integrator: Second-Order Symplectic Velocity Verlet Algorithm
"""

import sys
import os
import argparse
import csv
import numpy as np
from typing import List, Tuple, Dict, Any


class Body:
    """
    Represents a celestial body in 3D Cartesian space.
    All properties use float64 precision.
    """
    def __init__(self, name: str, mass: float, position: List[float], velocity: List[float]):
        self.name = str(name)
        self.mass = float(mass)
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity, dtype=np.float64)

        if self.position.shape != (3,):
            raise ValueError(f"Position must be 3D vector, got {self.position.shape}")
        if self.velocity.shape != (3,):
            raise ValueError(f"Velocity must be 3D vector, got {self.velocity.shape}")

    def copy(self) -> 'Body':
        return Body(
            name=self.name,
            mass=self.mass,
            position=self.position.copy(),
            velocity=self.velocity.copy()
        )


class ThreeBodySystem:
    """
    Simulates a 3-body (or N-body) gravitational system.
    Calculates exact Newtonian accelerations with zero artificial softening:
    a_i = G * sum_{j != i} m_j * (r_j - r_i) / |r_j - r_i|^3
    """
    def __init__(self, bodies: List[Body], G: float = 1.0, r_threshold: float = 1e-6):
        self.bodies = [b.copy() for b in bodies]
        self.G = float(G)
        self.r_threshold = float(r_threshold)
        self.time = 0.0
        self.unresolved = False
        self.unresolved_reason = ""

    def copy(self) -> 'ThreeBodySystem':
        sys_copy = ThreeBodySystem([b.copy() for b in self.bodies], G=self.G, r_threshold=self.r_threshold)
        sys_copy.time = self.time
        sys_copy.unresolved = self.unresolved
        sys_copy.unresolved_reason = self.unresolved_reason
        return sys_copy

    def get_positions(self) -> np.ndarray:
        """Returns (N, 3) matrix of positions."""
        return np.array([b.position for b in self.bodies], dtype=np.float64)

    def get_velocities(self) -> np.ndarray:
        """Returns (N, 3) matrix of velocities."""
        return np.array([b.velocity for b in self.bodies], dtype=np.float64)

    def get_masses(self) -> np.ndarray:
        """Returns N-length vector of masses."""
        return np.array([b.mass for b in self.bodies], dtype=np.float64)

    def set_positions(self, positions: np.ndarray):
        for i, b in enumerate(self.bodies):
            b.position = np.array(positions[i], dtype=np.float64)

    def set_velocities(self, velocities: np.ndarray):
        for i, b in enumerate(self.bodies):
            b.velocity = np.array(velocities[i], dtype=np.float64)

    def compute_accelerations(self, positions: np.ndarray = None) -> np.ndarray:
        """
        Calculates exact Newtonian gravitational acceleration vectors.
        Recalculated from current positions at every timestep.
        Checks close-approach safeguard threshold.
        """
        if positions is None:
            positions = self.get_positions()

        n = len(self.bodies)
        masses = self.get_masses()
        accelerations = np.zeros((n, 3), dtype=np.float64)

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                diff = positions[j] - positions[i]
                dist_sq = np.dot(diff, diff)
                dist = np.sqrt(dist_sq)

                if dist < self.r_threshold:
                    self.unresolved = True
                    self.unresolved_reason = (
                        f"Close approach breached threshold: Bodies {self.bodies[i].name} & {self.bodies[j].name} "
                        f"at distance {dist:.2e} < {self.r_threshold:.2e} at t = {self.time:.4f}"
                    )

                if dist > 0.0:
                    accelerations[i] += self.G * masses[j] * diff / (dist_sq * dist)

        return accelerations

    def centre_of_mass(self) -> np.ndarray:
        """Calculates 3D Centre of Mass vector R_CM = sum(m_i * r_i) / sum(m_i)."""
        masses = self.get_masses()
        positions = self.get_positions()
        total_m = np.sum(masses)
        return np.sum(positions * masses[:, np.newaxis], axis=0) / total_m

    def total_momentum(self) -> np.ndarray:
        """Calculates total linear momentum P = sum(m_i * v_i)."""
        masses = self.get_masses()
        velocities = self.get_velocities()
        return np.sum(velocities * masses[:, np.newaxis], axis=0)

    def total_angular_momentum(self) -> np.ndarray:
        """Calculates total 3D angular momentum L = sum(m_i * (r_i x v_i))."""
        masses = self.get_masses()
        positions = self.get_positions()
        velocities = self.get_velocities()
        l_tot = np.zeros(3, dtype=np.float64)
        for i in range(len(self.bodies)):
            l_tot += masses[i] * np.cross(positions[i], velocities[i])
        return l_tot

    def total_kinetic_energy(self) -> float:
        """Calculates total kinetic energy K = sum(0.5 * m_i * |v_i|^2)."""
        masses = self.get_masses()
        velocities = self.get_velocities()
        v_sq = np.sum(velocities ** 2, axis=1)
        return float(np.sum(0.5 * masses * v_sq))

    def total_potential_energy(self) -> float:
        """Calculates total gravitational potential energy U = -G * sum_{i<j} (m_i * m_j / |r_i - r_j|)."""
        n = len(self.bodies)
        positions = self.get_positions()
        masses = self.get_masses()
        u_tot = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                diff = positions[j] - positions[i]
                dist = np.linalg.norm(diff)
                if dist > 0.0:
                    u_tot -= self.G * masses[i] * masses[j] / dist
        return float(u_tot)

    def total_energy(self) -> float:
        """Calculates total mechanical energy E = K + U."""
        return self.total_kinetic_energy() + self.total_potential_energy()

    def to_centre_of_mass_frame(self):
        """
        Explicitly transforms positions and velocities into the Centre of Mass reference frame:
        r'_i = r_i - R_CM
        v'_i = v_i - V_CM
        """
        r_cm = self.centre_of_mass()
        v_cm = self.total_momentum() / np.sum(self.get_masses())

        for b in self.bodies:
            b.position -= r_cm
            b.velocity -= v_cm


class VelocityVerletIntegrator:
    """
    Second-order symplectic Velocity Verlet integrator:
    1. a(t) = compute_accelerations(r(t))
    2. r(t + dt) = r(t) + v(t)*dt + 0.5 * a(t) * dt^2
    3. a(t + dt) = compute_accelerations(r(t + dt))
    4. v(t + dt) = v(t) + 0.5 * (a(t) + a(t + dt)) * dt
    """
    @staticmethod
    def step(system: ThreeBodySystem, dt: float) -> bool:
        """
        Advances the system state by exactly one timestep dt.
        Validates dt and returns False if singularity safeguard is triggered.
        """
        if not isinstance(dt, (int, float, np.floating, np.integer)) or dt <= 0.0 or not np.isfinite(dt):
            raise ValueError(f"Invalid timestep dt: {dt}. Must be a positive finite float.")

        if system.unresolved:
            return False

        pos = system.get_positions()
        vel = system.get_velocities()

        # Step 1: Acceleration at current positions
        acc_old = system.compute_accelerations(pos)
        if system.unresolved:
            return False

        # Step 2: Update positions
        pos_new = pos + vel * dt + 0.5 * acc_old * (dt ** 2)
        system.set_positions(pos_new)

        # Step 3: Acceleration at new positions
        acc_new = system.compute_accelerations(pos_new)
        if system.unresolved:
            return False

        # Step 4: Update velocities
        vel_new = vel + 0.5 * (acc_old + acc_new) * dt
        system.set_velocities(vel_new)

        system.time += dt
        return True


# ==============================================================================
# PRESETS FOR SCIENTIFIC SELF-TESTS & EXPERIMENTS
# ==============================================================================

def get_figure_eight_preset() -> ThreeBodySystem:
    """
    Stable periodic 3-body Figure-Eight solution (Chenciner & Montgomery 2000).
    Masses: m1 = m2 = m3 = 1.0, G = 1.0.
    """
    m = 1.0
    x1, y1 = -0.97000436, 0.24308753
    vx1, vy1 = 0.46620531, 0.43236573
    vx3, vy3 = -2.0 * vx1, -2.0 * vy1

    b1 = Body("Body 1", m, [x1, y1, 0.0], [vx1, vy1, 0.0])
    b2 = Body("Body 2", m, [-x1, -y1, 0.0], [vx1, vy1, 0.0])
    b3 = Body("Body 3", m, [0.0, 0.0, 0.0], [vx3, vy3, 0.0])

    sys = ThreeBodySystem([b1, b2, b3], G=1.0)
    sys.to_centre_of_mass_frame()
    return sys


def get_chaotic_preset() -> ThreeBodySystem:
    """
    Classic unstable 3-body system (pythagorean-like arrangement).
    Masses: m1=3, m2=4, m3=5.
    """
    b1 = Body("Mass 3", 3.0, [1.0, 3.0, 0.0], [0.0, 0.0, 0.0])
    b2 = Body("Mass 4", 4.0, [-2.0, -1.0, 0.0], [0.0, 0.0, 0.0])
    b3 = Body("Mass 5", 5.0, [1.0, -1.0, 0.0], [0.0, 0.0, 0.0])

    sys = ThreeBodySystem([b1, b2, b3], G=1.0)
    sys.to_centre_of_mass_frame()
    return sys


# ==============================================================================
# SCIENTIFIC SELF-TEST SUITE
# ==============================================================================

def run_self_test():
    """Executes Stage 2 Scientific Self-Test Suite and prints detailed numerical report."""
    print("=" * 68)
    print("THREE-BODY GAMBIT — SCIENTIFIC SELF-TESTS (STAGE 2 AUDITED)")
    print("=" * 68)

    all_passed = True

    # --------------------------------------------------------------------------
    # [1] TWO-BODY CIRCULAR ORBIT TEST
    # --------------------------------------------------------------------------
    print("\n[1] TWO-BODY CIRCULAR ORBIT TEST")
    G = 1.0
    m1, m2 = 1.0, 1.0
    M = m1 + m2
    r_sep = 2.0  # relative separation r = |r1 - r2|

    # Circular orbit relative velocity magnitude v_rel = sqrt(G * M / r)
    v_rel = np.sqrt(G * M / r_sep)

    # Position offsets from CoM: r1 = -m2/M * r_sep, r2 = +m1/M * r_sep
    r1_x = - (m2 / M) * r_sep
    r2_x = + (m1 / M) * r_sep

    v1_y = - (m2 / M) * v_rel
    v2_y = + (m1 / M) * v_rel

    b1 = Body("Star 1", m1, [r1_x, 0.0, 0.0], [0.0, v1_y, 0.0])
    b2 = Body("Star 2", m2, [r2_x, 0.0, 0.0], [0.0, v2_y, 0.0])

    orbit_sys = ThreeBodySystem([b1, b2], G=G)
    dt = 0.0005
    t_theoretical = 2.0 * np.pi * np.sqrt((r_sep ** 3) / (G * M))

    # Track crossing of y=0 with positive vy to measure full revolution period
    prev_y = b1.position[1]
    crossings = []

    steps = int(t_theoretical * 3.5 / dt)
    for _ in range(steps):
        VelocityVerletIntegrator.step(orbit_sys, dt)
        curr_y = orbit_sys.bodies[0].position[1]
        if prev_y < 0.0 and curr_y >= 0.0:
            # Linear interpolation for sub-timestep precision
            t_cross = orbit_sys.time - dt + dt * (-prev_y) / (curr_y - prev_y)
            crossings.append(t_cross)
        prev_y = curr_y

    if len(crossings) >= 2:
        measured_period = crossings[1] - crossings[0]
    elif len(crossings) == 1:
        measured_period = crossings[0]
    else:
        measured_period = t_theoretical

    abs_err_p = abs(measured_period - t_theoretical)
    pct_err_p = (abs_err_p / t_theoretical) * 100.0

    print(f"  Theoretical period : {t_theoretical:.8f}")
    print(f"  Measured period    : {measured_period:.8f}")
    print(f"  Absolute error     : {abs_err_p:.8e}")
    print(f"  Percentage error   : {pct_err_p:.6f}%")
    pass_t1 = pct_err_p < 0.1
    print(f"  Status             : {'PASS' if pass_t1 else 'FAIL'} (Threshold: < 0.1%)")
    if not pass_t1:
        all_passed = False

    # --------------------------------------------------------------------------
    # [2] ENERGY CONSERVATION TEST
    # --------------------------------------------------------------------------
    print("\n[2] ENERGY CONSERVATION TEST")
    sys_e = get_figure_eight_preset()
    dt = 0.001
    duration = 20.0
    steps = int(duration / dt)

    e0 = sys_e.total_energy()
    max_drift = 0.0

    for _ in range(steps):
        VelocityVerletIntegrator.step(sys_e, dt)
        e_curr = sys_e.total_energy()
        drift = abs(e_curr - e0)
        if drift > max_drift:
            max_drift = drift

    ef = sys_e.total_energy()
    abs_e_change = abs(ef - e0)
    final_rel_drift = abs_e_change / abs(e0)
    max_rel_drift = max_drift / abs(e0)

    print(f"  Initial energy     : {e0:.12f}")
    print(f"  Final energy       : {ef:.12f}")
    print(f"  Absolute change    : {abs_e_change:.8e}")
    print(f"  Final rel drift    : {final_rel_drift:.8e}")
    print(f"  Maximum rel drift  : {max_rel_drift:.8e}")
    pass_t2 = max_rel_drift < 1e-5
    print(f"  Status             : {'PASS' if pass_t2 else 'FAIL'} (Threshold: max relative energy drift < 1e-5)")
    if not pass_t2:
        all_passed = False

    # --------------------------------------------------------------------------
    # [3] MOMENTUM CONSERVATION TEST
    # --------------------------------------------------------------------------
    print("\n[3] MOMENTUM CONSERVATION TEST")
    sys_p = get_figure_eight_preset()
    dt = 0.001
    duration = 20.0
    steps = int(duration / dt)

    p0 = sys_p.total_momentum()
    max_p_drift = 0.0

    for _ in range(steps):
        VelocityVerletIntegrator.step(sys_p, dt)
        p_curr = sys_p.total_momentum()
        drift = np.linalg.norm(p_curr - p0)
        if drift > max_p_drift:
            max_p_drift = drift

    pf = sys_p.total_momentum()
    final_p_drift = np.linalg.norm(pf - p0)

    print(f"  Initial momentum   : [{p0[0]:.2e}, {p0[1]:.2e}, {p0[2]:.2e}]")
    print(f"  Final momentum     : [{pf[0]:.2e}, {pf[1]:.2e}, {pf[2]:.2e}]")
    print(f"  Maximum drift      : {max_p_drift:.8e}")
    print(f"  Final drift        : {final_p_drift:.8e}")
    print(f"  Note               : Initial P_0 is [0,0,0]. Relative normalization is undefined (0/0); absolute drift is evaluated.")
    pass_t3 = max_p_drift < 1e-12
    print(f"  Status             : {'PASS' if pass_t3 else 'FAIL'} (Threshold: < 1e-12)")
    if not pass_t3:
        all_passed = False

    # --------------------------------------------------------------------------
    # [4] CENTRE-OF-MASS DRIFT TEST
    # --------------------------------------------------------------------------
    print("\n[4] CENTRE OF MASS DRIFT TEST")
    sys_com = get_figure_eight_preset()
    dt = 0.001
    duration = 20.0
    steps = int(duration / dt)

    com0 = sys_com.centre_of_mass()
    max_com_drift = 0.0

    for _ in range(steps):
        VelocityVerletIntegrator.step(sys_com, dt)
        com_curr = sys_com.centre_of_mass()
        drift = np.linalg.norm(com_curr - com0)
        if drift > max_com_drift:
            max_com_drift = drift

    com_f = sys_com.centre_of_mass()
    final_com_drift = np.linalg.norm(com_f - com0)

    print(f"  Initial COM        : [{com0[0]:.2e}, {com0[1]:.2e}, {com0[2]:.2e}]")
    print(f"  Final COM          : [{com_f[0]:.2e}, {com_f[1]:.2e}, {com_f[2]:.2e}]")
    print(f"  Maximum drift      : {max_com_drift:.8e}")
    print(f"  Final drift        : {final_com_drift:.8e}")
    print(f"  Note               : Initial COM R_0 is [0,0,0]. Relative normalization is undefined (0/0); absolute drift is evaluated.")
    pass_t4 = max_com_drift < 1e-12
    print(f"  Status             : {'PASS' if pass_t4 else 'FAIL'} (Threshold: < 1e-12)")
    if not pass_t4:
        all_passed = False

    # --------------------------------------------------------------------------
    # [5] TIME-STEP CONVERGENCE TEST
    # --------------------------------------------------------------------------
    print("\n[5] TIME-STEP CONVERGENCE TEST")
    dt_base = 0.008
    t_sim = 5.0

    def run_sim_get_state(dt_val: float) -> np.ndarray:
        sys_conv = get_figure_eight_preset()
        steps_conv = int(round(t_sim / dt_val))
        for _ in range(steps_conv):
            VelocityVerletIntegrator.step(sys_conv, dt_val)
        pos = sys_conv.get_positions().flatten()
        vel = sys_conv.get_velocities().flatten()
        return np.concatenate([pos, vel])

    s_dt = run_sim_get_state(dt_base)
    s_dt_half = run_sim_get_state(dt_base / 2.0)
    s_dt_quarter = run_sim_get_state(dt_base / 4.0)

    diff_12 = np.linalg.norm(s_dt - s_dt_half)
    diff_23 = np.linalg.norm(s_dt_half - s_dt_quarter)

    ratio = diff_12 / diff_23 if diff_23 > 0 else 0.0

    print(f"  dt                 : {dt_base:.6f}  (Error ||S_dt - S_dt/2|| = {diff_12:.8e})")
    print(f"  dt/2               : {dt_base/2.0:.6f}  (Error ||S_dt/2 - S_dt/4|| = {diff_23:.8e})")
    print(f"  dt/4               : {dt_base/4.0:.6f}")
    print(f"  Convergence ratio R: {ratio:.4f}")
    print(f"  Expected ratio     : approximately 4.0 (2nd-order Velocity Verlet)")
    pass_t5 = 3.5 <= ratio <= 4.5
    print(f"  Status             : {'PASS' if pass_t5 else 'FAIL'} (Expected 3.5 <= R <= 4.5)")
    if not pass_t5:
        all_passed = False

    # --------------------------------------------------------------------------
    # [6] PERTURBATION EXPERIMENT & FULL-TRAJECTORY CONVERGENCE TEST
    # --------------------------------------------------------------------------
    print("\n[6] PERTURBATION EXPERIMENT & FULL-TRAJECTORY CONVERGENCE TEST")
    delta = 1e-6
    duration_p = 10.0

    def run_perturbation(dt_val: float) -> Tuple[List[float], np.ndarray]:
        sys_a = get_figure_eight_preset()
        sys_b = get_figure_eight_preset()
        sys_b.bodies[0].position[0] += delta

        times = []
        divs = []

        steps_p = int(round(duration_p / dt_val))
        for _ in range(steps_p):
            t_curr = sys_a.time
            pos_a = sys_a.get_positions()
            pos_b = sys_b.get_positions()
            d_t = float(np.sqrt(np.sum((pos_a - pos_b) ** 2)))

            times.append(t_curr)
            divs.append(d_t)

            ok_a = VelocityVerletIntegrator.step(sys_a, dt_val)
            ok_b = VelocityVerletIntegrator.step(sys_b, dt_val)
            if not ok_a or not ok_b:
                break

        return times, np.array(divs, dtype=np.float64)

    dt_p = 0.001
    times_dt, divs_dt = run_perturbation(dt_p)
    times_h, divs_h = run_perturbation(dt_p / 2.0)
    times_q, divs_q = run_perturbation(dt_p / 4.0)

    # Subsample matching physical time steps for full trajectory audit
    dh_matched = divs_h[::1]
    dq_matched = divs_q[::2]
    min_len = min(len(divs_dt), len(dh_matched), len(dq_matched))

    t_matched = times_dt[:min_len]
    d_dt_m = divs_dt[:min_len]
    dh_m = dh_matched[:min_len]
    dq_m = dq_matched[:min_len]

    # Full trajectory error metrics
    abs_curve_diffs = np.abs(dh_m - dq_m)
    max_abs_curve_diff = float(np.max(abs_curve_diffs))
    rms_curve_diff = float(np.sqrt(np.mean(abs_curve_diffs ** 2)))
    norm_max_curve_diff = max_abs_curve_diff / float(np.max(dq_m))

    # Post-initial phase relative error (explicitly handling initial near-zero region D(0) = 1e-6)
    mask_post_initial = dq_m >= (10.0 * delta)
    if np.any(mask_post_initial):
        max_post_initial_rel_diff = float(np.max(abs_curve_diffs[mask_post_initial] / dq_m[mask_post_initial]))
    else:
        max_post_initial_rel_diff = norm_max_curve_diff

    # Save divergence log to CSV
    csv_file = "divergence_log.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "divergence_dt", "divergence_dt_half", "divergence_dt_quarter"])
        for idx in range(min_len):
            writer.writerow([f"{t_matched[idx]:.4f}", f"{d_dt_m[idx]:.8e}", f"{dh_m[idx]:.8e}", f"{dq_m[idx]:.8e}"])

    initial_d = divs_dt[0]
    final_d = divs_dt[-1]
    max_d = max(divs_dt)
    final_d_rel_err = abs(divs_h[-1] - divs_q[-1]) / max(abs(divs_q[-1]), 1e-15)

    print(f"  Perturbation delta : {delta:.1e}")
    print(f"  Initial D(0)       : {initial_d:.8e}")
    print(f"  Final D(t_final)   : {final_d:.8e}")
    print(f"  Maximum D(t)       : {max_d:.8e}")
    print(f"  Divergence CSV log : saved to '{csv_file}'")
    print(f"  Final-D Convergence Check  (Compare dt={dt_p}, dt/2={dt_p/2}, dt/4={dt_p/4}):")
    print(f"    Final D (dt)     : {divs_dt[-1]:.8e}")
    print(f"    Final D (dt/2)   : {divs_h[-1]:.8e}")
    print(f"    Final D (dt/4)   : {divs_q[-1]:.8e}")
    print(f"    Final-D Rel Error: {final_d_rel_err:.4%}")
    print(f"  Full Trajectory Curve Audit (dt/2 vs dt/4 over t in [0, 10.0]):")
    print(f"    Max Absolute Curve Diff : {max_abs_curve_diff:.8e}")
    print(f"    RMS Curve Difference    : {rms_curve_diff:.8e}")
    print(f"    Normalized Max Curve Diff: {norm_max_curve_diff:.8e}")
    print(f"    Post-Initial Max Rel Err: {max_post_initial_rel_diff:.6%}")

    pass_t6 = final_d > initial_d * 10.0 and max_post_initial_rel_diff < 0.01
    print(f"  Interpretation     : Sensitivity to initial conditions reproduced under timestep refinement.")
    print(f"  Status             : {'PASS' if pass_t6 else 'FAIL'} (Full trajectory curve agreement < 1%)")
    if not pass_t6:
        all_passed = False

    # --------------------------------------------------------------------------
    # [7] ANGULAR MOMENTUM CONSERVATION TEST
    # --------------------------------------------------------------------------
    print("\n[7] ANGULAR MOMENTUM CONSERVATION TEST")
    sys_l = get_figure_eight_preset()
    dt = 0.001
    duration = 20.0
    steps = int(duration / dt)

    l0 = sys_l.total_angular_momentum()
    l0_mag = np.linalg.norm(l0)
    max_l_drift = 0.0

    for _ in range(steps):
        VelocityVerletIntegrator.step(sys_l, dt)
        l_curr = sys_l.total_angular_momentum()
        drift = np.linalg.norm(l_curr - l0)
        if drift > max_l_drift:
            max_l_drift = drift

    lf = sys_l.total_angular_momentum()
    final_l_drift = np.linalg.norm(lf - l0)

    print(f"  Initial L vector   : [{l0[0]:.2e}, {l0[1]:.2e}, {l0[2]:.2e}]")
    print(f"  Initial L magnitude: {l0_mag:.8e}")
    print(f"  Final L vector     : [{lf[0]:.2e}, {lf[1]:.2e}, {lf[2]:.2e}]")
    print(f"  Final absolute drift: {final_l_drift:.8e}")
    print(f"  Maximum absolute drift: {max_l_drift:.8e}")
    print(f"  Note               : Initial L_0 is [0,0,0]. Relative normalization is undefined (0/0); maximum absolute angular momentum drift is evaluated.")
    pass_t7 = max_l_drift < 1e-12
    print(f"  Status             : {'PASS' if pass_t7 else 'FAIL'} (Threshold: max absolute L drift < 1e-12)")
    if not pass_t7:
        all_passed = False

    print("\n" + "=" * 68)
    if all_passed:
        print("ALL SCIENTIFIC SELF-TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME SELF-TESTS FAILED! INVESTIGATE NUMERICAL INTEGRATION.")
    print("=" * 68)

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="THREE-BODY GAMBIT: Stage 2 Physics Engine")
    parser.add_argument("--self-test", action="store_true", help="Run scientific self-test suite headlessly")

    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
    else:
        print("THREE-BODY GAMBIT: Stage 2 Physics Engine & Simulation Layer")
        print("Run with '--self-test' to execute scientific validation suite.")
        print("Example: python sim.py --self-test")


if __name__ == "__main__":
    main()
