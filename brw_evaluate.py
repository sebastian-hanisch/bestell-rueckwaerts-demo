"""Exakter Wert einer festen Politik und die nicht steuerbaren Anlaufkosten.

`evaluate_fixed` rechnet die erwarteten Kosten der festen Regel „bis S auffüllen“ in jeder der noch n Perioden im selben Modell
und auf demselben Gitter wie die Rückwärtsrechnung (`brw_algorithm`), aber ohne zu minimieren."""

import numpy as np

from brw_algorithm import Model, expect_next
from brw_cost import period_cost
from brw_demand import lead_pmf


def evaluate_fixed(N: int, model: Model, S: int) -> list:
    """V^fix_n(x) für n = 0..N: erwartete steuerbare Kosten der festen Politik „bis S auffüllen“ bei Position x und n Rest-Perioden."""
    if N < 1:
        raise ValueError("N muss mindestens 1 sein")
    model.index(S)   # S muss im Gitter liegen
    nx = len(model.x)
    target = np.maximum(np.arange(nx), S - model.lo)      # Gitterindex von y = max(x, S)
    y = model.x[target]
    V = np.zeros(nx)
    out = [V]
    for _ in range(N):
        EV = expect_next(V, model)
        V = model.c * (y - model.x) + model.G[target] + EV[target]
        out.append(V)
    return out


def startup_cost(model: Model) -> float:
    """Kosten der ersten L Perioden bei Anfangsposition 0 und nichts unterwegs: Die erste Bestellung kommt erst nach L Perioden an,
    bis dahin ist der Bestand 0 und jede Nachfrage Rückstand. Nicht steuerbar, in V_n(0) nicht enthalten."""
    total = 0.0
    for t in range(1, model.L + 1):
        total += float(period_cost(np.array([0]), lead_pmf(model.pmf1, t), model.h, model.p)[0])
    return total


def total_cost(model: Model, V: np.ndarray, x0: int = 0) -> float:
    """Gesamtkosten über N + L Kalenderperioden: Anlaufkosten plus steuerbare Kosten V_N(x0) bei Anfangsposition x0."""
    return startup_cost(model) + float(V[model.index(x0)])
