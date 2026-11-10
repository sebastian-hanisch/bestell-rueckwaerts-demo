"""Die geschlossene Regel: Aufziehniveau als Quantil der Nachfrage über die Wiederbeschaffungszeit L + 1.

Satz der Demo (Modell: Rückstand, Poisson-Nachfrage, Einkaufspreis 0, keine Bestellgrenze): S ist das kleinste Niveau, bei dem die
Verteilungsfunktion der Nachfrage über L + 1 Perioden mindestens p / (p + h) beträgt. Mit Einkaufspreis c und unbewertetem Rest gilt das für
die letzte Periode mit dem Verhältnis (p - c) / (p + h) (Messbefund, `tests/test_claims.py`). Die Verteilungsfunktion wird hier selbst
aus der Poisson-Formel aufsummiert, ohne die Faltung und ohne die Bellman-Rechnung."""

from math import exp, lgamma, log

import numpy as np


def critical_ratio(p: float, h: float, c: float = 0.0) -> float:
    """Kritisches Verhältnis (p - c) / (p + h); ohne Einkaufspreis p / (p + h)."""
    if p + h <= 0:
        raise ValueError("p + h muss positiv sein")
    return (p - c) / (p + h)


def poisson_cdf_table(mean: float, kmax: int) -> np.ndarray:
    """Verteilungsfunktion P(D <= k) der Poisson-Verteilung für k = 0..kmax, aus der Formel aufsummiert."""
    if mean <= 0:
        raise ValueError("Mittel muss positiv sein")
    total = 0.0
    out = []
    for k in range(kmax + 1):
        total += exp(-mean + k * log(mean) - lgamma(k + 1.0))
        out.append(total)
    return np.array(out)


def quantile_level(ratio: float, cdf: np.ndarray) -> int:
    """Kleinstes k mit F(k) >= ratio für eine Verteilungsfunktion in Tabellenform (k = 0, 1, ...)."""
    if not 0 < ratio < 1:
        raise ValueError("Das kritische Verhältnis muss zwischen 0 und 1 liegen")
    cdf = np.asarray(cdf)
    idx = int(np.searchsorted(cdf, ratio - 1e-12, side="left"))   # F(k) = ratio gilt als erreicht (Gleichstand zweier Niveaus: das kleinere)
    if idx >= len(cdf):
        raise ValueError("Die Tabelle der Verteilungsfunktion reicht nicht bis zum kritischen Verhältnis")
    return idx


def poisson_quantile(ratio: float, mean_total: float) -> int:
    """Quantil der Poisson-Verteilung mit Mittel mean_total (= (L + 1) mal Mittel einer Periode)."""
    kmax = int(mean_total + 12 * mean_total ** 0.5 + 40)
    return quantile_level(ratio, poisson_cdf_table(mean_total, kmax))


def order_quantity(position: int, level: int) -> int:
    """Bestellung bis zum Niveau: max(Niveau - Position, 0)."""
    return max(level - position, 0)
