"""Einheiten von Hand gerechnet (Mini-Instanz = Handbeispiel) und Eigenschaften der Rückwärtsrechnung (DEMO-PLAYBOOK §1b und §5).

Handrechnung (Nachfrage 0, 1, 2 mit je 1/3, h = 1, p = 3, Lieferzeit 0):
  G(y) = (1/3) sum_d [ (y - d)^+ + 3 (d - y)^+ ]:  G(0) = (0 + 3 + 6)/3 = 3, G(1) = (1 + 0 + 3)/3 = 4/3, G(2) = (2 + 1 + 0)/3 = 1, G(3) = (3 + 2 + 1)/3 = 2.
  c = 0: V_1(x) = 1 für x <= 2 und V_1(3) = 2; H_2(2) = 1 + (1 + 1 + 1)/3 = 2, S_2 = 2, V_2 = 2; H_3(2) = 1 + 2 = 3, V_3 = 3; V_3(3) = 40/9.
  c = 1: H_1 = 3, 7/3, 3, 5 für y = 0..3, S_1 = 1; H_2 = 19/3, 14/3, 41/9, 58/9, S_2 = 2; H_3 = 77/9, 62/9, 59/9, 221/27, S_3 = 2."""

import numpy as np
import pytest

import brw_algorithm as A
import brw_cost as K
import brw_demand as D
import brw_evaluate as E
import brw_hand as H
import brw_policy as P
import brw_simulate as S
from brw_evaluation import make_model


# ---------------------------------------------------------------- Nachfrage und Kosten

def test_poisson_pmf_sums_to_one_and_matches_the_formula_at_a_few_points():
    pmf = D.poisson_pmf(3.0, 56)
    assert pmf.sum() == pytest.approx(1.0, abs=1e-15)
    assert pmf[0] == pytest.approx(np.exp(-3.0), rel=1e-12)             # P(D = 0) = e^-3
    assert pmf[2] == pytest.approx(np.exp(-3.0) * 9 / 2, rel=1e-12)     # P(D = 2) = e^-3 · 3² / 2!
    assert pmf[3] == pytest.approx(np.exp(-3.0) * 27 / 6, rel=1e-12)


def test_truncation_puts_the_rest_on_the_top_value():
    pmf = D.poisson_pmf(3.0, 2)    # absichtlich viel zu klein abgeschnitten
    assert pmf.sum() == pytest.approx(1.0, abs=1e-15)
    assert pmf[2] == pytest.approx(1.0 - np.exp(-3.0) * (1 + 3), rel=1e-12)


def test_lead_pmf_of_two_periods_by_hand():
    lead = D.lead_pmf(D.three_point_pmf(), 2)       # Summe zweier Nachfragen 0..2: 0:1/9, 1:2/9, 2:3/9, 3:2/9, 4:1/9
    assert lead == pytest.approx(np.array([1, 2, 3, 2, 1]) / 9)
    assert D.lead_pmf(D.three_point_pmf(), 0).tolist() == [1.0]


def test_period_cost_by_hand():
    G = K.period_cost(np.arange(0, 4), D.three_point_pmf(), 1.0, 3.0)
    assert G == pytest.approx([3.0, 4 / 3, 1.0, 2.0])


def test_period_cost_is_zero_for_constant_demand_at_the_demand_level():
    pmf = np.array([0.0, 0.0, 1.0])                  # Nachfrage immer 2
    assert K.period_cost(np.array([2]), pmf, 1.0, 1.0)[0] == 0.0


# ---------------------------------------------------------------- Rückwärtsrechnung

def test_hand_example_without_purchase_price(mini):
    bw = A.backward(3, mini)
    assert bw.S[1:] == [2, 2, 2]
    i = mini.index
    assert [bw.V[1][i(x)] for x in (-2, 0, 2, 3)] == pytest.approx([1.0, 1.0, 1.0, 2.0])
    assert [bw.V[2][i(x)] for x in (0, 2)] == pytest.approx([2.0, 2.0])
    assert bw.V[3][i(0)] == pytest.approx(3.0) and bw.V[3][i(3)] == pytest.approx(40 / 9)


