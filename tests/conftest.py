"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brw_algorithm as A  # noqa: E402
import brw_demand as D  # noqa: E402


@pytest.fixture
def mini():
    """Handbeispiel: Nachfrage 0, 1, 2 mit je 1/3, h = 1, p = 3, Lieferzeit 0, Einkaufspreis 0.
    Handrechnung: G(0) = 3, G(1) = 4/3, G(2) = 1, G(3) = 2; Quantil zum Verhältnis 3/4 ist S = 2."""
    return A.Model(L=0, pmf1=D.three_point_pmf(), h=1.0, p=3.0, c=0.0)


@pytest.fixture
def mini_c1():
    """Dasselbe Handbeispiel mit Einkaufspreis 1: S_1 = 1, S_2 = S_3 = 2."""
    return A.Model(L=0, pmf1=D.three_point_pmf(), h=1.0, p=3.0, c=1.0)
