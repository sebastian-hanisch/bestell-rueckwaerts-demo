"""Periodenkosten: Lager- und Rückstandskosten als Funktion des Bestands nach der Bestellung."""

import numpy as np


def period_cost(y, pmf: np.ndarray, h: float, p: float) -> np.ndarray:
    """G(y) = E[ h (y - D)^+ + p (D - y)^+ ] für jedes ganzzahlige y im Array; D hat die Verteilungstabelle pmf über 0..dmax."""
    y = np.atleast_1d(np.asarray(y))[:, None]
    d = np.arange(len(pmf))[None, :]
    return (np.asarray(pmf)[None, :] * (h * np.maximum(y - d, 0) + p * np.maximum(d - y, 0))).sum(axis=1)
