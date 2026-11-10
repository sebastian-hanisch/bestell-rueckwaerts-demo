"""Das Handbeispiel in exakter Bruchrechnung (fractions), unabhängig von numpy und von `brw_algorithm`.

Nachfrage D = 0, 1, 2 mit je 1/3, h = 1, p = 3, Lieferzeit 0, drei Perioden rückwärts; Einkaufspreis c = 0 oder 1 (Rest am Ende unbewertet).
Rekursion: H_n(y) = c y + G(y) + (1/3) sum_d V_{n-1}(y - d), V_n(x) = min_{y >= x} H_n(y) - c x, V_0 = 0.
Die App zeigt die Tabellen und die Rechenzeile je Runde; der Test vergleicht sie mit `brw_algorithm.backward` (Gleitkomma)."""

from dataclasses import dataclass
from fractions import Fraction as F

import brw_constants as C

_X_LO, _X_HI = -10, 10          # Positionen der Rechnung; V außerhalb wird am unteren Rand abgeschnitten (nicht erreichbar)
_Y_LO, _Y_HI = -6, 8            # Niveaus, über die das Minimum gesucht wird (G ist konvex, das Minimum liegt weit innerhalb)


@dataclass(frozen=True)
class Round:
    n: int
    H: dict          # y -> H_n(y) für alle y im Suchbereich
    S: int           # kleinstes Minimum von H_n
    V: dict          # x -> V_n(x) für alle x im Gitter
    line: str        # die Rechenzeile für H_n(S) mit eingesetzten Zahlen


@dataclass(frozen=True)
class HandExample:
    c: int
    G: dict          # y -> G(y)
    G_terms: dict    # y -> Summanden von 3 G(y) als Text, z. B. "1 + 0 + 3"
    ratio: F         # p / (p + h)
    cdf: dict        # k -> F(k)
    quantile: int    # kleinstes S mit F(S) >= ratio (c = 0)
    ratio_c: F       # (p - c) / (p + h)
    quantile_c: int  # das Quantil zu ratio_c (Niveau der letzten Periode)
    rounds: list     # Round für n = 1..3


def _demand() -> dict:
    return {d: F(1, len(C.HAND_DEMAND)) for d in C.HAND_DEMAND}


def _G(y: int, demand: dict, h: int, p: int) -> F:
    return sum(pr * (h * max(y - d, 0) + p * max(d - y, 0)) for d, pr in demand.items())


def _quantile(ratio: F, demand: dict) -> tuple[int, dict]:
    cdf, total = {}, F(0)
    for d, pr in demand.items():
        total += pr
        cdf[d] = total
    return min(k for k, v in cdf.items() if v >= ratio), cdf


def solve(c: int) -> HandExample:
    """Löst das Handbeispiel exakt in Brüchen."""
    if c not in C.HAND_C_OPTIONS:
        raise ValueError(f"Einkaufspreis {c} nicht im Handbeispiel (erlaubt: {C.HAND_C_OPTIONS})")
    h, p = C.HAND_H, C.HAND_P
    demand = _demand()
    G = {y: _G(y, demand, h, p) for y in range(_Y_LO - 2, _Y_HI + 1)}
    terms = {y: " + ".join(str(h * max(y - d, 0) + p * max(d - y, 0)) for d in demand) for y in range(0, 4)}
    ratio = F(p, p + h)
    ratio_c = F(p - c, p + h)
    quantile, cdf = _quantile(ratio, demand)
    quantile_c, _ = _quantile(ratio_c, demand)
    V = {x: F(0) for x in range(_X_LO, _X_HI + 1)}
    rounds = []
    for n in range(1, C.HAND_ROUNDS + 1):
        H = {y: c * y + G[y] + sum(pr * V[max(y - d, _X_LO)] for d, pr in demand.items()) for y in range(_Y_LO, _Y_HI + 1)}
        best = min(H.values())
        S = min(y for y in H if H[y] == best)
        newV = {x: min(H[y] for y in H if y >= x) - c * x if x <= _Y_HI else V[x] for x in range(_X_LO, _X_HI + 1)}
        if n == 1:   # V_0 = 0: nur Einkauf und Periodenkosten
            line = f"H_1({S}) = {c}·{S} + G({S}) = {c * S} + {G[S]} = {H[S]}"
        else:
            parts = " + ".join(f"V_{n - 1}({S - d})" for d in demand)
            values = " + ".join(str(V[max(S - d, _X_LO)]) for d in demand)
            line = f"H_{n}({S}) = {c}·{S} + G({S}) + ({parts})/3 = {c * S} + {G[S]} + ({values})/3 = {H[S]}"
        rounds.append(Round(n, H, S, newV, line))
        V = newV
    return HandExample(c, G, terms, ratio, cdf, quantile, ratio_c, quantile_c, rounds)