def test_hand_example_with_purchase_price_one(mini_c1):
    bw = A.backward(3, mini_c1)
    assert bw.S[1:] == [1, 2, 2]                              # nur die letzte Periode bestellt weniger
    i = mini_c1.index
    assert [bw.V[1][i(x)] for x in (0, 1, 2, 3)] == pytest.approx([7 / 3, 4 / 3, 1.0, 2.0])
    assert [bw.V[2][i(x)] for x in (0, 1, 2, 3)] == pytest.approx([41 / 9, 32 / 9, 23 / 9, 31 / 9])
    assert [bw.V[3][i(x)] for x in (0, 1, 2, 3)] == pytest.approx([59 / 9, 50 / 9, 41 / 9, 140 / 27])


@pytest.mark.parametrize("c", [0, 1])
def test_fraction_calculation_agrees_with_the_float_backward_recursion(c):
    hand = H.solve(c)
    model = A.Model(L=0, pmf1=D.three_point_pmf(), h=1.0, p=3.0, c=float(c))
    bw = A.backward(3, model)
    assert [r.S for r in hand.rounds] == bw.S[1:]
    for r in hand.rounds:
        for x in range(-2, 4):
            assert float(r.V[x]) == pytest.approx(bw.V[r.n][model.index(x)], abs=1e-12), (c, r.n, x)


def test_fraction_values_of_the_hand_example():
    h0, h1 = H.solve(0), H.solve(1)
    assert [str(h0.G[y]) for y in range(4)] == ["3", "4/3", "1", "2"]
    assert [str(h1.rounds[0].H[y]) for y in range(4)] == ["3", "7/3", "3", "5"]
    assert [str(h1.rounds[1].H[y]) for y in range(4)] == ["19/3", "14/3", "41/9", "58/9"]
    assert str(h1.rounds[2].H[3]) == "221/27" and h0.ratio == pytest.approx(0.75)
    assert (h0.quantile, h1.quantile_c) == (2, 1)          # Verhältnis 3/4 -> 2; mit c = 1: (3 - 1)/4 = 1/2 -> 1


def test_first_round_is_the_newsvendor_quantile():
    """n = 1: ohne Folgeperiode ist das Niveau das Quantil zum Verhältnis (p - c)/(p + h), auch mit Lieferzeit."""
    for L in (0, 2):
        for c in (0, 3):
            m = make_model(L=L, mean=3, ph=9, c=c)
            q = P.poisson_quantile(P.critical_ratio(m.p, m.h, m.c), 3 * (L + 1))
            assert A.backward(1, m).S[1] == q, (L, c)


def test_constant_demand_has_level_equal_to_demand_and_zero_cost():
    pmf = np.array([0.0, 0.0, 1.0])
    m = A.Model(L=0, pmf1=pmf, h=1.0, p=1.0)
    bw = A.backward(4, m)
    assert bw.S[1:] == [2, 2, 2, 2] and bw.V[4][m.index(2)] == pytest.approx(0.0)


def test_action_is_to_fill_up_to_the_level(mini):
    """Struktur: in jedem Zustand ist die beste Bestellung max(S_n - x, 0), nicht nur im Mittel."""
    bw = A.backward(3, mini)
    for n in (1, 2, 3):
        assert np.array_equal(mini.x[bw.action[n]], np.maximum(mini.x, bw.S[n]))


def test_model_rejects_purchase_price_at_or_above_the_penalty():
    with pytest.raises(ValueError):
        A.Model(L=0, pmf1=D.three_point_pmf(), p=3.0, c=3.0)
    with pytest.raises(ValueError):
        A.Model(L=0, pmf1=D.three_point_pmf(), p=3.0, c=4.0)
    A.Model(L=0, pmf1=D.three_point_pmf(), p=3.0, c=2.999)   # knapp darunter ist erlaubt


def test_model_rejects_invalid_input():
    for kwargs in ({"L": -1}, {"L": 0, "h": 0.0}, {"L": 0, "p": 0.0}, {"L": 0, "c": -1.0}):
        with pytest.raises(ValueError):
            A.Model(pmf1=D.three_point_pmf(), **kwargs)
    with pytest.raises(ValueError):
        A.backward(0, A.Model(L=0, pmf1=D.three_point_pmf()))


