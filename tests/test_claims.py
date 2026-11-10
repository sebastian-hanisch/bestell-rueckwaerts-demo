"""Jede Zahl der README steht hier als Zählung (k von m Zellen, Band oder exakt): Tabelle „Zahl -> Test“ in der README.

Die Messreihen rechnen dieselben Funktionen wie `tools/measure_grid.py` (alle Zellen der Regler, kein Zufall); nur die Simulation ist vorgerechnet
(`data/simulation_vorgerechnet.json`, erzeugt von `tools/measure_simulation.py`) und wird hier gegen die exakten Werte gelesen."""

import importlib.util
import sys
from pathlib import Path

import pytest

import brw_algorithm as A
import brw_demand as D
import brw_evaluation as EV

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("measure_grid", ROOT / "tools" / "measure_grid.py")
MG = importlib.util.module_from_spec(_spec)
sys.modules["measure_grid"] = MG
_spec.loader.exec_module(MG)


@pytest.fixture(scope="module")
def c0():
    return MG.cells_c0()


@pytest.fixture(scope="module")
def purchase():
    return MG.cells_purchase()


@pytest.fixture(scope="module")
def extra():
    return MG.table_extra()


# ---------------------------------------------------------------- c = 0: 80 Zellen

def test_80_cells_level_equals_quantile_equals_enumeration_at_every_rest_period(c0):
    assert len(c0) == 80
    assert sum(1 for r in c0 if r["set"] == {r["q"]} and r["q"] == r["enum"]) == 80


def test_80_cells_are_stationary_from_one_rest_period_and_the_fixed_level_costs_nothing_extra(c0):
    assert sum(1 for r in c0 if r["n_star"] == 1) == 80
    assert max(abs(r["extra"]) for r in c0) < 1e-9


def test_80_cells_action_is_max_of_position_and_level_in_every_state(c0):
    assert sum(1 for r in c0 if r["action_ok"]) == 80


def test_80_cells_have_no_tie_between_best_and_second_best_level_and_no_edge_mass(c0):
    assert min(r["tie"] for r in c0) > 0.007 and min(r["gap_min"] for r in c0) > 0.007      # in der README: mehr als 0,007
    assert sum(1 for r in c0 if r["edge_ok"]) == 80


def test_equivalence_over_lead_time_times_mean_in_20_groups_of_the_80_cells():
    assert MG.equivalence_groups() == (60, 20, 0)


# ---------------------------------------------------------------- Vehikel

def test_vehicle_table_levels_costs_and_startup():
    rows = MG.vehicle_rows()
    assert [r["S"] for r in rows] == [5, 9, 13, 17]
    assert [round(r["g"], 4) for r in rows] == [3.3462, 4.6126, 5.5798, 6.4507]
    assert [round(r["V52"], 4) for r in rows] == [174.0027, 239.8546, 290.1492, 335.4338]
    assert [round(r["startup"], 6) for r in rows] == [0.0, 27.0, 81.0, 162.0]
    assert all(r["n_star"] == 1 for r in rows)


def test_vehicle_controllable_cost_is_n_times_the_period_cost_at_c_zero():
    for L in range(4):
        a = EV.analyse(EV.Settings(L=L))
        assert a.controllable == pytest.approx(52 * a.g, rel=1e-9)


def test_level_table_for_mean_3_and_every_penalty_ratio():
    expected = {0: [3, 4, 4, 5, 6], 1: [6, 7, 8, 9, 10], 2: [9, 10, 11, 13, 14], 3: [12, 13, 15, 17, 18]}
    for L, levels in expected.items():
        got = [A.backward(5, EV.make_model(L=L, mean=3, ph=ph)).S[5] for ph in (1, 2, 4, 9, 19)]
        assert got == levels, L


def test_truncation_mass_per_mean():
    masses = MG.truncation_masses()
    assert all(m < 1e-43 for m in masses.values()) and masses[3] == pytest.approx(2.0e-51, rel=0.05)


# ---------------------------------------------------------------- c > 0

def test_144_cells_with_purchase_price_limit_level_is_the_quantile_and_last_level_is_the_formula(purchase):
    assert len(purchase) == 144
    assert sum(1 for r in purchase if r["S_last"] == r["q"]) == 144            # bei 30 Rest-Perioden
    assert sum(1 for r in purchase if r["S1"] == r["q1"]) == 144              # S_1 = Quantil zum Verhältnis (p - c)/(p + h)
    assert sum(1 for r in purchase if r["action_ok"]) == 144
    assert sum(1 for r in purchase if r["edge_ok"]) == 144                    # Randmasse unten 0


