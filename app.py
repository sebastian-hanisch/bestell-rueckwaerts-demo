"""Bestellen per Rückwärtsrechnung - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Die Rückwärtsrechnung (Bellman) für ein Ein-Artikel-Lager findet die Bestellregel: bis zum Niveau S auffüllen, S = Quantil der Nachfrage
über die Wiederbeschaffungszeit. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import brw_constants as C
import brw_evaluation as EV
import brw_hand as H
import brw_policy as P
from brw_evaluation import Settings, de, thousands
from brw_layout import dunkles_design, kopf_css
from brw_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from brw_texts import ASSUMPTIONS_MARKDOWN, DELIMIT_MARKDOWN, HOW_IT_WORKS_MARKDOWN, INTRO_MARKDOWN, MATH_MARKDOWN
from brw_visualization import build_cdf, build_cost_growth, build_levels, build_purchase_levels, build_simulation

st.set_page_config(page_title="Bestellen per Rückwärtsrechnung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(s):
    return EV.analyse(s)


@st.cache_data(show_spinner=False)
def _grid(mean):
    return EV.level_grid(mean)


@st.cache_data(show_spinner=False)
def _equivalence(s):
    return EV.equivalence_rows(s)


@st.cache_data(show_spinner=False)
def _purchase(s):
    return EV.purchase_rows(s)


@st.cache_data(show_spinner=False)
def _simulation(s):
    return EV.sim_rows(s)


@st.cache_data(show_spinner=False)
def _precomputed():
    return EV.load_precomputed()


@st.cache_data(show_spinner=False)
def _hand(c):
    return H.solve(c)


def _verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in brw_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📦 Bestellen per Rückwärtsrechnung")
st.markdown(INTRO_MARKDOWN)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/bestell-rueckwaerts-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Ein Lager bestellt in jeder **Periode** (etwa jede Woche) einen Artikel nach, und niemand weiß vorher, wie viel gekauft wird. Die Demo gibt keine Bestellregel vor, sie **findet** sie: Sie rechnet von der letzten Periode **rückwärts** zur ersten und fragt in jeder, wie viel zu bestellen am besten ist. Heraus kommt eine einfache Regel: auf ein festes Niveau auffüllen (**Base-Stock**). Das Niveau ist ein **Quantil** der Nachfrage über die Zeit bis zur Lieferung, also der Bestand, der diese Nachfrage mit einer vom Kostenverhältnis bestimmten Wahrscheinlichkeit deckt. Das gilt im Modell der Demo, also bei zufälliger Nachfrage nach einer festen Verteilung (Poisson), Nachlieferung fehlender Ware und ohne Einkaufspreis. Mit Einkaufspreis weichen die letzten Perioden ab. Die Zahlen stammen aus erzeugten Beispielen, nicht aus echten Lagerdaten.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/bestell-rueckwaerts-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert die Rückwärtsrechnung", expanded=True):
    st.markdown(HOW_IT_WORKS_MARKDOWN)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Modell**")
    L = st.slider("Lieferzeit L (Perioden)", *bounds("L_slider"), key="L_slider", help="Perioden zwischen Bestellung und Ankunft. Die Bestellung der Periode t steht für die Nachfrage der Periode t + L bereit.")
    ph = st.select_slider("Strafverhältnis p/h", options=C.PH_OPTIONS, key="ph_select", help="Kosten je fehlendem Stück und Periode (p) im Verhältnis zu den Lagerkosten je Stück und Periode (h = 1).")
    mean = st.slider("Mittel der Nachfrage je Periode", *bounds("mean_slider"), key="mean_slider", help="Mittel der Poisson-Nachfrage je Periode.")
    c = st.select_slider("Einkaufspreis c je Stück", options=C.C_OPTIONS, key="c_select", help="Kosten je bestelltem Stück; der Rest am Ende des Horizonts ist nichts wert. Muss kleiner sein als p.")
    st.markdown("**Rechnung**")
    n = st.slider("Rest-Perioden n", *bounds("n_slider"), key="n_slider", help="Zahl der noch zu entscheidenden Perioden (Horizont).")
    st.markdown("**Handbeispiel (Abschnitt 1)**")
    hand_c = st.radio("Einkaufspreis im Handbeispiel", C.HAND_C_OPTIONS, key="hand_c_radio", horizontal=True, help="Wirkt nur auf das Handbeispiel von Abschnitt 1.")
    st.markdown("**Simulation (Experiment 4)**")
    paths = st.select_slider("Pfade der Simulation", options=C.PATHS_OPTIONS, key="paths_select", format_func=thousands)
    seed = st.number_input("Zufalls-Seed der Simulation", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)

sync_query_params({"L_slider": int(L), "ph_select": int(ph), "mean_slider": int(mean), "c_select": int(c), "n_slider": int(n),
                   "paths_select": int(paths), "seed_input": int(seed), "hand_c_radio": int(hand_c)})
settings = Settings(L=int(L), ph=int(ph), mean=int(mean), c=int(c), n=int(n), paths=int(paths), seed=int(seed), hand_c=int(hand_c))

# --- 1. Handbeispiel -----------------------------------------------------------------------------------------------------------------------

st.markdown("## 🧮 Handbeispiel von Hand")
st.markdown(
    f"""
