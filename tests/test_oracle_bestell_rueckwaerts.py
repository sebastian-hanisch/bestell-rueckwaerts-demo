"""Orakel-Tests: die Rückwärtsrechnung gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12).

(a) Niveau der Rückwärtsrechnung gegen scipy (`poisson.ppf`) und gegen die Aufzählung von G (kleines Raster; der große Lauf mit 80 Zellen
    und 40 Rest-Perioden steht in tests/test_claims.py und in tools/measure_grid.py).
(b) Rechnung mit dem **vollen Zustand** (Bestand und jede Bestellung unterwegs) im endlichen Horizont gegen die Bestandspositions-Rechnung
    (eigener Code in diesem Test, ohne `brw_algorithm`): gleicher Wert, und die Regel „bis S_n auffüllen“ ist in jedem Zustand im Wert optimal.
(c) Exakter Gesamtwert gegen eine Simulation, die in diesem Test mit numpy (`default_rng`, `poisson`) und einer Liste von Bestellungen neu
    geschrieben ist (Toleranz in Standardfehlern, nicht exakt).
(d) Die Handrechnung in Brüchen (`fractions`) steht in tests/test_algorithm.py gegen `brw_hand`."""

import numpy as np
import pytest

import brw_algorithm as A
import brw_demand as D
import brw_evaluate as E
from brw_evaluation import make_model


# ---------------------------------------------------------------- (a) Quantil und Aufzählung

def test_level_equals_scipy_quantile_and_enumeration_on_a_small_grid():
    stats = pytest.importorskip("scipy.stats")
    cells = 0
    for L in range(4):
        for ph in (1, 4, 9, 19):
            for mean in (2, 3, 5):
                m = make_model(L=L, mean=mean, ph=ph)
                bw = A.backward(12, m)
                ppf = int(stats.poisson.ppf(ph / (ph + 1.0), mean * (L + 1)))
                enum = int(m.x[int(np.argmin(m.G))])                      # Aufzählung: das (erste) Minimum von G über das ganze Gitter
                assert set(bw.S[1:]) == {ppf} and enum == ppf, (L, ph, mean)
                cells += 1
    assert cells == 48


def test_period_cost_equals_scipy_expectation():
    stats = pytest.importorskip("scipy.stats")
    m = make_model(L=2, mean=3, ph=9)                                       # Nachfrage über 3 Perioden: Poisson(9)
    d = np.arange(0, 120)
    pmf = stats.poisson.pmf(d, 9.0)
    for y in (0, 5, 9, 13, 25):
        expected = float((pmf * (np.maximum(y - d, 0) + 9.0 * np.maximum(d - y, 0))).sum())
        assert m.G[m.index(y)] == pytest.approx(expected, rel=1e-10), y


def test_purchase_price_last_period_level_equals_scipy_quantile():
    stats = pytest.importorskip("scipy.stats")
    for L in (0, 3):
        for c in (1, 3, 5):
            m = make_model(L=L, mean=3, ph=9, c=c)
            assert A.backward(1, m).S[1] == int(stats.poisson.ppf((9 - c) / 10.0, 3 * (L + 1))), (L, c)


# ---------------------------------------------------------------- (b) voller Zustand

class FullState:
    """Rückwärtsrechnung mit dem vollen Zustand (net, o_1, ..., o_{L-1}); Bestellungen 0..Q; Nachfrage pmf14 (Poisson-Mittel 3 bis 14, Rest auf 14).

    Zeitablauf: Zustand zu Beginn der Entscheidung, die Bestellung a kommt nach L Perioden an (o_1 kommt zu Beginn der nächsten Periode an).
    L = 0: Kosten auf net + a - d; sonst auf net - d, danach net' = net - d + o_1 und Vektor (o_2, ..., o_{L-1}, a)."""

    def __init__(self, L, c, p, Q=20, xlo=-45, xhi=20, mean=3.0, dmax=14):
        self.L, self.c, self.p, self.Q, self.xlo, self.xhi = L, c, p, Q, xlo, xhi
        self.pmf = D.poisson_pmf(mean, dmax)
        self.dims = [xhi - xlo + 1] + [Q + 1] * max(L - 1, 0)
        grids = np.indices(self.dims).reshape(len(self.dims), -1)
        self.x = grids[0] + xlo
        self.o = grids[1:]                                                  # Form (L - 1, Zustände)
        self.pos = self.x + (self.o.sum(axis=0) if L > 1 else 0)
        self.size = int(np.prod(self.dims))

    def index(self, x, o):
        i = np.clip(x, self.xlo, self.xhi) - self.xlo
        for k in range(len(o)):
            i = i * (self.Q + 1) + o[k]
        return i

    def q_values(self, V):
        """Q[a, Zustand] = Kosten dieser Periode + E V(nächster Zustand) bei Bestellung a."""
        L = self.L
        out = np.empty((self.Q + 1, self.size))
        for a in range(self.Q + 1):
            acc = np.full(self.size, self.c * a, dtype=float)
            for d, pr in enumerate(self.pmf):
                if L == 0:
                    net = self.x + a - d
                    nxt = self.index(net, [])
                elif L == 1:
                    net = self.x - d
                    nxt = self.index(net + a, [])
                else:
                    net = self.x - d
                    nxt = self.index(net + self.o[0], list(self.o[1:]) + [np.full(self.size, a)])
                acc += pr * (self.hp(net) + V[nxt])
            out[a] = acc
        return out

    def hp(self, net):
        return 1.0 * np.maximum(net, 0) + self.p * np.maximum(-net, 0)