def test_32_cells_with_purchase_price_stationary_from_2_to_5_rest_periods(extra):
    assert len(extra) == 32
    assert (min(r["n_star"] for r in extra), max(r["n_star"] for r in extra)) == (2, 5)
    assert all(all(s <= r["S"] for s in r["S14"]) for r in extra)               # die letzten Perioden bestellen nie mehr als das Grenzniveau


def test_32_cells_extra_cost_of_the_fixed_level_bands(extra):
    for n, lo, hi in ((1, 1.86, 31.91), (3, 0.69, 13.33), (52, 0.04, 1.35)):
        values = [r["pct"][n] for r in extra]
        assert (round(min(values), 2), round(max(values), 2)) == (lo, hi), n
    assert (round(min(r["abs52"] for r in extra), 3), round(max(r["abs52"] for r in extra), 3)) == (0.145, 15.791)
    assert (round(min(r["abs52_g"] for r in extra), 2), round(max(r["abs52_g"] for r in extra), 2)) == (0.04, 2.45)


def test_hand_picked_cell_mean_3_ph_9_c_3_L_3():
    a = EV.analyse(EV.Settings(L=3, ph=9, c=3))
    assert a.bw.S[1:5] == [13, 15, 16, 17] and a.level == 17 and a.n_star == 4
    assert a.fixed_extra == pytest.approx(7.1348, abs=5e-5)


def test_branch_extra_cost_is_exactly_zero_at_c_zero_and_positive_with_purchase_price():
    """Zweig-Test: die Spalte „Mehrkosten des festen S“ ist kein toter Zweig."""
    assert max(abs(EV.analyse(EV.Settings(L=L, c=0)).fixed_extra) for L in range(4)) < 1e-9
    assert min(EV.analyse(EV.Settings(L=L, c=1)).fixed_extra for L in range(4)) > 0.1


def test_branch_purchase_price_changes_the_last_level_and_lead_time_changes_the_level():
    base = A.backward(1, EV.make_model(L=0, mean=3, ph=9, c=0)).S[1]
    assert A.backward(1, EV.make_model(L=0, mean=3, ph=9, c=3)).S[1] != base
    assert A.backward(1, EV.make_model(L=3, mean=3, ph=9, c=0)).S[1] != base


# ---------------------------------------------------------------- Simulation (vorgerechnet)

def test_precomputed_simulation_48_seed_values_within_the_noise():
    pre = EV.load_precomputed()
    assert (pre["paths"], len(pre["seeds"]), pre["horizon"]) == (100000, 4, 52)
    assert len(pre["rows"]) == 16
    zs = [z for r in pre["rows"] for z in r["z"]]
    assert len(zs) == 64 and max(abs(z) for z in zs) < 2.2                      # README: größter Betrag 2,09 (Rückwärtsrechnung und festes Niveau bei c = 0 teilen die Zahlen)
    assert round(max(abs(z) for z in zs), 2) == 2.09
    distinct = {(r["c"], r["L"], tuple(r["sim_means"])) for r in pre["rows"]}
    assert len(distinct) == 12                                                  # bei c = 0 sind beide Politiken dieselbe Regel: 4 + 8 = 12 verschiedene Zeilen


def test_precomputed_exact_values_agree_with_the_live_exact_values():
    pre = EV.load_precomputed()
    for r in pre["rows"]:
        a = EV.analyse(EV.Settings(L=r["L"], ph=pre["ph"], mean=pre["mean"], c=r["c"], n=pre["horizon"]))
        expected = a.total if r["policy"] == "dp" else a.total + a.fixed_extra
        assert r["exact"] == pytest.approx(expected, rel=1e-12), r
        assert r["level"] == a.level


def test_precomputed_means_of_the_four_seeds_are_within_the_standard_error():
    pre = EV.load_precomputed()
    for r in pre["rows"]:
        mean4 = sum(r["sim_means"]) / 4
        se4 = (sum(s * s for s in r["ses"]) ** 0.5) / 4
        assert abs(mean4 - r["exact"]) < 3 * se4, r


def test_abort_mass_of_poisson_truncation_is_negligible():
    for mean in (2, 3, 4, 5):
        assert D.truncation_mass(mean, D.dmax_for(mean)) < 1e-43
