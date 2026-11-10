"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, Gleichstände, inklusive Grenzen, Reglerränder."""

import numpy as np
import pytest

import brw_algorithm as A
import brw_constants as C
import brw_demand as D
import brw_evaluate as E
import brw_evaluation as EV
import brw_policy as P
import brw_simulate as S


def test_one_rest_period_has_a_single_level_and_two_rest_periods_are_consistent(mini):
    bw1 = A.backward(1, mini)
    assert bw1.S == [None, 2] and len(bw1.V) == 2
    bw2 = A.backward(2, mini)
    assert bw2.S == [None, 2, 2] and bw2.V[2][mini.index(0)] == pytest.approx(2.0)     # n = 2: H_2(2) = 2 von Hand


def test_exactly_two_rest_periods_with_purchase_price_differ_in_the_last_one(mini_c1):
    assert A.backward(2, mini_c1).S[1:] == [1, 2]


def test_stationary_from_with_one_and_two_entries():
    assert A.stationary_from([None, 4]) == 1
    assert A.stationary_from([None, 3, 4]) == 2


def test_penalty_equal_to_holding_cost_gives_the_median():
    """p/h = 1: kritisches Verhältnis 1/2, das Niveau ist der Median der Nachfrage über L + 1 Perioden (L = 0, Mittel 3: Median der Poisson-Verteilung ist 3)."""
    assert A.backward(5, EV.make_model(L=0, mean=3, ph=1)).S[5] == 3


def test_position_above_the_level_orders_nothing_and_costs_more(mini):
    bw = A.backward(3, mini)
    x = 3                                                   # über S = 2
    assert mini.x[bw.action[1][mini.index(x)]] == x          # keine Bestellung
    assert bw.V[1][mini.index(3)] > bw.V[1][mini.index(2)]


def test_lowest_reachable_position_is_above_the_grid_edge():
    for L in range(4):
        for mean in (2, 5):
            m = EV.make_model(L=L, mean=mean, ph=19)
            assert A.edge_mass_is_zero(m, A.backward(8, m).S)


def test_slider_extremes_run_without_error():
    for L, ph, mean, c, n in ((C.L_MIN, 1, C.MEAN_MIN, 0, C.N_MIN), (C.L_MAX, 19, C.MEAN_MAX, 5, C.N_MAX)):
        a = EV.analyse(EV.Settings(L=L, ph=ph, mean=mean, c=c, n=n))
        assert a.level >= 0 and a.controllable > 0 and a.n_star is not None


def test_one_rest_period_in_the_analysis_has_no_stationarity_surprise():
    a = EV.analyse(EV.Settings(n=1))
    assert a.controllable == pytest.approx(a.g) and a.fixed_extra == pytest.approx(0.0, abs=1e-12)


def test_purchase_price_equal_to_or_above_penalty_is_not_computed():
    with pytest.raises(ValueError):
        EV.analyse(EV.Settings(ph=2, c=3))
    with pytest.raises(ValueError):
        EV.analyse(EV.Settings(ph=1, c=1))                  # gleich: Grenze nicht inklusive
    EV.analyse(EV.Settings(ph=2, c=1))                      # knapp darunter: gerechnet
    assert all(r["c"] < 4 for r in EV.purchase_rows(EV.Settings(ph=4)))
    assert [r["c"] for r in EV.purchase_rows(EV.Settings(ph=1))] == [0]


def test_bounds_of_the_regulators_are_inclusive():
    assert C.L_MIN == 0 and C.L_MAX == 3 and C.N_MIN == 1 and C.N_MAX == C.NMAX
    assert C.PH_OPTIONS[0] == 1 and C.HAND_C_OPTIONS == (0, 1)
    EV.analyse(EV.Settings(n=C.N_MAX))
    with pytest.raises(ValueError):                          # n = NMAX + 1 liegt außerhalb der gerechneten Restzahlen
        EV.analyse(EV.Settings(n=C.NMAX + 1))


def test_demand_input_errors():
    with pytest.raises(ValueError):
        D.poisson_pmf(0.0, 10)
    with pytest.raises(ValueError):
        D.poisson_pmf(3.0, -1)
    with pytest.raises(ValueError):
        D.lead_pmf(np.array([1.0]), -1)
    with pytest.raises(ValueError):
        P.poisson_cdf_table(0.0, 5)


def test_hand_example_rejects_other_purchase_prices():
    import brw_hand as H
    with pytest.raises(ValueError):
        H.solve(2)


def test_total_cost_with_start_position_outside_the_grid_is_an_error(mini):
    with pytest.raises(ValueError):
        E.total_cost(mini, A.backward(2, mini).V[2], x0=999)


def test_two_paths_are_enough_for_a_standard_error():
    costs = S.simulate([5, None], L=1, mean=3.0, h=1.0, p=9.0, c=0.0, paths=2, seed=1)
    assert len(costs) == 2 and np.isfinite(S.summary(costs)[1])
