"""Simulation der echten Bewegung (Bestand, Rückstand, Bestellungen unterwegs), unabhängig von der Kostenfunktion G.

Die Simulation kennt weder G noch die Bestandsposition als Rechengröße der Rückwärtsrechnung: Sie bewegt Bestand und Bestellungen
Periode für Periode, erzeugt die Nachfrage aus Zufallszahlen und summiert die tatsächlich anfallenden Kosten. Der Zufall kommt aus dem
eigenen ganzzahligen Erzeuger (`brw_rng`, SplitMix64): ein Strom je Periode, abgeleitet aus dem Zufalls-Seed; Python-`hash()` und
numpy-Ströme (zwischen Versionen nicht stabil) kommen nicht vor."""

from collections import deque

import numpy as np

from brw_demand import dmax_for, poisson_pmf
from brw_rng import SplitMix64, uniform_block


def poisson_draws(cdf: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Poisson-Nachfrage durch Inversion: die kleinste Nachfrage d mit F(d) > u (u gleichverteilt auf [0, 1))."""
    return np.minimum(np.searchsorted(cdf, u, side="right"), len(cdf) - 1)


def simulate(levels: list, *, L: int, mean: float, h: float, p: float, c: float, paths: int, seed: int) -> np.ndarray:
    """Gesamtkosten je Pfad über len(levels) Perioden, Start: Bestand 0, nichts unterwegs.

    levels[t] ist das Aufziehniveau der Periode t (t = 0, 1, ...); None heißt: in dieser Periode wird nicht bestellt (die letzten L Perioden
    eines Horizonts von N + L Perioden, weil später ankommende Bestellungen nichts mehr bewirken). Bestellt wird max(Niveau - Position, 0)."""
    if paths < 2:
        raise ValueError("Mindestens 2 Pfade (sonst gibt es keinen Standardfehler)")
    cdf = np.cumsum(poisson_pmf(mean, dmax_for(mean)))
    master = SplitMix64(seed)
    net = np.zeros(paths)                                   # Bestand minus Rückstand
    pipeline = deque(np.zeros(paths) for _ in range(L))     # Bestellungen der Perioden t - L .. t - 1, älteste zuerst
    cost = np.zeros(paths)
    for level in levels:
        if L > 0:
            net = net + pipeline.popleft()                  # die Bestellung der Periode t - L trifft ein
        position = net + (sum(pipeline) if L > 1 else 0.0)  # Bestand plus unterwegs minus Rückstand
        order = np.zeros(paths) if level is None else np.maximum(level - position, 0.0)
        cost += c * order
        if L > 0:
            pipeline.append(order)
        else:
            net = net + order
        demand = poisson_draws(cdf, uniform_block(master.next(), paths)).astype(float)
        net = net - demand
        cost += h * np.maximum(net, 0.0) + p * np.maximum(-net, 0.0)
    return cost


def summary(costs: np.ndarray) -> tuple[float, float]:
    """Mittel und Standardfehler des Mittels."""
    return float(costs.mean()), float(costs.std(ddof=1) / np.sqrt(len(costs)))


def z_score(sim_mean: float, se: float, exact: float) -> float:
    """Abweichung der Simulation vom exakten Wert in Standardfehlern."""
    return (sim_mean - exact) / se if se > 0 else 0.0


def levels_for_optimal(S_by_rest: list, N: int, L: int) -> list:
    """Niveaus der Rückwärtsrechnung je Kalenderperiode t = 0..N+L-1: in Periode t sind noch N - t Entscheidungen offen."""
    return [S_by_rest[N - t] if t < N else None for t in range(N + L)]


def levels_for_fixed(S: int, N: int, L: int) -> list:
    """Das feste Niveau S in den ersten N Perioden, danach keine Bestellung."""
    return [S if t < N else None for t in range(N + L)]
