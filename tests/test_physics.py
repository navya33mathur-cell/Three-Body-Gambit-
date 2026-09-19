"""
Pytest integration for Orbital Echo.
"""
import pytest
from selftest import (
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
)

def test_circular_orbit():
    assert test_1_two_body_circular_orbit()

def test_figure_eight():
    assert test_2_figure_eight_stability()

def test_energy():
    assert test_3_energy_conservation()

def test_momentum():
    assert test_4_linear_momentum()

def test_com():
    assert test_5_centre_of_mass()

def test_angular_momentum():
    assert test_6_angular_momentum()

def test_convergence():
    assert test_7_timestep_convergence()

def test_divergence():
    assert test_8_divergence_test()

def test_timestep_safety():
    assert test_9_timestep_safety()

def test_save_load():
    assert test_10_save_load()
