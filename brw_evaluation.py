"""Kennzahlen, Tabellen und Verdikte. Jedes Verdikt ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft st.<Art>(Text)."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import brw_algorithm as A
import brw_constants as C
import brw_demand as D
import brw_evaluate as E
import brw_policy as P
import brw_simulate as S

DATA_FILE = Path(__file__).resolve().parent / "data" / "simulation_vorgerechnet.json"


@dataclass(frozen=True)
class Settings:
    """Alle Regler mit Schlüsselwörtern (nie positional)."""

    L: int = C.DEFAULT_L
    ph: int = C.DEFAULT_PH
    mean: int = C.DEFAULT_MEAN
    c: int = C.DEFAULT_C
    n: int = C.DEFAULT_N
    paths: int = C.DEFAULT_PATHS
    seed: int = C.DEFAULT_SEED
    hand_c: int = 0


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def thousands(n: int) -> str:
    """Ganzzahl mit Punkt als Tausendertrenner."""
    return f"{n:,}".replace(",", ".")


def make_model(*, L: int, mean: float, ph: float, c: float = 0.0) -> A.Model:
    return A.Model(L=L, pmf1=D.poisson_pmf(mean, D.dmax_for(mean)), h=C.H_COST, p=float(ph), c=float(c))


@dataclass(frozen=True)
class Analysis:
    model: A.Model
    bw: A.Backward
    ratio: float          # p / (p + h)
    level: int            # Quantil zum Verhältnis p / (p + h) über L + 1 Perioden: Grenzwert der Niveaus
    level_last: int       # Quantil zum Verhältnis (p - c) / (p + h): Niveau der letzten Periode
    n_star: int | None    # ab dieser Rest-Periodenzahl ist das Niveau das Grenzniveau
    g: float              # Periodenkosten G(S) beim Grenzniveau
    controllable: float   # V_n(0): steuerbare Kosten bei n Rest-Perioden, Start Position 0
    startup: float        # Anlaufkosten der ersten L Perioden
    fixed_extra: float    # Mehrkosten des festen Niveaus gegen die Rückwärtsrechnung (absolut, bei n Perioden)
    fixed_extra_pct: float  # dieselben Mehrkosten in % der steuerbaren Kosten V_n(0) einschließlich Einkauf

    @property
    def total(self) -> float:
        return self.startup + self.controllable


def analyse(s: Settings) -> Analysis:
    if s.c >= s.ph * C.H_COST:
        raise ValueError("Einkaufspreis c >= Strafkosten p: nicht gerechnet")
    if not 1 <= s.n <= C.NMAX:
        raise ValueError(f"Rest-Perioden n = {s.n} liegt außerhalb von 1 bis {C.NMAX}")
    model = make_model(L=s.L, mean=s.mean, ph=s.ph, c=s.c)
    bw = A.backward(C.NMAX, model)
    ratio = P.critical_ratio(model.p, model.h)
    mean_total = s.mean * (s.L + 1)
    level = P.poisson_quantile(ratio, mean_total)
    level_last = P.poisson_quantile(P.critical_ratio(model.p, model.h, model.c), mean_total)
    i0 = model.index(0)
    fixed = E.evaluate_fixed(s.n, model, level)
    vo, vf = float(bw.V[s.n][i0]), float(fixed[s.n][i0])
    return Analysis(model, bw, ratio, level, level_last, A.stationary_from(bw.S, level), float(model.G[model.index(level)]), vo,
                    E.startup_cost(model), vf - vo, 100.0 * (vf / vo - 1.0) if vo > 0 else 0.0)


def level_grid(mean: int, *, rest: int = 40) -> list[dict]:
    """Zellen Lieferzeit x p/h bei c = 0: Niveau der Rückwärtsrechnung (rest Rest-Perioden) gegen das Quantil."""
    rows = []
    for L in range(C.L_MIN, C.L_MAX + 1):
        for ph in C.PH_OPTIONS:
            model = make_model(L=L, mean=mean, ph=ph)
            bw = A.backward(rest, model)
            q = P.poisson_quantile(P.critical_ratio(model.p, model.h), mean * (L + 1))
            rows.append({"L": L, "ph": ph, "dp": bw.S[rest], "quantile": q, "same": set(bw.S[1:]) == {q}})
    return rows


def equivalence_rows(s: Settings, *, rest: int = 40) -> list[dict]:
    """Alle Kombinationen (Lieferzeit, Mittel) im Reglerbereich mit demselben Produkt (L + 1) x Mittel wie die Einstellung, bei c = 0."""
    target = (s.L + 1) * s.mean
    rows = []
    for L in range(C.L_MIN, C.L_MAX + 1):
        for mean in range(C.MEAN_MIN, C.MEAN_MAX + 1):
            if (L + 1) * mean != target:
                continue
            model = make_model(L=L, mean=mean, ph=s.ph)
            bw = A.backward(rest, model)
            level = bw.S[rest]
            rows.append({"L": L, "mean": mean, "product": target, "level": level, "g": float(model.G[model.index(level)])})
    return rows


def purchase_rows(s: Settings) -> list[dict]:
    """Je Einkaufspreis c < p (bei Lieferzeit, p/h und Mittel der Einstellung): Niveaus der letzten Perioden, Stationarität, Mehrkosten des festen Niveaus."""
    rows = []
    for c in C.C_OPTIONS:
        if c >= s.ph * C.H_COST:
            continue
        a = analyse(Settings(L=s.L, ph=s.ph, mean=s.mean, c=c, n=s.n))
        rows.append({"c": c, "levels": a.bw.S[1:7], "level": a.level, "level_last": a.level_last, "n_star": a.n_star, "extra": a.fixed_extra,
                     "extra_g": a.fixed_extra / a.g, "extra_pct": a.fixed_extra_pct})
    return rows


def sim_rows(s: Settings) -> list[dict]:
    """Live-Simulation der Rückwärtsrechnung und des festen Niveaus gegen den exakten Gesamtwert (N = n Entscheidungen, Start: Bestand 0, nichts unterwegs)."""
    a = analyse(s)
    m = a.model
    out = []
    for name, levels, exact in (
        ("Rückwärtsrechnung", S.levels_for_optimal(a.bw.S, s.n, s.L), a.total),
        ("festes Niveau S", S.levels_for_fixed(a.level, s.n, s.L), a.total + a.fixed_extra),
    ):
        costs = S.simulate(levels, L=s.L, mean=s.mean, h=m.h, p=m.p, c=m.c, paths=s.paths, seed=s.seed)
        mean, se = S.summary(costs)
        out.append({"policy": name, "exact": exact, "sim": mean, "se": se, "z": S.z_score(mean, se, exact), "paths": s.paths})
    return out


def load_precomputed(path: Path = DATA_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- Verdikte

def verdict_quantile(level_dp: int, level_q: int, *, ratio: float, L: int, mean: float) -> tuple[str, str]:
    """Kernfrage: ist das Niveau der Rückwärtsrechnung (größte gerechnete Restzahl) das Quantil der Nachfrage über L + 1 Perioden?"""
    where = f"Quantil der Nachfrage über {L + 1} Periode{'n' if L else ''} (Mittel {de(mean * (L + 1), 1)}) zum Verhältnis p / (p + h) = {de(ratio, 3)}"
    if level_dp == level_q:
        return "success", f"Die Rückwärtsrechnung ergibt das Aufziehniveau **S = {level_dp}**. Das ist das {where}; beide Wege sind unabhängig gerechnet."
    return "warning", f"Die Rückwärtsrechnung ergibt S = {level_dp}, das {where} ist {level_q}: Der Satz gilt hier nicht."


def verdict_stationary(n_star: int | None, level: int, levels_first: list, c: float) -> tuple[str, str]:
    """Ab wie vielen Rest-Perioden gilt das Grenzniveau? levels_first = S_1, S_2, ... (die letzten Perioden zuerst)."""
    if n_star is None:
        return "warning", f"Bis zur größten gerechneten Restzahl erreicht die Rückwärtsrechnung das Niveau {level} nicht."
    if n_star == 1:
        return "success", (f"Schon bei **einer** Rest-Periode gilt S = {level}: Die Politik der letzten Perioden weicht nicht ab, ein festes Niveau verursacht "
                           f"keine Mehrkosten gegenüber der Rückwärtsrechnung (Einkaufspreis {de(c, 0)}, Rückstand, Poisson, keine Bestellgrenze).")
    first = ", ".join(str(v) for v in levels_first[: n_star - 1])
    return "info", (f"Die letzten {n_star - 1} Periode{'n' if n_star > 2 else ''} weichen ab: S_1 bis S_{n_star - 1} = {first}, ab {n_star} Rest-Perioden gilt "
                    f"S = {level}. Deutung, nicht gemessen: Bei Einkaufspreis {de(c, 0)} ist der Rest am Ende nichts wert, deshalb lohnt das Auffüllen in den letzten Perioden weniger.")


def verdict_grid(same: int, total: int, mean: int) -> tuple[str, str]:
    kind = "success" if same == total else "warning"
    return kind, (f"In **{same} von {total}** Zellen (Lieferzeit 0 bis 3, p/h = 1 bis 19, Mittel {mean}, Einkaufspreis 0) ist das Niveau der Rückwärtsrechnung "
                  "bei jeder der 40 Rest-Perioden das Quantil.")


def verdict_equivalence(rows: list[dict]) -> tuple[str, str]:
    """Gleiches (L + 1) x Mittel: gleiches Niveau und gleiche Periodenkosten (nur für Poisson-Nachfrage)."""
    if len(rows) < 2:
        return "info", f"Für (L + 1) · Mittel = {rows[0]['product']} gibt es im Reglerbereich keine zweite Kombination aus Lieferzeit und Mittel."
    levels = {r["level"] for r in rows}
    gs = [r["g"] for r in rows]
    if len(levels) == 1 and max(gs) - min(gs) < 1e-9:
        return "success", (f"{len(rows)} Kombinationen mit (L + 1) · Mittel = {rows[0]['product']} haben dasselbe Niveau S = {rows[0]['level']} und dieselben Periodenkosten "
                           f"{de(gs[0], 4)}: Bei Einkaufspreis 0 wirken Lieferzeit und Mittel auf Niveau und Periodenkosten nur über dieses Produkt (gilt für Poisson-Nachfrage, nicht allgemein; "
                           "die Anlaufkosten hängen an Lieferzeit und Mittel einzeln).")
    return "warning", f"Bei (L + 1) · Mittel = {rows[0]['product']} unterscheiden sich Niveau oder Periodenkosten der Kombinationen."


def verdict_purchase(row: dict, n: int) -> tuple[str, str]:
    """Mehrkosten des festen Niveaus bei Einkaufspreis c (eine Zeile aus purchase_rows) und n Rest-Perioden."""
    if row["extra"] < 1e-9:
        return "success", (f"Bei Einkaufspreis {row['c']} verursacht das feste Niveau über {n} Rest-Periode{'n' if n > 1 else ''} gegenüber der Rückwärtsrechnung "
                           "keine Mehrkosten: Die Randperioden weichen nicht ab.")
    return "info", (f"Bei Einkaufspreis {row['c']} kostet das feste Niveau S = {row['level']} über {n} Rest-Periode{'n' if n > 1 else ''} **{de(row['extra'], 2)}** mehr "
                    f"({de(row['extra_g'], 2)} Periodenkosten, {de(row['extra_pct'], 2)} % der steuerbaren Kosten einschließlich Einkauf).")


def verdict_simulation(rows: list[dict]) -> tuple[str, str]:
    """Exakter Wert gegen Simulation: im Rahmen des Zufalls, wenn jede Abweichung höchstens 3 Standardfehler beträgt."""
    worst = max(abs(r["z"]) for r in rows)
    paths = rows[0]["paths"]
    if worst <= 3:
        return "success", f"Die Simulation ({thousands(paths)} Pfade) weicht von den exakten Werten um höchstens {de(worst, 2)} Standardfehler ab: im Rahmen des Zufalls."
    return "warning", f"Die Simulation ({thousands(paths)} Pfade) weicht um {de(worst, 2)} Standardfehler ab: mehr, als der Zufall erklärt."


def verdict_hand(ex) -> tuple[str, str]:
    """Verdikt des Handbeispiels (`brw_hand.HandExample`): dieselbe Regel in allen drei Runden oder eine abweichende letzte Periode."""
    levels = [r.S for r in ex.rounds]
    s = levels[-1]
    cost_step = ex.G[s]
    if len(set(levels)) == 1:
        return "success", (f"In allen drei Runden gilt dieselbe Regel: **auf {s} auffüllen**. Das ist das Quantil ({ex.quantile}) der Nachfrage zum Verhältnis p / (p + h) = {ex.ratio}. "
                           f"Die Kosten wachsen um G({s}) = {cost_step} je Periode (V_n(x) = n · G({s}) für Positionen x ≤ {s}).")
    first = ", ".join(str(v) for v in levels)
    return "info", (f"Die Niveaus der drei Runden sind S_1, S_2, S_3 = {first}: Die letzte Periode bestellt weniger, die beiden davor das Niveau {s}. "
                    f"Die letzte Runde ist ein Newsvendor mit dem Verhältnis (p − c)/(p + h) = {ex.ratio_c} und dem Quantil {ex.quantile_c}.")