def test_index_outside_the_grid_is_an_error(mini):
    with pytest.raises(ValueError):
        mini.index(mini.hi + 1)
    with pytest.raises(ValueError):
        mini.index(mini.lo - 1)


def test_stationary_from_by_hand():
    assert A.stationary_from([None, 1, 2, 2, 2]) == 2
    assert A.stationary_from([None, 2, 2, 2]) == 1
    assert A.stationary_from([None, 2, 1, 2]) == 3        # die Folge fällt dazwischen ab: erst ab der letzten Abweichung
    assert A.stationary_from([None, 2, 2, 3], limit=2) is None
    assert A.stationary_from([None, 1, 2, 3], limit=3) == 3


# ---------------------------------------------------------------- Eigenschaften

def test_value_does_not_decrease_with_the_penalty():
    values = [A.backward(10, make_model(L=1, mean=3, ph=ph)).V[10][0 - make_model(L=1, mean=3, ph=ph).lo] for ph in (1, 2, 4, 9, 19)]
    assert all(b >= a for a, b in zip(values, values[1:]))


def test_level_grows_with_lead_time_mean_and_penalty():
    def level(L, mean, ph):
        return A.backward(3, make_model(L=L, mean=mean, ph=ph)).S[3]
    assert [level(L, 3, 9) for L in range(4)] == sorted(level(L, 3, 9) for L in range(4))
    assert [level(1, m, 9) for m in range(2, 6)] == sorted(level(1, m, 9) for m in range(2, 6))
    assert [level(1, 3, ph) for ph in (1, 2, 4, 9, 19)] == sorted(level(1, 3, ph) for ph in (1, 2, 4, 9, 19))


def test_doubling_h_and_p_does_not_change_the_level_and_doubles_the_costs():
    pmf = D.poisson_pmf(3.0, 56)
    a = A.backward(8, A.Model(L=1, pmf1=pmf, h=1.0, p=9.0))
    b = A.backward(8, A.Model(L=1, pmf1=pmf, h=2.0, p=18.0))
    assert a.S == b.S
    assert b.V[8] == pytest.approx(2 * a.V[8])


def test_value_falls_in_x_up_to_the_level():
    m = make_model(L=1, mean=3, ph=9)
    bw = A.backward(6, m)
    seg = bw.V[6][: m.index(bw.S[6]) + 1]
    assert np.all(np.diff(seg) <= 1e-12)


def test_startup_cost_has_the_closed_form_p_mean_L_L_plus_1_over_2():
    for L in range(4):
        for mean in (2, 3, 5):
            m = make_model(L=L, mean=mean, ph=9)
            assert E.startup_cost(m) == pytest.approx(9.0 * mean * L * (L + 1) / 2, rel=1e-9)


def test_startup_cost_is_zero_without_lead_time(mini):
    assert E.startup_cost(mini) == 0.0


# ---------------------------------------------------------------- feste Politik

def test_fixed_level_equals_the_optimum_without_purchase_price(mini):
    bw = A.backward(3, mini)
    fixed = E.evaluate_fixed(3, mini, 2)
    assert fixed[3] == pytest.approx(bw.V[3])


def test_fixed_level_costs_more_in_the_last_period_with_purchase_price(mini_c1):
    """Handrechnung: fest S = 2 bei n = 1: c·y + G(y) = 2 + 1 = 3 gegen das Optimum 7/3 bei y = 1; Differenz 2/3."""
    bw = A.backward(1, mini_c1)
    fixed = E.evaluate_fixed(1, mini_c1, 2)
    i = mini_c1.index(0)
    assert fixed[1][i] == pytest.approx(3.0) and bw.V[1][i] == pytest.approx(7 / 3)
    assert fixed[1][i] - bw.V[1][i] == pytest.approx(2 / 3)


def test_fixed_level_outside_the_grid_is_an_error(mini):
    with pytest.raises(ValueError):
        E.evaluate_fixed(3, mini, mini.hi + 5)


def test_total_cost_adds_startup_and_controllable_costs():
    m = make_model(L=2, mean=3, ph=9)
    bw = A.backward(5, m)
    assert E.total_cost(m, bw.V[5]) == pytest.approx(81.0 + bw.V[5][m.index(0)])


# ---------------------------------------------------------------- Quantil