@pytest.mark.parametrize("L", [0, 1, 2, 3])
@pytest.mark.parametrize("c", [0, 3])
def test_full_state_recursion_equals_the_position_recursion(L, c):
    """Wert bei Start (Bestand 0, nichts unterwegs) über N + L Kalenderperioden = Anlaufkosten + V_N(0) der Positions-Rechnung; die Regel ist überall im Wert optimal."""
    N = 3
    full = FullState(L=L, c=c, p=9.0)
    model = A.Model(L=L, pmf1=D.poisson_pmf(3.0, 14), h=1.0, p=9.0, c=float(c))
    bw = A.backward(N, model)
    V = np.zeros(full.size)
    start = int(full.index(np.array([0]), [np.array([0])] * max(L - 1, 0))[0])
    worst_gap, rule_bad, rule_checked = 0.0, 0, 0
    for k in range(1, N + L + 1):
        Q = full.q_values(V)
        Vk = Q.min(axis=0)
        n = k - L                                                           # Zahl der noch sinnvollen Entscheidungen
        if n >= 1:
            expected = E.startup_cost(model) + float(bw.V[n][model.index(0)])
            worst_gap = max(worst_gap, abs(Vk[start] - expected))
            S = bw.S[n]
            rule = np.clip(S - full.pos, 0, full.Q)
            usable = (S - full.pos <= full.Q) & (full.x >= -20) & (full.pos <= full.xhi - 3)
            val = Q[rule, np.arange(full.size)]
            rule_checked += int(usable.sum())
            rule_bad += int((val[usable] > Vk[usable] + 1e-8).sum())
        V = Vk
    assert worst_gap < 1e-9, worst_gap
    assert rule_checked >= 50 and rule_bad == 0, (rule_checked, rule_bad)


# ---------------------------------------------------------------- (c) Simulation

def _simulate_with_numpy(levels, *, L, mean, p, c, paths, seed):
    """Unabhängige Simulation: Bestand, Rückstand und eine Liste der Bestellungen unterwegs je Pfad; numpy-Erzeuger, Python-Schleife je Periode."""
    rng = np.random.default_rng(seed)
    total = np.zeros(paths)
    for j in range(paths):
        inventory, backlog, pipeline, cost = 0, 0, [0] * L, 0.0
        for level in levels:
            if L > 0:
                arrived = pipeline.pop(0)                                   # trifft zu Beginn der Periode ein: erst Rückstand abbauen, dann Lager
                use = min(arrived, backlog)
                backlog -= use
                inventory += arrived - use
            position = inventory - backlog + sum(pipeline)
            order = 0 if level is None else max(level - position, 0)
            cost += c * order
            if L > 0:
                pipeline.append(order)
            else:
                use = min(order, backlog)
                backlog -= use
                inventory += order - use
            demand = int(rng.poisson(mean))
            served = min(inventory, demand)
            inventory -= served
            backlog += demand - served
            cost += 1.0 * inventory + p * backlog
        total[j] = cost
    return total


@pytest.mark.parametrize("L,c", [(0, 0), (2, 3)])
def test_exact_total_cost_agrees_with_an_independent_simulation(L, c):
    N, paths = 12, 6000
    model = make_model(L=L, mean=3, ph=9, c=c)
    bw = A.backward(N, model)
    level = int(model.x[int(np.argmin(model.G))])
    fixed = E.evaluate_fixed(N, model, level)
    i0 = model.index(0)
    cases = [
        ("Rückwärtsrechnung", [bw.S[N - t] if t < N else None for t in range(N + L)], E.startup_cost(model) + float(bw.V[N][i0])),
        ("festes Niveau", [level if t < N else None for t in range(N + L)], E.startup_cost(model) + float(fixed[N][i0])),
    ]
    for name, levels, exact in cases:
        for seed in (101, 102):
            costs = _simulate_with_numpy(levels, L=L, mean=3.0, p=9.0, c=float(c), paths=paths, seed=seed)
            se = costs.std(ddof=1) / np.sqrt(paths)
            assert abs(costs.mean() - exact) < 4 * se, (name, L, c, seed, costs.mean(), exact, se)
