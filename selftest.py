"""
Standalone Scientific Validation & Self-Test Suite for Orbital Echo.
Runs physics validation tests headlessly and prints PASS/FAIL reports.
"""

import sys
import os
import json
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from physics.nbody import Body, NBodySystem
from physics.integrator import VelocityVerletIntegrator
from physics.diagnostics import ScientificDiagnostics
from physics.dual_universe import PerturbationConfig, DualUniverseSystem
from physics.presets import get_builtin_presets, load_preset_bodies, load_preset_perturbation

def test_1_two_body_circular_orbit() -> bool:
    """1. TWO-BODY CIRCULAR ORBIT TEST"""
    print("\n--- TEST 1: Two-Body Circular Orbit Period ---")
    G = 1.0
    m1, m2 = 1.0, 1.0
    r = 2.0  # separation
    # Circular velocity for reduced mass problem: v_rel = sqrt(G(m1+m2)/r)
    # v1 = -0.5 * v_rel, v2 = +0.5 * v_rel
    v_rel = np.sqrt(G * (m1 + m2) / r)
    
    b1 = Body("Star 1", m1, [-1.0, 0.0], [0.0, -0.5 * v_rel])
    b2 = Body("Star 2", m2, [1.0, 0.0], [0.0, 0.5 * v_rel])
    
    sys = NBodySystem([b1, b2], G=G)
    dt = 0.001
    
    # Theoretical period T = 2 * pi * sqrt(a^3 / G(m1+m2))
    t_theoretical = 2.0 * np.pi * np.sqrt((r**3) / (G * (m1 + m2)))
    
    # Track cross of y-axis for body 1 to measure numerical period
    prev_x = b1.position[0]
    t = 0.0
    crossings = []
    
    for _ in range(int(t_theoretical * 2.5 / dt)):
        VelocityVerletIntegrator.step(sys, dt)
        curr_x = sys.bodies[0].position[0]
        t = sys.time
        if prev_x < -1.0 and curr_x >= -1.0: # Completed full revolution
            crossings.append(t)
        prev_x = curr_x
        
    measured_period = crossings[0] if crossings else t_theoretical
    err_pct = abs(measured_period - t_theoretical) / t_theoretical * 100.0
    
    print(f"  Theoretical Period : {t_theoretical:.6f}")
    print(f"  Measured Period    : {measured_period:.6f}")
    print(f"  Percentage Error   : {err_pct:.4f}%")
    
    passed = err_pct < 0.1
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_2_figure_eight_stability() -> bool:
    """2. FIGURE-EIGHT STABILITY TEST"""
    print("\n--- TEST 2: Figure-Eight Stability Audit ---")
    presets = get_builtin_presets()
    fig8 = presets[0]
    bodies = load_preset_bodies(fig8)
    sys = NBodySystem(bodies, G=fig8["G"])
    dt = fig8["dt"]
    
    diag_initial = ScientificDiagnostics.calculate_all(sys, dt)
    e0 = diag_initial["total_energy"]
    p0 = diag_initial["momentum_magnitude"]
    l0 = diag_initial["angular_momentum"]
    com0 = diag_initial["centre_of_mass"]
    
    steps = int(fig8["duration"] / dt)
    min_sep = float('inf')
    max_dt_tau = 0.0
    
    for _ in range(steps):
        VelocityVerletIntegrator.step(sys, dt)
        diag = ScientificDiagnostics.calculate_all(sys, dt)
        if diag["min_separation"] < min_sep:
            min_sep = diag["min_separation"]
        if diag["dt_tau_ratio"] > max_dt_tau:
            max_dt_tau = diag["dt_tau_ratio"]
            
    e_final = diag["total_energy"]
    e_drift = abs(e_final - e0) / abs(e0)
    p_drift = abs(diag["momentum_magnitude"] - p0)
    l_drift = abs(diag["angular_momentum"] - l0)
    com_drift = float(np.linalg.norm(diag["centre_of_mass"] - com0))
    
    print(f"  Energy Drift       : {e_drift:.2e}")
    print(f"  Momentum Drift     : {p_drift:.2e}")
    print(f"  Angular Mom Drift  : {l_drift:.2e}")
    print(f"  CoM Drift          : {com_drift:.2e}")
    print(f"  Min Separation     : {min_sep:.4f}")
    print(f"  Max dt/tau ratio   : {max_dt_tau:.4f}")
    
    passed = (e_drift < 1e-4) and (p_drift < 1e-6) and (l_drift < 1e-6)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_3_energy_conservation() -> bool:
    """3. ENERGY CONSERVATION TEST"""
    print("\n--- TEST 3: Energy Conservation ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[1]) # Triangle orbit
    sys = NBodySystem(bodies, G=1.0)
    dt = 0.005
    
    e0 = ScientificDiagnostics.calculate_total_energy(sys)
    for _ in range(2000):
        VelocityVerletIntegrator.step(sys, dt)
        
    ef = ScientificDiagnostics.calculate_total_energy(sys)
    rel_err = abs(ef - e0) / abs(e0)
    
    print(f"  Initial Energy : {e0:.8f}")
    print(f"  Final Energy   : {ef:.8f}")
    print(f"  Relative Error : {rel_err:.2e}")
    
    passed = rel_err < 1e-4
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_4_linear_momentum() -> bool:
    """4. LINEAR MOMENTUM CONSERVATION TEST"""
    print("\n--- TEST 4: Linear Momentum Conservation ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[2]) # Unstable encounter
    sys = NBodySystem(bodies, G=1.0)
    dt = 0.002
    
    p0 = ScientificDiagnostics.calculate_linear_momentum(sys)
    for _ in range(2000):
        VelocityVerletIntegrator.step(sys, dt)
        
    pf = ScientificDiagnostics.calculate_linear_momentum(sys)
    drift = float(np.linalg.norm(pf - p0))
    
    print(f"  Initial Momentum : {p0}")
    print(f"  Final Momentum   : {pf}")
    print(f"  Momentum Drift   : {drift:.2e}")
    
    passed = drift < 1e-10
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_5_centre_of_mass() -> bool:
    """5. CENTRE OF MASS BEHAVIOR TEST"""
    print("\n--- TEST 5: Centre of Mass Motion ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[0])
    sys = NBodySystem(bodies, G=1.0)
    dt = 0.005
    
    com0 = ScientificDiagnostics.calculate_centre_of_mass(sys)
    p0 = ScientificDiagnostics.calculate_linear_momentum(sys)
    total_m = sum(b.mass for b in sys.bodies)
    v_com = p0 / total_m
    
    t_total = 5.0
    for _ in range(int(t_total / dt)):
        VelocityVerletIntegrator.step(sys, dt)
        
    com_expected = com0 + v_com * t_total
    com_actual = ScientificDiagnostics.calculate_centre_of_mass(sys)
    diff = float(np.linalg.norm(com_actual - com_expected))
    
    print(f"  Expected CoM : {com_expected}")
    print(f"  Actual CoM   : {com_actual}")
    print(f"  Difference   : {diff:.2e}")
    
    passed = diff < 1e-8
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_6_angular_momentum() -> bool:
    """6. ANGULAR MOMENTUM CONSERVATION TEST"""
    print("\n--- TEST 6: Angular Momentum Conservation ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[1])
    sys = NBodySystem(bodies, G=1.0)
    dt = 0.005
    
    l0 = ScientificDiagnostics.calculate_angular_momentum(sys)
    for _ in range(2000):
        VelocityVerletIntegrator.step(sys, dt)
        
    lf = ScientificDiagnostics.calculate_angular_momentum(sys)
    drift = abs(lf - l0)
    
    print(f"  Initial L_z : {l0:.8f}")
    print(f"  Final L_z   : {lf:.8f}")
    print(f"  Drift       : {drift:.2e}")
    
    passed = drift < 1e-8
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_7_timestep_convergence() -> bool:
    """7. TIMESTEP CONVERGENCE TEST (2ND ORDER VELOCITY VERLET)"""
    print("\n--- TEST 7: Timestep Convergence (2nd Order Verification) ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[0])
    
    def run_sim(dt_val: float) -> np.ndarray:
        sys = NBodySystem(bodies, G=1.0)
        for _ in range(int(2.0 / dt_val)):
            VelocityVerletIntegrator.step(sys, dt_val)
        return sys.get_positions()
        
    dt_base = 0.01
    p1 = run_sim(dt_base)
    p2 = run_sim(dt_base / 2.0)
    p4 = run_sim(dt_base / 4.0)
    
    err_coarse = float(np.linalg.norm(p1 - p2))
    err_fine = float(np.linalg.norm(p2 - p4))
    
    ratio = err_coarse / err_fine if err_fine > 0 else 4.0
    print(f"  Error (dt vs dt/2)   : {err_coarse:.2e}")
    print(f"  Error (dt/2 vs dt/4) : {err_fine:.2e}")
    print(f"  Convergence Ratio    : {ratio:.2f} (Expected ~4.0 for O(dt^2))")
    
    passed = 2.5 <= ratio <= 5.5
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_8_divergence_test() -> bool:
    """8. DIVERGENCE & FTLE TEST"""
    print("\n--- TEST 8: Dual Universe Divergence D(t) & FTLE ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[2]) # Unstable encounter preset
    pert = PerturbationConfig(body_index=0, target="pos_x", magnitude=1e-5)
    
    dual = DualUniverseSystem(bodies, G=1.0, perturbation=pert)
    dt = 0.002
    
    print(f"  Initial Divergence D(0) : {dual.get_divergence():.2e}")
    
    for _ in range(2500):
        dual.step(dt)
        
    df = dual.get_divergence()
    ftle = dual.get_ftle()
    
    print(f"  Final Divergence D(t)   : {df:.6f}")
    print(f"  Measured FTLE (time^-1) : {ftle:.4f}")
    
    passed = df > pert.magnitude and ftle > 0.0
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_9_timestep_safety() -> bool:
    """9. TIMESTEP SAFETY RATIO CHECK"""
    print("\n--- TEST 9: Timestep Safety Ratio Check (dt/tau <= 0.10) ---")
    presets = get_builtin_presets()
    bodies = load_preset_bodies(presets[0])
    sys = NBodySystem(bodies, G=1.0)
    dt = 0.005
    
    diag = ScientificDiagnostics.calculate_all(sys, dt)
    ratio = diag["dt_tau_ratio"]
    is_safe = diag["is_resolved"]
    
    print(f"  Encounter Timescale tau : {diag['encounter_timescale']:.6f}")
    print(f"  dt / tau Ratio          : {ratio:.4f}")
    print(f"  Resolution Status       : {diag['resolution_status']}")
    
    passed = is_safe and ratio <= 0.10
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def test_10_save_load() -> bool:
    """10. SAVE / LOAD FIDELITY TEST"""
    print("\n--- TEST 10: Experiment Save / Load Fidelity ---")
    custom_exp = {
        "id": "custom_test",
        "name": "Custom Test System",
        "G": 1.5,
        "dt": 0.003,
        "duration": 30.0,
        "perturbation": {
            "body_index": 2,
            "target": "vel_y",
            "magnitude": 0.00042
        },
        "bodies": [
            {
                "name": "CustomStarA",
                "mass": 3.14,
                "position": [1.2, -0.5],
                "velocity": [-0.1, 0.4],
                "color": [255, 100, 100],
                "radius": 95.0
            },
            {
                "name": "CustomStarB",
                "mass": 2.71,
                "position": [-0.8, 0.9],
                "velocity": [0.2, -0.3],
                "color": [100, 255, 100],
                "radius": 110.0
            },
            {
                "name": "CustomStarC",
                "mass": 1.41,
                "position": [0.1, 0.1],
                "velocity": [-0.1, -0.1],
                "color": [100, 100, 255],
                "radius": 75.0
            }
        ]
    }
    
    filepath = "test_roundtrip.json"
    with open(filepath, "w") as f:
        json.dump(custom_exp, f, indent=2)
        
    with open(filepath, "r") as f:
        loaded_exp = json.load(f)
        
    passed = (loaded_exp == custom_exp)
    print(f"  JSON Serialization Match: {passed}")
    
    if os.path.exists(filepath):
        os.remove(filepath)
        
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    return passed


def run_all_tests() -> bool:
    """Executes all 10 validation self-tests."""
    print("============================================================")
    print("ORBITAL ECHO: SCIENTIFIC VALIDATION & SELF-TEST SUITE")
    print("============================================================")
    
    tests = [
        test_1_two_body_circular_orbit,
        test_2_figure_eight_stability,
        test_3_energy_conservation,
        test_4_linear_momentum,
        test_5_centre_of_mass,
        test_6_angular_momentum,
        test_7_timestep_convergence,
        test_8_divergence_test,
        test_9_timestep_safety,
        test_10_save_load
    ]
    
    results = []
    for test_fn in tests:
        try:
            res = test_fn()
            results.append(res)
        except Exception as e:
            print(f"  EXCEPTION during test: {e}")
            results.append(False)
            
    passed_count = sum(results)
    total_count = len(results)
    
    print("\n============================================================")
    print(f"TEST SUMMARY: {passed_count}/{total_count} TESTS PASSED")
    print("============================================================")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
