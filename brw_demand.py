"""Nachfrage: Poisson-Verteilung, Faltung über die Wiederbeschaffungszeit und die Dreipunkt-Nachfrage des Handbeispiels.

Alle Verteilungen sind Tabellen über 0, 1, ..., dmax; bei der Poisson-Verteilung liegt die Restmasse oberhalb von dmax auf dmax
(Abschneidemasse, `truncation_mass`)."""

from math import exp, lgamma, log

import numpy as np


def dmax_for(mean: float) -> int:
    """Obere Abschneidegrenze der Poisson-Nachfrage einer Periode: das 12-Fache des Mittels plus 20."""
    return int(12 * mean + 20)


def poisson_pmf(mean: float, dmax: int) -> np.ndarray:
    """Poisson(mean) auf 0..dmax; die Restmasse oberhalb von dmax wird auf dmax gelegt (Summe genau 1)."""
    if mean <= 0:
        raise ValueError("Mittel muss positiv sein")
    if dmax < 0:
        raise ValueError("dmax darf nicht negativ sein")
    k = np.arange(dmax + 1)
    lp = -mean + k * log(mean) - np.array([lgamma(i + 1.0) for i in k])
    pmf = np.exp(lp)
    pmf[-1] += 1.0 - pmf.sum()
    return pmf


def truncation_mass(mean: float, dmax: int) -> float:
    """Wahrscheinlichkeit P(D > dmax) der Poisson-Nachfrage, die `poisson_pmf` auf dmax legt (Summe des Tails, ohne 1 - Summe)."""
    total = 0.0
    for k in range(dmax + 1, dmax + 400):
        total += exp(-mean + k * log(mean) - lgamma(k + 1.0))
    return total


def lead_pmf(pmf1: np.ndarray, k: int) -> np.ndarray:
    """Verteilung der Summe von k unabhängigen Nachfragen (Faltung); k = 0 ist die Nachfrage 0."""
    if k < 0:
        raise ValueError("k darf nicht negativ sein")
    out = np.array([1.0])
    for _ in range(k):
        out = np.convolve(out, pmf1)
    return out


def three_point_pmf() -> np.ndarray:
    """Nachfrage des Handbeispiels: 0, 1, 2 mit je 1/3."""
    return np.array([1 / 3, 1 / 3, 1 / 3])


def mean_of(pmf: np.ndarray) -> float:
    return float((np.arange(len(pmf)) * np.asarray(pmf)).sum())
