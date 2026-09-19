# THREE-BODY GAMBIT: CHAOS THROUGH TIME

> **YPAE SIMATHON 02 Competition Project**  

---

## 🔬 1. Scientific Question

How can extremely small changes in the initial conditions of a gravitational three-body system lead to substantially different future states over time, and how can we demonstrate that observed trajectory divergence represents true physical sensitivity to initial conditions rather than numerical integration error?

---

## 🌌 2. Core Physics Equations

The simulation computes the motion of three celestial bodies interacting solely through classical Newtonian gravitation without artificial smoothing or scripted paths ($\epsilon = 0$).

For body $i \in \{1, 2, 3\}$, the gravitational acceleration $\mathbf{a}_i$ is computed at every timestep directly from current 3D positions $\mathbf{r}_k$:

$$\mathbf{a}_i = G \sum_{j \neq i} m_j \frac{\mathbf{r}_j - \mathbf{r}_i}{|\mathbf{r}_j - \mathbf{r}_i|^3}$$

where $G = 1.0$ in dimensionless simulation units.

---

## ⚡ 3. Numerical Integration & Simulation Step API

The trajectory of each body is integrated using the second-order symplectic **Velocity Verlet** scheme:

1. **Acceleration at current step**:  
   $$\mathbf{a}(t) = \mathbf{a}(\mathbf{r}(t))$$

2. **Position Update**:  
   $$\mathbf{r}(t + \Delta t) = \mathbf{r}(t) + \mathbf{v}(t) \Delta t + \frac{1}{2} \mathbf{a}(t) \Delta t^2$$

3. **Acceleration at new positions**:  
   $$\mathbf{a}(t + \Delta t) = \mathbf{a}(\mathbf{r}(t + \Delta t))$$

4. **Velocity Update**:  
   $$\mathbf{v}(t + \Delta t) = \mathbf{v}(t) + \frac{1}{2} \left[ \mathbf{a}(t) + \mathbf{a}(t + \Delta t) \right] \Delta t$$

### Simulation Step API Safety
* **Step Invocation**: `VelocityVerletIntegrator.step(system, dt)` advances physical simulation clock `system.time` by exactly $\Delta t$ upon successful integration.
* **$dt$ Validation**: Validates that $\Delta t > 0$ and is a finite floating-point number.
* **Unresolved Protection**: Rejects integration steps if the system has breached close-approach threshold `system.unresolved == True`.

---

## 📐 4. Dimensionless Unit System

The engine operates in a dimensionless unit framework where $G = 1.0$:

| Quantity | Unit Definition | Physical Mapping Example |
| :--- | :--- | :--- |
| **Gravitational Constant ($G$)** | $1.0$ (Dimensionless) | $6.67430 \times 10^{-11} \text{ m}^3 \text{ kg}^{-1} \text{ s}^{-2}$ |
| **Mass Unit ($M_u$)** | $1.0$ | Solar Mass ($1.989 \times 10^{30} \text{ kg}$) |
| **Distance Unit ($L_u$)** | $1.0$ | Astronomical Unit ($1.496 \times 10^{11} \text{ m}$) |
| **Time Unit ($T_u$)** | $\sqrt{L_u^3 / (G M_u)} = 1.0$ | $1 \text{ Year} / (2\pi) \approx 58.13 \text{ days}$ |
| **Velocity Unit ($V_u$)** | $L_u / T_u = 1.0$ | Earth Orbital Velocity ($\approx 29.78 \text{ km/s}$) |
| **Energy Unit ($E_u$)** | $M_u V_u^2 = 1.0$ | $1.76 \times 10^{41} \text{ Joules}$ |

---

## 🛡️ 5. Conserved Quantities & Diagnostic Normalization

The engine tracks key dynamical invariants throughout simulation:

* **Centre of Mass**:  
  $$\mathbf{R}_{CM} = \frac{\sum_i m_i \mathbf{r}_i}{\sum_i m_i}$$

* **Total Linear Momentum**:  
  $$\mathbf{P} = \sum_i m_i \mathbf{v}_i$$

* **Total Angular Momentum**:  
  $$\mathbf{L} = \sum_i m_i (\mathbf{r}_i \times \mathbf{v}_i)$$

* **Total Kinetic Energy**:  
  $$K = \sum_i \frac{1}{2} m_i |\mathbf{v}_i|^2$$

* **Total Potential Energy**:  
  $$U = -G \sum_{i < j} \frac{m_i m_j}{|\mathbf{r}_i - \mathbf{r}_j|}$$

* **Total Mechanical Energy**:  
  $$E = K + U$$