Nachfrage je Periode **0, 1 oder 2 Stück mit je 1/3**, Lagerkosten h = 1, Strafkosten p = 3, Lieferzeit 0, **Einkaufspreis c = {settings.hand_c}**, drei Perioden rückwärts.
Wer in einer Periode auf das Niveau y auffüllt, zahlt für die Periode im Mittel G(y) = (1/3) · Σ [ h · (y − D)⁺ + p · (D − y)⁺ ]. Alle Zahlen sind exakte Brüche.
"""
)
hand = _hand(settings.hand_c)
st.markdown("**Schritt 1: Kosten einer Periode.**")
st.markdown(
    "| Niveau y | Rechnung | G(y) |\n|---|---|---|\n"
    + "\n".join(f"| {y} | ({hand.G_terms[y]}) / 3 | {hand.G[y]} |" for y in C.HAND_Y)
)
st.markdown(
    f"**Schritt 2: Quantil.** Verhältnis p / (p + h) = {hand.ratio}; die Verteilungsfunktion der Nachfrage ist F(0) = {hand.cdf[0]}, F(1) = {hand.cdf[1]}, F(2) = {hand.cdf[2]}. "
    f"Das kleinste Niveau mit F(S) ≥ {hand.ratio} ist **S = {hand.quantile}**."
)
st.markdown("**Schritt 3: rückwärts rechnen.** Mit V₀ = 0 gilt in jeder Runde (ein Display-Block, siehe auch den Expander „Mathematische Formulierung“):")
st.markdown(r"$$H_n(y) = c\,y + G(y) + \tfrac{1}{3}\sum_{d=0}^{2} V_{n-1}(y - d), \qquad V_n(x) = \min_{y \ge x} H_n(y) - c\,x$$")
for rnd in hand.rounds:
    st.markdown(f"**Runde n = {rnd.n}** ({'die letzte Periode' if rnd.n == 1 else f'noch {rnd.n} Perioden'})")
    head = "| Niveau y | " + " | ".join(str(y) for y in C.HAND_Y) + " |\n|---|" + "---|" * len(C.HAND_Y) + "\n"
    h_row = "| H_%d(y) | " % rnd.n + " | ".join(f"**{rnd.H[y]} ✅**" if y == rnd.S else str(rnd.H[y]) for y in C.HAND_Y) + " |\n"
    v_row = "| V_%d(x) (Position x = y) | " % rnd.n + " | ".join(str(rnd.V[y]) for y in C.HAND_Y) + " |"
    st.markdown(head + h_row + v_row)
    st.caption(f"Minimum bei y = {rnd.S}: {rnd.line}")
_verdict(EV.verdict_hand(hand))

st.markdown("---")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
if settings.c >= settings.ph * C.H_COST:
    st.warning(f"Der Einkaufspreis c = {settings.c} ist nicht kleiner als die Strafkosten p = {settings.ph}: Die letzte Periode bestellt dann nie, "
               "das Niveau fällt unter das Gitter. Dieser Fall ist nicht gerechnet; bitte c kleiner als p/h wählen.")
else:
    with st.spinner("Rechne die Rückwärtsrechnung (je nach Rechner; gemessen unter einer Sekunde) …"):
        a = _analysis(settings)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Aufziehniveau S (Grenzwert)", f"{a.level}", delta=f"Quantil, {a.level_last} in der letzten Periode" if a.level_last != a.level else "gleich in jeder Periode", delta_color="off",
              help="Kleinste Position, bei der die Verteilungsfunktion der Nachfrage über L + 1 Perioden mindestens p / (p + h) erreicht.")
    m2.metric("Stationär ab", "nie bis n = 60" if a.n_star is None else f"{a.n_star} Rest-Periode" + ("n" if a.n_star > 1 else ""), delta="Niveau = S ab da", delta_color="off")
    m3.metric("Kosten je Periode G(S)", de(a.g, 4), delta="im stationären Betrieb", delta_color="off")
    m4.metric(f"Steuerbare Kosten V_{settings.n}(0)", de(a.controllable, 2), delta=f"Anlauf getrennt: {de(a.startup, 0)}", delta_color="off",
              help="Kosten der Rückwärtsrechnung über n Perioden bei Start mit Position 0. Die Anlaufkosten der ersten L Perioden (Bestellungen noch unterwegs, Rückstand mit Strafe p) sind nicht steuerbar und stehen daneben.")
    st.plotly_chart(build_levels(a.bw.S, a.level, settings.n), width="stretch", key="levels_chart")
    st.caption(f"Aufziehniveau S_n je Zahl der Rest-Perioden n (n = 1: letzte Periode), gerechnet bis n = {C.NMAX}. Gestrichelt: das Quantil. "
               f"Gesamtkosten über {settings.n + settings.L} Kalenderperioden = steuerbar + Anlauf = {de(a.total, 2)}.")

    st.markdown("## ❓ Kernfrage: Ist die Regel „bis S auffüllen“, und ist S ein Quantil?")
    _verdict(EV.verdict_quantile(a.bw.S[C.NMAX], a.level, ratio=a.ratio, L=settings.L, mean=settings.mean))
    st.markdown("---")

    # --- Experiment 1 ----------------------------------------------------------------------------------------------------------------------
    st.subheader("🔬 Experiment 1: Wie viele Perioden, bis die Politik stationär ist?")
    st.caption("Exakt gerechnet (kein Zufall). Gesucht: ab welcher Zahl von Rest-Perioden das Niveau das spätere ist. Bei Einkaufspreis 0 ist die Antwort 1.")
    _verdict(EV.verdict_stationary(a.n_star, a.level, a.bw.S[1:], settings.c))
    shown = sorted({k for k in (1, 2, 3, 4, 5, 10, 20, 40, settings.n) if k <= settings.n})
    st.dataframe(
        [{"Rest-Perioden n": k, "Niveau S_n": a.bw.S[k], "Steuerbare Kosten V_n(0)": de(float(a.bw.V[k][a.model.index(0)]), 2),
          "Zuwachs gegen n − 1": de(float(a.bw.V[k][a.model.index(0)] - a.bw.V[k - 1][a.model.index(0)]), 4)} for k in shown],
        hide_index=True, width="stretch",
    )
    st.plotly_chart(build_cost_growth([float(v[a.model.index(0)]) for v in a.bw.V], a.g, settings.n), width="stretch", key="growth_chart")
    st.caption("Bei Einkaufspreis 0 liegt V_n(0) auf der Geraden n · G(S): Jede Periode kostet G(S). Mit Einkaufspreis kommen die Einkaufskosten dazu, die Linie liegt darüber.")
    st.markdown("---")

    # --- Experiment 2 ----------------------------------------------------------------------------------------------------------------------
    st.subheader("🔬 Experiment 2: Quantil-Karte, Rückwärtsrechnung gegen Formel")
    st.caption("Exakt gerechnet. Links: Verteilungsfunktion der Nachfrage über L + 1 Perioden und das kritische Verhältnis; darunter alle 20 Zellen aus Lieferzeit und p/h bei dem gewählten Mittel (c = 0).")
    mean_total = settings.mean * (settings.L + 1)
    st.plotly_chart(build_cdf(P.poisson_cdf_table(mean_total, int(mean_total + 12 * mean_total ** 0.5 + 40)), a.ratio, a.level, mean_total), width="stretch", key="cdf_chart")
    with st.spinner("Rechne 20 Zellen mit je 40 Rest-Perioden (je nach Rechner; gemessen 0,5 bis 1 Sekunde) …"):
        grid = _grid(settings.mean)
    st.dataframe(
        [{"Lieferzeit L": L_, **{f"p/h = {ph_}": (f"{next(r for r in grid if r['L'] == L_ and r['ph'] == ph_)['dp']}"
                                                  f"{' ✅' if next(r for r in grid if r['L'] == L_ and r['ph'] == ph_)['same'] else ' ≠ Quantil'}") for ph_ in C.PH_OPTIONS}}
         for L_ in range(C.L_MIN, C.L_MAX + 1)],
        hide_index=True, width="stretch",
    )
    st.caption("Jede Zelle: Niveau der Rückwärtsrechnung; ✅ heißt: bei jeder der 40 Rest-Perioden gleich dem Quantil.")
    _verdict(EV.verdict_grid(sum(1 for r in grid if r["same"]), len(grid), settings.mean))
    eq = _equivalence(Settings(L=settings.L, ph=settings.ph, mean=settings.mean))
    st.dataframe([{"Lieferzeit L": r["L"], "Mittel": r["mean"], "(L + 1) · Mittel": r["product"], "Niveau S": r["level"], "Kosten je Periode G(S)": de(r["g"], 4)} for r in eq],
                 hide_index=True, width="stretch")
    _verdict(EV.verdict_equivalence(eq))
    st.markdown("---")

    # --- Experiment 3 ----------------------------------------------------------------------------------------------------------------------
    st.subheader("🔬 Experiment 3: Letzte Perioden mit Einkaufspreis")
    st.caption("Exakt gerechnet. Der Einkaufspreis c je Stück bei unbewertetem Rest macht das Auffüllen in den letzten Perioden weniger lohnend. Gezeigt: je Einkaufspreis unterhalb von p die Niveaus S_1 bis S_6, "
               "ab wann das Niveau das spätere ist und was das feste Niveau S in allen Perioden über n Rest-Perioden mehr kostet.")
    rows = _purchase(Settings(L=settings.L, ph=settings.ph, mean=settings.mean, n=settings.n))
    st.plotly_chart(build_purchase_levels(rows), width="stretch", key="purchase_chart")
    st.dataframe(
        [{"Einkaufspreis c": r["c"], "Niveaus S_1 bis S_6": ", ".join(str(v) for v in r["levels"]), "Stationär ab n": r["n_star"], "Niveau letzte Periode": r["level_last"],
          f"Mehrkosten festes S (n = {settings.n})": de(r["extra"], 3), "in Periodenkosten": de(r["extra_g"], 2), "in % der steuerbaren Kosten": de(r["extra_pct"], 2)} for r in rows],
        hide_index=True, width="stretch",
    )
    current = next(r for r in rows if r["c"] == settings.c)
    _verdict(EV.verdict_purchase(current, settings.n))
    st.markdown("---")

    # --- Experiment 4 ----------------------------------------------------------------------------------------------------------------------
    st.subheader("🔬 Experiment 4: Exakt gegen Simulation")
    st.caption(f"Die exakte Rechnung gegen eine Simulation der echten Bewegung von Bestand, Rückstand und Bestellungen unterwegs ({thousands(settings.paths)} Pfade, Zufalls-Seed {settings.seed}; "
               "bei 100.000 Pfaden je nach Rechner gemessen unter einer Sekunde je Politik). Verglichen werden die Gesamtkosten einschließlich Anlauf.")
    with st.spinner(f"Simuliere {thousands(settings.paths)} Pfade (je nach Rechner; gemessen unter einer Sekunde) …"):
        sim = _simulation(settings)
    st.plotly_chart(build_simulation(sim), width="stretch", key="sim_chart")
    st.dataframe(
        [{"Politik": r["policy"], "Exakt": de(r["exact"], 3), "Simulation": de(r["sim"], 3), "Standardfehler": de(r["se"], 3), "Abweichung in Standardfehlern": de(r["z"], 2), "Pfade": thousands(r["paths"])} for r in sim],
        hide_index=True, width="stretch",
    )
    _verdict(EV.verdict_simulation(sim))
    pre = _precomputed()
    st.markdown(f"**Vorgerechnet** (Mittel {pre['mean']}, p/h = {pre['ph']}, {pre['horizon']} Entscheidungen, je {thousands(pre['paths'])} Pfade und {len(pre['seeds'])} Zufalls-Seeds, `tools/measure_simulation.py`):")
    st.dataframe(
        [{"Einkaufspreis c": r["c"], "Lieferzeit L": r["L"], "Politik": "Rückwärtsrechnung" if r["policy"] == "dp" else "festes Niveau S", "Niveau S": r["level"], "Exakt": de(r["exact"], 3),
          "Mittel der 4 Zufalls-Seeds": de(sum(r["sim_means"]) / len(r["sim_means"]), 3), "Größte |Abweichung| in Standardfehlern": de(max(abs(z) for z in r["z"]), 2)} for r in pre["rows"]],
        hide_index=True, width="stretch",
    )
    st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Gemessen? |
|---|---|---|
| **Einkaufspreis 0** (c = 0) | Mit Einkaufspreis und unbewertetem Rest bestellen die letzten 1 bis 4 Perioden weniger; das feste Niveau S kostet über 52 Perioden 0,04 bis 2,45 Periodenkosten mehr (Experiment 3, 32 Zellen bei Mittel 3) | ja |
| **Poisson-Nachfrage** | Die Gleichwertigkeit über (L + 1) · Mittel nutzt, dass Summen von Poisson-Größen wieder Poisson-verteilt sind; andere Verteilungen sind nicht gerechnet | nein |
| **Rückstand** | Bei verlorener Nachfrage ist die Bestandsposition als Zustand nicht mehr ausreichend; das ist ein anderes Modell und hier nicht gerechnet | nein |
| **Einkaufspreis kleiner als p** | Ab c ≥ p bestellt die letzte Periode nie; die Demo zeigt dann eine Meldung statt einer Zahl | nicht gerechnet |
| **Kein Restwert, keine Diskontierung** | Ein Restwert oder ein Zinssatz würde die letzten Perioden verändern; nicht gerechnet | nein |
"""
)
st.markdown(DELIMIT_MARKDOWN)

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(ASSUMPTIONS_MARKDOWN)

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/bestell-rueckwaerts-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind die Nachfrage $D$ je Periode (Poisson), die Lieferzeit $L$, die Kosten $h$, $p$ und $c$ und die Zahl $n$ der noch zu entscheidenden Perioden. Gesucht ist für jede Bestandsposition $x$ die beste Bestellung.

| Symbol | Bedeutung |
|---|---|
| $x$ | Bestandsposition: Bestand plus Bestellungen unterwegs minus Rückstand |
| $y$ | Bestandsposition nach der Bestellung (Auffüllniveau), $y \ge x$ |
| $D^{(L+1)}$ | Nachfrage über die Wiederbeschaffungszeit, also die Summe von $L + 1$ Perioden |
| $G(y)$ | erwartete Lager- und Rückstandskosten einer Periode bei Niveau $y$ |
| $H_n(y)$ | Wert, wenn bei $n$ Rest-Perioden auf $y$ aufgefüllt wird (ohne den Anteil $-c\,x$) |
| $V_n(x)$ | kleinste erwartete Kosten bei Position $x$ und $n$ Rest-Perioden |
| $S_n$ | kleinstes Minimum von $H_n$: Aufziehniveau bei $n$ Rest-Perioden |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/bestell-rueckwaerts-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(MATH_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Bestandspolitiken: von Base-Stock bis Regelwahl](https://sebastianhanisch.net/konzepte-bestandspolitiken.html)."
)
