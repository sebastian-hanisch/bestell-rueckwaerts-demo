"""Messreihe der README im Zielumfang (alle Zellen der Regler); tests/test_claims.py ruft dieselben Funktionen auf.

Aufruf aus dem Repo-Ordner: python tools/measure_grid.py  (druckt die Zahlen der README-Tabelle „Zahl -> Test“).

Zellen (Poisson-Nachfrage, h = 1, Rückstand, keine Bestellgrenze):
  c = 0:  Lieferzeit 0..3 x p/h 1, 2, 4, 9, 19 x Mittel 2..5 = 80 Zellen, 40 Rest-Perioden
  c > 0:  Lieferzeit 0..3 x p/h 2, 4, 9, 19 x Mittel 2..5 x Einkaufspreis 1, 3, 5 mit c < p = 144 Zellen, 30 Rest-Perioden
  Tabelle der Mehrkosten: Mittel 3, p/h 4, 9, 19, c 1, 3, 5 mit c < p = 32 Zellen"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import brw_algorithm as A  # noqa: E402
import brw_cost as K  # noqa: E402
import brw_evaluate as E  # noqa: E402
import brw_evaluation as EV  # noqa: E402
import brw_policy as P  # noqa: E402

PH_ALL = (1, 2, 4, 9, 19)


def cells_c0(rest: int = 40) -> list[dict]:
    """80 Zellen bei c = 0: Niveau der Rückwärtsrechnung bei jeder Restzahl 1..rest, Quantil, Aufzählung von G, Stationarität, Kosten des festen Niveaus."""
    out = []
    for L in range(4):
        for ph in PH_ALL:
            for mean in range(2, 6):
                m = EV.make_model(L=L, mean=mean, ph=ph)
                bw = A.backward(rest, m)
                q = P.poisson_quantile(P.critical_ratio(m.p, m.h), mean * (L + 1))
                enum = int(m.x[int(np.argmax(m.G <= m.G.min() + 1e-12))])      # Aufzählung: kleinstes Minimum von G
                fixed = E.evaluate_fixed(rest, m, q)
                i0 = m.index(0)
                gs = np.sort(m.G)
                action_ok = all(np.array_equal(m.x[bw.action[n]], np.maximum(m.x, bw.S[n])) for n in range(1, rest + 1))
                out.append({"L": L, "ph": ph, "mean": mean, "set": set(bw.S[1:]), "q": q, "enum": enum, "n_star": A.stationary_from(bw.S, q),
                            "extra": float(fixed[rest][i0] - bw.V[rest][i0]), "g": float(m.G[m.index(q)]), "tie": float(gs[1] - gs[0]),
                            "action_ok": action_ok, "gap_min": min(bw.gap[1:]), "edge_ok": A.edge_mass_is_zero(m, bw.S)})
    return out


def cells_purchase(rest: int = 30) -> list[dict]:
    """144 Zellen mit Einkaufspreis: Grenzniveau gegen Quantil, S_1 gegen das Quantil zum Verhältnis (p - c)/(p + h), Struktur der Aktion."""
    out = []
    for L in range(4):
        for ph in (2, 4, 9, 19):
            for mean in range(2, 6):
                for c in (1, 3, 5):
                    if c >= ph:
                        continue
                    m = EV.make_model(L=L, mean=mean, ph=ph, c=c)
                    bw = A.backward(rest, m)
                    q = P.poisson_quantile(P.critical_ratio(m.p, m.h), mean * (L + 1))
                    q1 = P.poisson_quantile(P.critical_ratio(m.p, m.h, m.c), mean * (L + 1))
                    action_ok = all(np.array_equal(m.x[bw.action[n]], np.maximum(m.x, bw.S[n])) for n in range(1, rest + 1))
                    out.append({"L": L, "ph": ph, "mean": mean, "c": c, "S_last": bw.S[rest], "q": q, "S1": bw.S[1], "q1": q1, "action_ok": action_ok, "edge_ok": A.edge_mass_is_zero(m, bw.S)})
    return out


def table_extra(rest: int = 60) -> list[dict]:
    """32 Zellen (Mittel 3): n*, Niveaus S_1..S_4, Mehrkosten des festen Niveaus bei N = 1, 3, 52 in % und absolut bei 52."""
    out = []
    for ph in (4, 9, 19):
        for c in (1, 3, 5):
            if c >= ph:
                continue
            for L in range(4):
                m = EV.make_model(L=L, mean=3, ph=ph, c=c)
                bw = A.backward(rest, m)
                q = P.poisson_quantile(P.critical_ratio(m.p, m.h), 3 * (L + 1))
                fixed = E.evaluate_fixed(52, m, q)
                i0 = m.index(0)
                pct = {n: 100.0 * (float(fixed[n][i0]) / float(bw.V[n][i0]) - 1.0) for n in (1, 3, 52)}
                abs52 = float(fixed[52][i0] - bw.V[52][i0])
                out.append({"ph": ph, "c": c, "L": L, "S": q, "S14": bw.S[1:5], "n_star": A.stationary_from(bw.S, q), "pct": pct, "abs52": abs52,
                            "abs52_g": abs52 / float(m.G[m.index(q)])})
    return out


def equivalence_groups() -> tuple[int, int, int]:
    """Paare (Nachfrage über L + 1 Perioden, p/h) aus den 80 Zellen: (Zahl der Paare, davon mit mehreren Zellen, davon mit abweichendem Niveau oder abweichenden Periodenkosten)."""
    groups = {}
    for mean in range(2, 6):
        for L in range(4):
            for ph in PH_ALL:
                m = EV.make_model(L=L, mean=mean, ph=ph)
                q = P.poisson_quantile(P.critical_ratio(m.p, m.h), mean * (L + 1))
                groups.setdefault((mean * (L + 1), ph), []).append((q, float(m.G[m.index(q)])))
    multi = {k: v for k, v in groups.items() if len(v) > 1}
    bad = sum(1 for v in multi.values() if len({q for q, _ in v}) != 1 or max(g for _, g in v) - min(g for _, g in v) > 1e-9)
    return len(groups), len(multi), bad


def vehicle_rows() -> list[dict]:
    """Vehikel (Mittel 3, p/h 9, c = 0): Niveau, Periodenkosten, steuerbare Kosten bei 52 Perioden, Anlaufkosten je Lieferzeit."""
    out = []
    for L in range(4):
        a = EV.analyse(EV.Settings(L=L))
        out.append({"L": L, "S": a.level, "g": a.g, "V52": a.controllable, "startup": a.startup, "n_star": a.n_star})
    return out


def truncation_masses() -> dict:
    import brw_demand as D
    return {mean: D.truncation_mass(mean, D.dmax_for(mean)) for mean in range(2, 6)}


def main() -> None:
    c0 = cells_c0()
    print("c = 0, 80 Zellen: Niveau = Quantil = Aufzählung bei jeder der 40 Restzahlen:", sum(1 for r in c0 if r["set"] == {r["q"]} and r["q"] == r["enum"]), "/", len(c0))
    print("   Stationär ab n* = 1:", sum(1 for r in c0 if r["n_star"] == 1), "/", len(c0), "| Mehrkosten festes Niveau < 1e-9:", sum(1 for r in c0 if abs(r["extra"]) < 1e-9))
    print("   Aktion = max(Position, S_n):", sum(1 for r in c0 if r["action_ok"]), "/", len(c0), "| kleinster Gleichstandsabstand von G:", min(r["tie"] for r in c0),
          "| kleinster Abstand bester/zweitbester H-Wert:", min(r["gap_min"] for r in c0), "| Randmasse 0:", sum(1 for r in c0 if r["edge_ok"]), "/", len(c0))
    cp = cells_purchase()
    print("c > 0,", len(cp), "Zellen: Grenzniveau = Quantil:", sum(1 for r in cp if r["S_last"] == r["q"]), "| S_1 = Quantil zu (p - c)/(p + h):", sum(1 for r in cp if r["S1"] == r["q1"]),
          "| Aktion = max(Position, S_n):", sum(1 for r in cp if r["action_ok"]))
    t = table_extra()
    print("Mehrkosten-Tabelle,", len(t), "Zellen: n* von", min(r["n_star"] for r in t), "bis", max(r["n_star"] for r in t))
    for n in (1, 3, 52):
        print(f"   N = {n}: {min(r['pct'][n] for r in t):.2f} bis {max(r['pct'][n] for r in t):.2f} %")
    print(f"   absolut bei 52: {min(r['abs52'] for r in t):.3f} bis {max(r['abs52'] for r in t):.3f}; in Periodenkosten {min(r['abs52_g'] for r in t):.2f} bis {max(r['abs52_g'] for r in t):.2f}")
    print("Gleichwertigkeit über (L + 1) x Mittel: Paare, davon mehrfach, davon abweichend:", equivalence_groups())
    for r in vehicle_rows():
        print(r)
    print("Abschneidemasse P(D > dmax) je Mittel:", {k: f"{v:.1e}" for k, v in truncation_masses().items()})


if __name__ == "__main__":
    main()