def test_quantile_by_hand():
    cdf = np.array([1 / 3, 2 / 3, 1.0])
    assert P.quantile_level(0.75, cdf) == 2
    assert P.quantile_level(0.5, cdf) == 1
    assert P.quantile_level(0.2, cdf) == 0


def test_quantile_ties_take_the_smaller_level():
    """Gleichstand zweier Niveaus: F(1) = 2/3 genau gleich dem Verhältnis (p = 2, h = 1): G(1) = G(2), die Rückwärtsrechnung wählt das kleinere, ebenso die Formel."""
    cdf = np.array([1 / 3, 2 / 3, 1.0])
    assert P.quantile_level(2 / 3, cdf) == 1
    m = A.Model(L=0, pmf1=D.three_point_pmf(), h=1.0, p=2.0)
    assert m.G[m.index(1)] == pytest.approx(m.G[m.index(2)])
    assert A.backward(3, m).S[1:] == [1, 1, 1]


def test_quantile_errors():
    with pytest.raises(ValueError):
        P.quantile_level(0.0, np.array([0.5, 1.0]))
    with pytest.raises(ValueError):
        P.quantile_level(1.0, np.array([0.5, 1.0]))
    with pytest.raises(ValueError):
        P.quantile_level(0.99, np.array([0.5, 0.6]))
    with pytest.raises(ValueError):
        P.critical_ratio(0.0, 0.0)


def test_critical_ratio_values_and_order_quantity():
    assert P.critical_ratio(9, 1) == pytest.approx(0.9)
    assert P.critical_ratio(9, 1, 3) == pytest.approx(0.6)
    assert (P.order_quantity(2, 5), P.order_quantity(5, 5), P.order_quantity(7, 5)) == (3, 0, 0)


# ---------------------------------------------------------------- Simulation

def test_simulation_is_reproducible_and_depends_on_the_seed():
    kwargs = dict(L=1, mean=3.0, h=1.0, p=9.0, c=0.0, paths=500)
    levels = S.levels_for_fixed(9, 5, 1)
    a = S.simulate(levels, seed=5, **kwargs)
    assert np.array_equal(a, S.simulate(levels, seed=5, **kwargs))
    assert not np.array_equal(a, S.simulate(levels, seed=6, **kwargs))


def test_simulation_without_orders_costs_p_times_the_cumulative_demand():
    """Nie bestellen: der Rückstand wächst, Kosten je Periode t sind p · (Summe der Nachfragen bis t); Erwartung p · mean · T (T + 1) / 2."""
    T = 4
    costs = S.simulate([None] * T, L=0, mean=3.0, h=1.0, p=9.0, c=0.0, paths=20000, seed=3)
    mean, se = S.summary(costs)
    assert abs(mean - 9.0 * 3.0 * T * (T + 1) / 2) < 4 * se


def test_simulation_buys_up_to_the_level_in_the_first_period():
    """Eine Periode, Lieferzeit 0, Niveau 10, c = 2: Einkauf 20, dazu Lager- und Rückstandskosten; das Mittel liegt über 20."""
    costs = S.simulate([10], L=0, mean=3.0, h=1.0, p=9.0, c=2.0, paths=2000, seed=1)
    assert costs.min() >= 20.0 and costs.mean() > 20.0


def test_simulation_rejects_a_single_path():
    with pytest.raises(ValueError):
        S.simulate([1], L=0, mean=3.0, h=1.0, p=9.0, c=0.0, paths=1, seed=1)


def test_poisson_draws_by_inversion_hand_values():
    cdf = np.array([0.25, 0.75, 1.0])
    assert S.poisson_draws(cdf, np.array([0.0, 0.24, 0.25, 0.74, 0.75, 0.999])).tolist() == [0, 0, 1, 1, 2, 2]


def test_level_lists_per_calendar_period():
    assert S.levels_for_fixed(7, 3, 2) == [7, 7, 7, None, None]
    assert S.levels_for_optimal([None, 4, 5, 6], 3, 1) == [6, 5, 4, None]      # in Periode t sind noch N - t Entscheidungen offen


def test_z_score():
    assert S.z_score(11.0, 0.5, 10.0) == pytest.approx(2.0) and S.z_score(1.0, 0.0, 0.0) == 0.0