* **Diagnostic Normalization Rules**:  
  * For non-zero reference quantities ($E_0 \neq 0$), relative drift $\max_t \frac{|E(t) - E_0|}{|E_0|}$ is evaluated.
  * For zero or near-zero reference quantities ($\mathbf{P}_0 = \mathbf{0}$, $\mathbf{L}_0 = \mathbf{0}$, $\mathbf{R}_{CM,0} = \mathbf{0}$), relative division by zero is undefined ($0/0$). Absolute drift ($\max_t ||\mathbf{P}(t) - \mathbf{P}_0||$, $\max_t ||\mathbf{L}(t) - \mathbf{L}_0||$, $\max_t ||\mathbf{R}_{CM}(t) - \mathbf{R}_{CM,0}||$) is evaluated as the primary physical metric.

---

## 🛑 6. Close-Approach Singularity Safeguard

As two bodies approach closely ($|\mathbf{r}_i - \mathbf{r}_j| \to 0$), Newtonian gravitational acceleration approaches infinity. To avoid unphysical force spikes or silent numerical corruption:
* The engine evaluates pairwise distances at every step against a minimum resolvable threshold $r_{threshold} = 10^{-6}$.
* If $|\mathbf{r}_i - \mathbf{r}_j| < r_{threshold}$, the run is flagged as **unresolved**, recording time, body IDs, and separation before cleanly halting. No artificial denominator clamping or force softening is applied.

---

## 📊 7. Headless Scientific Validation & Self-Tests

The engine includes a 7-test CLI self-test suite (`python3 sim.py --self-test`). Below are the **actual measured numerical results** from execution:

```text
====================================================================
THREE-BODY GAMBIT — SCIENTIFIC SELF-TESTS (STAGE 2 AUDITED)
====================================================================

[1] TWO-BODY CIRCULAR ORBIT TEST
  Theoretical period : 12.56637061
  Measured period    : 12.56637088
  Absolute error     : 2.61802253e-07
  Percentage error   : 0.000002%
  Status             : PASS (Threshold: < 0.1%)

[2] ENERGY CONSERVATION TEST
  Initial energy     : -1.287137446272
  Final energy       : -1.287137450362
  Absolute change    : 4.08970080e-09
  Final rel drift    : 3.17736137e-09
  Maximum rel drift  : 5.89213591e-07
  Status             : PASS (Threshold: max relative energy drift < 1e-5)

[3] MOMENTUM CONSERVATION TEST
  Initial momentum   : [0.00e+00, 0.00e+00, 0.00e+00]
  Final momentum     : [-5.00e-15, -7.11e-15, 0.00e+00]
  Maximum drift      : 1.54636174e-14
  Final drift        : 8.68603189e-15
  Note               : Initial P_0 is [0,0,0]. Relative normalization is undefined (0/0); absolute drift is evaluated.
  Status             : PASS (Threshold: < 1e-12)

[4] CENTRE OF MASS DRIFT TEST
  Initial COM        : [0.00e+00, 0.00e+00, 0.00e+00]
  Final COM          : [-3.52e-14, -1.62e-14, 0.00e+00]
  Maximum drift      : 3.89172059e-14
  Final drift        : 3.87396827e-14
  Note               : Initial COM R_0 is [0,0,0]. Relative normalization is undefined (0/0); absolute drift is evaluated.
  Status             : PASS (Threshold: < 1e-12)

[5] TIME-STEP CONVERGENCE TEST
  dt                 : 0.008000  (Error ||S_dt - S_dt/2|| = 3.88889634e-04)
  dt/2               : 0.004000  (Error ||S_dt/2 - S_dt/4|| = 9.72656642e-05)
  dt/4               : 0.002000
  Convergence ratio R: 3.9982
  Expected ratio     : approximately 4.0 (2nd-order Velocity Verlet)
  Status             : PASS (Expected 3.5 <= R <= 4.5)

[6] PERTURBATION EXPERIMENT & FULL-TRAJECTORY CONVERGENCE TEST
  Perturbation delta : 1.0e-06
  Initial D(0)       : 1.00000000e-06
  Final D(t_final)   : 2.98813425e-05
  Maximum D(t)       : 2.99360914e-05
  Divergence CSV log : saved to 'divergence_log.csv'
  Final-D Convergence Check  (Compare dt=0.001, dt/2=0.0005, dt/4=0.00025):
    Final D (dt)     : 2.98813425e-05
    Final D (dt/2)   : 2.98806627e-05
    Final D (dt/4)   : 2.98802932e-05
    Final-D Rel Error: 0.0012%
  Full Trajectory Curve Audit (dt/2 vs dt/4 over t in [0, 10.0]):
    Max Absolute Curve Diff : 1.85073103e-11
    RMS Curve Difference    : 8.91839624e-12
    Normalized Max Curve Diff: 1.25555069e-06
    Post-Initial Max Rel Err: 0.000127%
  Interpretation     : Sensitivity to initial conditions reproduced under timestep refinement.
  Status             : PASS (Full trajectory curve agreement < 1%)

[7] ANGULAR MOMENTUM CONSERVATION TEST
  Initial L vector   : [0.00e+00, 0.00e+00, 0.00e+00]
  Initial L magnitude: 0.00000000e+00
  Final L vector     : [0.00e+00, 0.00e+00, 1.60e-14]
  Final absolute drift: 1.59872116e-14
  Maximum absolute drift: 1.60982339e-14
  Note               : Initial L_0 is [0,0,0]. Relative normalization is undefined (0/0); maximum absolute angular momentum drift is evaluated.
  Status             : PASS (Threshold: max absolute L drift < 1e-12)

====================================================================
ALL SCIENTIFIC SELF-TESTS PASSED SUCCESSFULLY!
====================================================================
```

