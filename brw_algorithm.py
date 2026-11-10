"""Kern der Demo: die exakte Rückwärtsrechnung (Bellman) für ein Ein-Artikel-Lager mit Rückstand und Lieferzeit.

Zeitablauf einer Periode t (alle Mengen ganzzahlig):
  1. Die Bestellung der Periode t - L trifft ein (bei L = 0 gleich die eigene).
  2. Es wird bestellt; die Bestellung steht für die Nachfrage der Periode t + L bereit.
  3. Die Nachfrage D_t fällt. Kosten am Periodenende: h je Stück Bestand, p je Stück Rückstand, c je bestelltem Stück.

Zustand der Rechnung ist die **Bestandsposition** x = Bestand + unterwegs - Rückstand (eine Zahl statt des ganzen Bestellvektors; die Gegenprobe mit
dem vollen Zustand steht in tests/test_oracle_bestell_rueckwaerts.py). Wer in Periode t bis y auffüllt, zahlt für die Periode t + L
G(y) = E[ h (y - D)^+ + p (D - y)^+ ] mit D = Nachfrage der L + 1 Perioden t .. t + L (`brw_cost.period_cost`).

Bellman-Gleichung bei n noch zu entscheidenden Perioden (V_0 = 0):
    H_n(y) = c y + G(y) + E[ V_{n-1}(y - D) ]        (Wert nach der Bestellung bis y, ohne den Anteil - c x)
    V_n(x) = min_{y >= x} H_n(y) - c x
Das kleinste Minimum von H_n ist das Aufziehniveau S_n; die beste Bestellung ist max(S_n - x, 0).

Es gibt keine Bestellgrenze. Das Gitter der Positionen reicht unten bis 10 unter das Niveau, das die größte Nachfrage einer Periode erreichen
kann, und oben bis 3 über das 1 - 1e-9-Quantil der Nachfrage über L + 1 Perioden; Positionen unter dem Gitter werden am Rand abgeschnitten,
die Politik erreicht sie nie (Randmasse 0, `edge_mass_is_zero`)."""

from dataclasses import dataclass

import numpy as np

from brw_cost import period_cost
from brw_demand import lead_pmf


class Model:
    """Alle Einstellungen mit Schlüsselwörtern (nie positional): Lieferzeit L, Nachfrage einer Periode pmf1, Kosten h, p, c."""

    def __init__(self, *, L: int, pmf1, h: float = 1.0, p: float = 9.0, c: float = 0.0):
        if L < 0:
            raise ValueError("Lieferzeit L darf nicht negativ sein")
        if h <= 0 or p <= 0:
            raise ValueError("h und p müssen positiv sein")
        if c < 0:
            raise ValueError("Einkaufspreis c darf nicht negativ sein")
        if c >= p:
            raise ValueError("Einkaufspreis c >= Strafkosten p: die letzte Periode bestellt nie, das Niveau fällt unter das Gitter; nicht gerechnet")
        self.L, self.h, self.p, self.c = int(L), float(h), float(p), float(c)
        self.pmf1 = np.asarray(pmf1, dtype=float)
        self.dmax1 = len(self.pmf1) - 1
        self.pmfL = lead_pmf(self.pmf1, self.L + 1)
        cdf = np.cumsum(self.pmfL)
        self.hi = int(np.searchsorted(cdf, 1 - 1e-9)) + 3
        self.lo = -(self.dmax1 + 10)
        self.x = np.arange(self.lo, self.hi + 1)
        self.G = period_cost(self.x, self.pmfL, self.h, self.p)

    def index(self, x: int) -> int:
        """Gitterindex der Bestandsposition x."""
        if not self.lo <= x <= self.hi:
            raise ValueError(f"Position {x} liegt außerhalb des Gitters {self.lo}..{self.hi}")
        return int(x - self.lo)


@dataclass(frozen=True)
class Step:
    V: np.ndarray        # V_n(x) für jede Position im Gitter
    S: int               # Aufziehniveau S_n (kleinstes Minimum von H_n innerhalb der Toleranz)
    action: np.ndarray   # Gitterindex des besten y je Position x
    gap: float           # Abstand zwischen bestem und zweitbestem H_n-Wert (Gleichstandsprüfung)


@dataclass(frozen=True)
class Backward:
    V: list              # V[n] für n = 0..N (V[0] = 0)
    S: list              # S[n] für n = 1..N (S[0] ist None)
    action: list         # action[n] für n = 1..N
    gap: list            # gap[n] für n = 1..N


def expect_next(V: np.ndarray, model: Model) -> np.ndarray:
    """E[ V(y - D) ] für jedes y im Gitter; Positionen unter dem Gitter werden am unteren Rand abgeschnitten."""
    nx = len(model.x)
    out = np.zeros(nx)
    for d, pr in enumerate(model.pmf1):
        if pr < 1e-300:
            continue
        out += pr * V[np.clip(np.arange(nx) - d, 0, nx - 1)]
    return out


def bellman_step(V_prev: np.ndarray, model: Model, tol: float = 1e-9) -> Step:
    """Ein Schritt rückwärts: aus V_{n-1} werden V_n, S_n und die beste Bestellung je Position."""
    H = model.c * model.x + model.G + expect_next(V_prev, model)
    nx = len(model.x)
    V = np.empty(nx)
    best = np.empty(nx, dtype=int)
    for i in range(nx):
        seg = H[i:]
        m = seg.min()
        best[i] = i + int(np.argmax(seg <= m + tol))   # kleinstes Minimum innerhalb der Toleranz
        V[i] = m - model.c * model.x[i]
    S = int(model.x[int(np.argmax(H <= H.min() + tol))])
    srt = np.sort(H)
    gap = float(srt[1] - srt[0]) if len(srt) > 1 else float("inf")
    return Step(V, S, best, gap)


def backward(N: int, model: Model) -> Backward:
    """V_0..V_N und S_1..S_N: S[n] gilt, wenn noch n Perioden zu entscheiden sind (n = 1 ist die letzte)."""
    if N < 1:
        raise ValueError("N muss mindestens 1 sein")
    V = np.zeros(len(model.x))
    Vs, Ss, As, gaps = [V], [None], [None], [None]
    for _ in range(N):
        step = bellman_step(V, model)
        V = step.V
        Vs.append(V)
        Ss.append(step.S)
        As.append(step.action)
        gaps.append(step.gap)
    return Backward(Vs, Ss, As, gaps)


def stationary_from(levels: list, limit: int | None = None) -> int | None:
    """Kleinste Zahl n, ab der S_m = S_limit für alle m >= n gilt (Index 1 = letzte Periode); None, wenn schon die größte Restzahl abweicht.

    `levels` ist S[1..N] mit None an Stelle 0 (wie `Backward.S`); `limit` ist der Grenzwert, Standard ist das Niveau bei der größten Restzahl."""
    seq = levels[1:]
    target = seq[-1] if limit is None else limit
    n = None
    for i in range(len(seq) - 1, -1, -1):
        if seq[i] == target:
            n = i + 1
        else:
            break
    return n


def edge_mass_is_zero(model: Model, levels: list) -> bool:
    """Randmasse unten: die niedrigste Position, die die Politik je erreicht, ist min(S_n) - dmax1, und sie liegt über dem Gitterrand."""
    lowest_level = min(s for s in levels[1:] if s is not None)
    return lowest_level - model.dmax1 > model.lo
