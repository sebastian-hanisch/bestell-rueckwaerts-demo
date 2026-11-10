"""Erzeugt data/simulation_vorgerechnet.json: exakte Gesamtkosten gegen Simulation, 4 Zufalls-Seeds mit je 100.000 Pfaden.

Modell: Poisson-Mittel 3, h = 1, p = 9, 52 Entscheidungen, Lieferzeit 0 bis 3, Einkaufspreis 0 und 3, Start Bestand 0 und nichts unterwegs;
verglichen werden die Rückwärtsrechnung und das feste Niveau. Aufruf aus dem Repo-Ordner: python tools/measure_simulation.py"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import brw_algorithm as A  # noqa: E402
import brw_constants as C  # noqa: E402
import brw_evaluate as E  # noqa: E402
import brw_evaluation as EV  # noqa: E402
import brw_policy as P  # noqa: E402
import brw_simulate as S  # noqa: E402


def main() -> None:
    rows = []
    t0 = time.time()
    for c in C.SIM_C_VALUES:
        for L in range(C.L_MIN, C.L_MAX + 1):
            model = EV.make_model(L=L, mean=C.SIM_MEAN, ph=C.SIM_PH, c=c)
            bw = A.backward(C.SIM_HORIZON, model)
            level = P.poisson_quantile(P.critical_ratio(model.p, model.h), C.SIM_MEAN * (L + 1))
            fixed = E.evaluate_fixed(C.SIM_HORIZON, model, level)
            i0 = model.index(0)
            for name, levels, exact in (
                ("dp", S.levels_for_optimal(bw.S, C.SIM_HORIZON, L), E.startup_cost(model) + float(bw.V[C.SIM_HORIZON][i0])),
                ("fest", S.levels_for_fixed(level, C.SIM_HORIZON, L), E.startup_cost(model) + float(fixed[C.SIM_HORIZON][i0])),
            ):
                means, ses = [], []
                for seed in C.SIM_SEEDS:
                    costs = S.simulate(levels, L=L, mean=C.SIM_MEAN, h=model.h, p=model.p, c=model.c, paths=C.SIM_PATHS_PRECOMPUTED, seed=seed)
                    m, se = S.summary(costs)
                    means.append(m)
                    ses.append(se)
                rows.append({"c": c, "L": L, "policy": name, "level": level, "exact": exact, "sim_means": means, "ses": ses,
                             "z": [S.z_score(m, s, exact) for m, s in zip(means, ses)]})
                print(f"c={c} L={L} {name}: exakt {exact:.4f}, Seeds {[round(m, 3) for m in means]}, z {[round(z, 2) for z in rows[-1]['z']]}", flush=True)
    out = {"horizon": C.SIM_HORIZON, "paths": C.SIM_PATHS_PRECOMPUTED, "seeds": list(C.SIM_SEEDS), "mean": C.SIM_MEAN, "ph": C.SIM_PH, "rows": rows}
    target = ROOT / "data" / "simulation_vorgerechnet.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"geschrieben: {target} ({target.stat().st_size} Byte, {time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