---

## 🔍 8. Scientific Interpretation of Perturbation & Divergence

The perturbation experiment measures Euclidean distance across corresponding bodies in Universe A and Universe B:

$$D(t) = \sqrt{\sum_{i=1}^3 |\mathbf{r}_{A,i}(t) - \mathbf{r}_{B,i}(t)|^2}$$

### Exact Interpretation
* **Sensitivity to Initial Conditions**: The perturbation experiment demonstrates **sensitivity to initial conditions reproduced under timestep refinement**.
* **Role of Full-Trajectory Timestep Refinement**: Running identical perturbations under $\Delta t, \Delta t/2, \Delta t/4$ demonstrates that the observed trajectory divergence is **numerically reproducible across the entire time interval** ($t \in [0, 10.0]$) with maximum trajectory curve error $< 1.86 \times 10^{-11}$ and post-initial relative curve error $< 0.0002\%$, confirming it is not an artifact of an unresolved integration step.
* **Non-Claim of Proof of Chaos**: The perturbation experiment alone does **NOT** claim to prove global deterministic chaos.

---

## 🛠️ 9. Reproducibility & Instructions

### Installation

```bash
git clone https://github.com/user/three-body-gambit.git
cd three-body-gambit
pip install -r requirements.txt
```

### Running Self-Tests

```bash
python3 sim.py --self-test
```

---

## 📜 10. Stage 2 Development Log

```text
Stage 2: Robust Simulation Layer & Audit Enhancements
------------------------------------------------------
- Added input validation to VelocityVerletIntegrator.step(system, dt) (dt > 0, finite float check, clock synchronization, unresolved state protection).
- Enforced diagnostic normalization rules:
  * Evaluated relative drift max_t |E(t)-E0|/|E0| for non-zero reference E0.
  * Evaluated absolute drift for zero reference quantities P0 = [0,0,0], L0 = [0,0,0], R_CM,0 = [0,0,0].
- Added Test 7: Angular Momentum Conservation Test (Figure-Eight orbit, T=20.0, dt=0.001). Measured max absolute L drift = 1.61e-14 (< 1e-12). PASS.
- Enhanced Test 6: Full-Trajectory Perturbation Curve Audit over t in [0, 10.0]. Measured max abs curve diff = 1.85e-11, RMS diff = 8.92e-12, post-initial max rel error = 0.000127%. PASS.
- Verified zero numerical regressions against Stage 1 baseline.
```

## 🖥️ 8. Scientific Interface

The application opens directly in **Scientific Mode**. There is no cinematic presentation mode. The main viewport shows the actual trajectories of Universe A and Universe B on a dark scientific grid, while the right panel reports the current numerical state.

### Presets

Use `1`–`5` to load the five built-in configurations. Each preset resets the experiment and its controlled perturbation.

### Step-by-step physics guide

Press `H` to open **WHAT IS HAPPENING?** in the right-hand panel. The guide is specific to the selected preset and advances one explanation at a time with clickable **NEXT →** and **← PREVIOUS** buttons. It explains the starting configuration, the gravitational dynamics, the controlled perturbation, what the separated trails mean, and how to interpret `D(t)` and numerical safety.

The guide deliberately distinguishes **sensitivity to initial conditions** from a claim that divergence alone proves mathematical chaos.

### Run

Requires Python 3.12 recommended, NumPy, and Pygame.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python sim.py --self-test
python main.py
```

