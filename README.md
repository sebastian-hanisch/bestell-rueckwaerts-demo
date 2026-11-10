# Bestellen per Rückwärtsrechnung – Streamlit-Demo

<!-- Live-Link nach dem Deploy hier einsetzen (Leerzeile davor und danach). -->

Erste Demo der Linie **Bestandspolitiken** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Ein Artikel, eine Entscheidung je Periode („wie viel bestellen?“), Poisson-Nachfrage, Rückstand. Die Demo **bestimmt** die Bestellregel per exakter Rückwärtsrechnung (Bellman), statt sie vorzugeben; nach dem Abgleich der README-Texte der älteren Nachbar-Demos des Portfolios tut das keine von ihnen. Der Zustand ist hier eine einzige Zahl, die Regel eine einfache.

## Warum dieses Problem

**Kernfrage: Wie viel bestellen, wenn jede Periode zählt?** Von Hand werden drei Perioden rückwärts gerechnet (Nachfrage 0, 1, 2 mit je 1/3), dann dieselbe Rechnung über bis zu 60 Perioden. Die Rechnung liefert keine vorgegebene Regel, sie findet sie: **bis zum Niveau S auffüllen** (Base-Stock), und S ist das **Quantil der Nachfrage über Lieferzeit + 1 Perioden** zum Verhältnis p / (p + h). Bei Einkaufspreis 0 verschiebt die Lieferzeit die Regel nur, sie verändert sie nicht. Im Modell der Demo ist die Politik schon bei **einer** Rest-Periode stationär; die Randperioden weichen erst mit einem **Einkaufspreis** ab.

## Modell

Ein Artikel, Poisson-Nachfrage mit Mittel 2 bis 5 je Periode, Lagerkosten h = 1 je Stück und Periode, Strafkosten p = (p/h) · h je fehlendem Stück und Periode (Rückstand: Fehlmengen werden nachgeliefert), Lieferzeit L = 0 bis 3 Perioden, optional Einkaufspreis c je bestelltem Stück (der Rest am Ende ist nichts wert). Zustand ist die **Bestandsposition** x (Bestand + Bestellungen unterwegs − Rückstand). Mit n noch zu entscheidenden Perioden und V₀ = 0 gilt (ausgeschrieben im 📐-Expander der App):

$$G(y) = \mathbb{E}\left[\, h\,(y - D^{(L+1)})^{+} + p\,(D^{(L+1)} - y)^{+} \right]$$

$$V_n(x) = \min_{y \ge x} \Big\{ c\,(y - x) + G(y) + \mathbb{E}\,V_{n-1}(y - D) \Big\}$$

$$S = \min\Big\{ k : \Pr\big(D^{(L+1)} \le k\big) \ge \frac{p}{p + h} \Big\}$$

D^(L+1) ist die Nachfrage über die Wiederbeschaffungszeit (Summe von L + 1 Perioden). Die beste Bestellung ist max(S_n − x, 0), wobei S_n das kleinste Minimum der Rundenfunktion H_n ist. Die dritte Gleichung folgt bei c = 0 aus der Herleitung im 📐-Expander der App (G(y + 1) − G(y) = (p + h) · Pr(D^(L+1) ≤ y) − p macht das Quantil zum kleinsten Minimum von G); gemessen sind die Zahlen der 80 Zellen (Poisson-Nachfrage, Rückstand, Einkaufspreis 0, keine Bestellgrenze). Anfangsposition 0, nichts unterwegs. Die ersten L Perioden verursachen **Anlaufkosten** (Bestellungen noch unterwegs, Rückstand mit Strafe p), die nicht steuerbar sind und in V_n(0) nicht enthalten sind: Anlauf = p · Mittel · L (L + 1) / 2.

## Methodik

- **Rückwärtsrechnung** (`brw_algorithm.py`): ein Gitter der Bestandspositionen, je Runde das Minimum von H_n über y ≥ x; das kleinste Minimum (Toleranz 1e-9) ist S_n. Das Gitter reicht unten 10 unter die größte Nachfrage einer Periode, oben 3 über das 1 − 1e-9-Quantil der Nachfrage über L + 1 Perioden; die Randmasse unten ist 0. Es gibt keine Bestellgrenze. Die Poisson-Nachfrage ist beim Zwölffachen des Mittels plus 20 abgeschnitten (Restmasse auf der Obergrenze: 4,2e-44, 2,0e-51, 4,0e-59, 5,1e-67 für Mittel 2, 3, 4, 5).
- **Handbeispiel in Brüchen** (`brw_hand.py`): `fractions`, unabhängig von numpy; die Tabellen G, H_n, V_n mit markiertem Minimum stehen in der App.
- **Geschlossene Regel** (`brw_policy.py`): Quantil aus der aufsummierten Poisson-Formel, ohne Faltung und ohne Bellman-Rechnung.
- **Feste Politik exakt** (`brw_evaluate.py`): „immer bis S auffüllen“ im selben Modell, ohne zu minimieren; Differenz zur Rückwärtsrechnung sind die Mehrkosten.
- **Simulation** (`brw_simulate.py`, `brw_rng.py`): bewegt Bestand, Rückstand und Bestellungen unterwegs Periode für Periode und kennt G nicht; Zufall aus dem ganzzahligen Erzeuger SplitMix64, ein Strom je Periode.
- **Gegenprobe mit vollem Zustand** (`tests/test_oracle_bestell_rueckwaerts.py`): Bestand und jede Bestellung unterwegs als Zustand, eigener Code im Test.

## Befunde (gemessen, keine Behauptungen)

Poisson-Nachfrage, h = 1, Rückstand, keine Bestellgrenze; „Zelle“ heißt eine Kombination der Regler. Alles exakt gerechnet, kein Zufall, außer der Simulation. Jede Zahl steht im Test der letzten Spalte (alle in `tests/test_claims.py`, wo nichts anderes steht); die Rasterzahlen rechnet `tools/measure_grid.py` aus.

| Frage | Befund | Test |
|---|---|---|
| Ist S das Quantil? (c = 0) | Das Niveau der Rückwärtsrechnung gleicht dem Poisson-Quantil über L + 1 Perioden und der Aufzählung von G in **80 von 80 Zellen** (Lieferzeit 0 bis 3, p/h = 1, 2, 4, 9, 19, Mittel 2 bis 5), bei jeder der 40 Rest-Perioden | `test_80_cells_level_equals_quantile_equals_enumeration_at_every_rest_period` |
| Vehikel (Mittel 3, p/h = 9, c = 0) | S = 5, 9, 13, 17 für Lieferzeit 0 bis 3; Kosten je Periode G(S) = 3,3462 / 4,6126 / 5,5798 / 6,4507; steuerbare Kosten V₅₂(0) = 174,0027 / 239,8546 / 290,1492 / 335,4338; Anlaufkosten 0 / 27 / 81 / 162 | `test_vehicle_table_levels_costs_and_startup`, `test_vehicle_controllable_cost_is_n_times_the_period_cost_at_c_zero` |
| Niveaus bei Mittel 3 für p/h = 1, 2, 4, 9, 19 | Lieferzeit 0: 3, 4, 4, 5, 6; 1: 6, 7, 8, 9, 10; 2: 9, 10, 11, 13, 14; 3: 12, 13, 15, 17, 18 | `test_level_table_for_mean_3_and_every_penalty_ratio` |
| Ab wann stationär? (c = 0) | Schon bei **einer** Rest-Periode in **80 von 80 Zellen**; das feste Niveau S kostet über 40 Rest-Perioden gegenüber der Rückwärtsrechnung exakt 0 (Betrag unter 1e-9) | `test_80_cells_are_stationary_from_one_rest_period_and_the_fixed_level_costs_nothing_extra` |
| Struktur der Bestellung | In allen 80 Zellen ist die beste Bestellung in jedem Zustand und bei jeder der 40 Rest-Perioden max(Position, S_n) − Position | `test_80_cells_action_is_max_of_position_and_level_in_every_state` |
| Gleichstand, Rand | Kleinster Abstand zwischen bestem und zweitbestem Niveau (Kosten) in den 80 Zellen: mehr als 0,007; Randmasse unten 0 in 80 von 80 Zellen (und in 144 von 144 Zellen mit Einkaufspreis) | `test_80_cells_have_no_tie_between_best_and_second_best_level_and_no_edge_mass` |
| Lieferzeit und Mittel wirken über (L + 1) · Mittel | 60 verschiedene Paare (Nachfrage über L + 1 Perioden, p/h) aus den 80 Zellen, davon 20 mit mehreren Zellen, **0 mit abweichendem** Niveau oder abweichenden Periodenkosten (bei c = 0 und nur für Poisson-Nachfrage; Anlaufkosten und, mit Einkaufspreis, die Niveaus der letzten Perioden hängen an Lieferzeit und Mittel einzeln) | `test_equivalence_over_lead_time_times_mean_in_20_groups_of_the_80_cells` |
| Mit Einkaufspreis c: Grenzniveau | In **144 von 144 Zellen** (Lieferzeit 0 bis 3, p/h = 2, 4, 9, 19, Mittel 2 bis 5, c = 1, 3, 5 mit c < p) gleicht das Niveau bei 30 Rest-Perioden dem Quantil zum Verhältnis p / (p + h); die letzte Periode (S_1) dem Quantil zum Verhältnis (p − c) / (p + h); die Struktur max(Position, S_n) gilt in allen 144 | `test_144_cells_with_purchase_price_limit_level_is_the_quantile_and_last_level_is_the_formula` |
| Mit Einkaufspreis c: wie viele Perioden weichen ab? | Mittel 3, p/h = 4, 9, 19, c = 1, 3, 5 mit c < p, Lieferzeit 0 bis 3 (32 Zellen): stationär ab 2 bis 5 Rest-Perioden; die Niveaus S_1 bis S_4 liegen in allen 32 Zellen nicht über S. Beispiel Mittel 3, p/h = 9, c = 3, L = 3: S_1 bis S_4 = 13, 15, 16, 17, ab 4 Rest-Perioden S = 17 | `test_32_cells_with_purchase_price_stationary_from_2_to_5_rest_periods`, `test_hand_picked_cell_mean_3_ph_9_c_3_L_3` |
| Mehrkosten des festen S mit Einkaufspreis | Dieselben 32 Zellen, Start Position 0: bei 1 Rest-Periode 1,86 bis 31,91 %, bei 3 Rest-Perioden 0,69 bis 13,33 %, bei 52 Rest-Perioden 0,04 bis 1,35 % der steuerbaren Kosten einschließlich Einkauf; absolut bei 52 Rest-Perioden 0,145 bis 15,791 (0,04 bis 2,45 Periodenkosten G(S)). Im Beispiel oben 7,13 | `test_32_cells_extra_cost_of_the_fixed_level_bands`, `test_hand_picked_cell_mean_3_ph_9_c_3_L_3` |
| Voller Zustand gegen Positions-Rechnung | Bei N = 3 Entscheidungen, Lieferzeit 0 bis 3, Einkaufspreis 0 und 3 (8 Fälle, Mittel 3, p/h = 9, Nachfrage bis 14, Bestellmengen bis 20): gleicher Wert (Anlauf + V_N(0)) mit größter Abweichung unter 1e-9 (gemessen 2,8e-14); die Regel max(S_n − Position, 0) ist in allen geprüften Zuständen im Wert optimal (Zustandsgitter bis 29.106 Zustände je Fall, davon höchstens 7.487 je Stufe und Fall geprüft) | `test_full_state_recursion_equals_the_position_recursion` (`tests/test_oracle_bestell_rueckwaerts.py`) |
| Exakt gegen Simulation | 4 Zufalls-Seeds mit je 100.000 Pfaden, Mittel 3, p/h = 9, 52 Entscheidungen, Lieferzeit 0 bis 3, c = 0 und 3: 12 verschiedene Zeilen (bei c = 0 sind Rückwärtsrechnung und festes Niveau dieselbe Regel) mal 4 Zufalls-Seeds = 48 Werte, größte Abweichung 2,09 Standardfehler; die Mittel der vier Zufalls-Seeds weichen um −0,063 bis +0,021 vom exakten Wert ab (Standardfehler je Zufalls-Seed 0,098 bis 0,327). Alle Lieferzeiten und beide Politiken benutzen je Zufalls-Seed dieselben Zufallszahlen, die Werte sind nicht unabhängig | `test_precomputed_simulation_48_seed_values_within_the_noise`, `test_precomputed_means_of_the_four_seeds_are_within_the_standard_error`, `test_precomputed_exact_values_agree_with_the_live_exact_values` |
| Unabhängige Simulation im Test | Exakter Gesamtwert gegen eine im Test neu geschriebene Simulation (numpy-Erzeuger, 6.000 Pfade, 2 Zufalls-Seeds, 12 Perioden): Abweichung unter 4 Standardfehlern in allen 8 Vergleichen (L = 0 mit c = 0 und L = 2 mit c = 3, je beide Politiken und beide Zufalls-Seeds; bei c = 0 sind beide Politiken dieselbe Regel, es sind 6 verschiedene Vergleiche) | `test_exact_total_cost_agrees_with_an_independent_simulation` (`tests/test_oracle_bestell_rueckwaerts.py`) |
| Abschneidemasse | P(D > Obergrenze) je Periode: höchstens 1e-43 für Mittel 2 bis 5 | `test_truncation_mass_per_mean`, `test_abort_mass_of_poisson_truncation_is_negligible` |

Alles, was hier nicht steht (andere Verteilungen, Diskontierung, Restwert, c ≥ p), ist **nicht gemessen**.

## Ehrliche Grenzen

**Annahmen**
- **Ein Artikel**, **Poisson-Nachfrage** mit ganzzahligem Mittel 2 bis 5 je Periode, unabhängig und gleich verteilt; Lagerkosten h = 1 je Stück und Periode, Strafkosten p = (p/h) · h je fehlendem Stück und Periode.
- **Rückstand:** Fehlmengen werden nachgeliefert und kosten p je Stück und Periode; verlorene Nachfrage ist ein anderes Modell und hier nicht gerechnet.
- **Zeitablauf:** Bestellung zu Beginn der Periode, sie steht für die Nachfrage der Periode t + L bereit (L = 0: sofort). Start bei Bestandsposition 0 mit nichts unterwegs.
- **Einkaufspreis c** je bestelltem Stück (0, 1, 3, 5), der Rest am Ende des Horizonts ist **nichts wert**. Bestellungen der letzten L Perioden kämen nach dem Horizont an und werden nicht gerechnet.
- **Keine Bestellkosten je Bestellung, keine Bestellgrenze, keine Diskontierung.** Das Gitter der Positionen ist so gewählt, dass die Randmasse unten 0 ist (die Politik erreicht den Gitterrand nie; geprüft mit `edge_mass_is_zero` in den 80 Zellen bei c = 0 und den 144 Zellen mit Einkaufspreis, `tests/test_claims.py`); die Poisson-Nachfrage ist bei dem Zwölffachen des Mittels plus 20 abgeschnitten, die Restmasse (Größenordnung 1e-44 bis 1e-67 je nach Mittel, `tests/test_claims.py`) liegt auf der Obergrenze.

**Grenzen**
- Der Satz „Aufziehniveau = Quantil über L + 1 Perioden“ folgt bei c = 0 aus der Herleitung im 📐-Expander (eigene Rechnung, keine Quellenaussage); gemessen sind die 80 Zellen mit Poisson-Nachfrage (`tests/test_claims.py`). Für Rückstand mit positiver Lieferzeit nennen Xin und Goldberg (arXiv 1409.1499, S. 2) Base-Stock als optimal und verweisen auf Scarf (1960), Iglehart (1963) und Veinott (1966); diese drei Originale wurden hier **nicht gelesen** (Angabe nach Xin und Goldberg).
- Die Aussage „Lieferzeit und Mittel wirken nur über (L + 1) · Mittel“ gilt für Niveau und Periodenkosten bei c = 0 und Poisson-Nachfrage (Summen von Poisson-Größen sind Poisson-verteilt), nicht allgemein; die Anlaufkosten p · Mittel · L (L + 1) / 2 und mit Einkaufspreis die Niveaus der letzten Perioden hängen an Lieferzeit und Mittel einzeln.
- Die Stationarität schon bei einer Rest-Periode (Experiment 1) gilt für **c = 0, Rückstand, Poisson, ohne Bestellgrenze**; mit Einkaufspreis und unbewertetem Rest fällt sie, die Herleitung versagt dann.
- Einkaufspreis c ab p wird nicht gerechnet (die letzte Periode bestellt dann nie; die Demo zeigt eine Meldung statt einer Zahl). Nicht gemessen sind außerdem: Diskontierung, ein Restwert ungleich 0, andere Nachfrageverteilungen, nicht ganzzahlige Mengen und Nachfrage mit Gedächtnis.

**Bekannte Probleme und Unsicherheiten**
- Minima gelten als gleich, wenn sie sich um weniger als 1e-9 unterscheiden; das kleinste Niveau gewinnt. Bei c = 0 beträgt der kleinste Abstand zwischen bestem und zweitbestem Niveau in den 80 Zellen mehr als 0,007, ein Gleichstand tritt dort nicht auf (`tests/test_claims.py`).
- Die Simulation (Experiment 4) benutzt für alle Lieferzeiten und beide Politiken dieselben Zufallszahlen je Zufalls-Seed; die Abweichungen sind daher nicht unabhängig voneinander. Die vorgerechneten Werte (4 Zufalls-Seeds mit je 100.000 Pfaden) stammen aus `tools/measure_simulation.py`, die Live-Simulation hat so viele Pfade, wie der Regler vorgibt. Ob ein Wert „im Rahmen des Zufalls“ liegt, entscheidet die Schwelle von 3 Standardfehlern; sie ist eine Konvention, kein Test.
- Die Probe mit dem vollen Zustand (Bestand und Bestellungen unterwegs) rechnet in den Tests mit Bestellmengen bis 20 und einem Nettobestand von −45 bis 20; sie ist eine Probe der Gleichwertigkeit im endlichen Horizont (N = 3 Entscheidungen, Lieferzeit 0 bis 3, Einkaufspreis 0 und 3), die Demo selbst rechnet auf der Bestandsposition.
- Alle Beispiele sind erzeugt; echte Lagerdaten wurden nicht verwendet. Die App ist mit Streamlits AppTest durchlaufen, ein Durchlauf im Browser mit echten Mausklicks ist nicht Teil dieses Stands.

**Abgrenzung zu Nachbar-Demos** (nach deren README gelesen): `newsvendor-evpi-demo` behandelt eine einzige Entscheidung vor der Nachfrage (ein Standort in geschlossener Form, dann sechs Standorte als LP). `rolling-horizon-demo` gibt das bedingte Quantil als Regel vor und prüft es gegen eine dynamische Programmierung; hier ist die Rückwärtsrechnung der Gegenstand und die Quantil-Regel ihr Ergebnis. `value-iteration-demo` und `dynamic-programming-demo` erklären das Verfahren an anderen Zuständen.

## Verifikation

Die Suite hat **148 Tests**.

- **Kern:** Einheiten gegen Handrechnung auf der Mini-Instanz des Handbeispiels (Brüche, c = 0 und 1: S_1 bis S_3 und V_n), n = 1 gleich Newsvendor, konstante Nachfrage, Eigenschaften (V_n steigt mit p, S wächst mit Lieferzeit, Mittel und p/h, Verdoppeln von h und p ändert S nicht, V_n fällt in x bis S), Randfälle (n = 1, n = 2, Gleichstand zweier Niveaus, c ≥ p, Reglerränder), Zweig-Tests (Einkaufspreis ändert S_1, Lieferzeit ändert S, Mehrkosten bei c = 0 exakt 0 und bei c > 0 nicht 0).
- **Orakel:** `tests/test_oracle_bestell_rueckwaerts.py`: Niveau gegen scipy-Quantil und Aufzählung, Kostenfunktion gegen scipy, Rechnung mit dem vollen Zustand, exakt gegen eine unabhängige Simulation; die Handrechnung in Brüchen gegen die Gleitkomma-Rückwärtsrechnung steht in `tests/test_algorithm.py`.
- **Zahlen:** `tests/test_claims.py` (Tabelle „Befunde“), die vorgerechnete Simulation liegt in `data/simulation_vorgerechnet.json` (erzeugt von `tools/measure_simulation.py`, 7 KB).
- **Verdikte:** reine Funktionen `verdict_*` in `brw_evaluation.py`, Schwellen und Zahlen im Text in `tests/test_verdicts.py`, dazu die erwartete Zeile je Preset.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an seinen Grenzen, jedes Preset, c ≥ p), Layout (Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben), Footer, Laufzeit-Importe, Permalink (Begrenzen und Einrasten).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Handbeispiel, Ergebnis, Kernfrage, vier Experimente |
| `brw_algorithm.py` | Kern: Bellman-Schritt und Rückwärtsrechnung auf der Bestandsposition |
| `brw_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `brw_cost.py` | Periodenkosten G(y) |
| `brw_demand.py` | Poisson-Nachfrage, Faltung über die Wiederbeschaffungszeit, Dreipunkt-Nachfrage |
| `brw_evaluate.py` | Exakter Wert einer festen Politik, Anlaufkosten |
| `brw_evaluation.py` | Kennzahlen, Tabellen und Verdikte (reine Funktionen) |
| `brw_hand.py` | Handbeispiel in exakten Brüchen |
| `brw_layout.py` | Fester Kopf (Stylesheet) |
| `brw_policy.py` | Quantil-Regel aus der aufsummierten Poisson-Formel |
| `brw_presets.py` | Permalink (Begrenzen, Einrasten), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `brw_rng.py` | SplitMix64 (Portfolio-Konvention) |
| `brw_simulate.py` | Simulation der echten Bewegung von Bestand, Rückstand und Bestellungen |
| `brw_texts.py` | Texte der App, die die README wörtlich wiederholt |
| `brw_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `data/simulation_vorgerechnet.json` | Vorgerechnete Simulation (4 Zufalls-Seeds × 100.000 Pfade) |
| `tools/measure_grid.py` | Messreihe aller Zellen (dieselben Funktionen rechnet `tests/test_claims.py`) |
| `tools/measure_simulation.py` | Erzeugt die vorgerechnete Simulation |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnung, Orakel, Zahlen der README, Verdikte, Randfälle, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Bestellkosten je Bestellung** (aus Base-Stock wird dort eine (s, S)-Regel), **verlorene Nachfrage** (dort reicht die Bestandsposition nicht mehr), verderbliche Ware, mehrere Stufen und gelernte Politiken: sind nicht Gegenstand dieser Demo.
- **Diskontierung, Restwert, andere Nachfrageverteilungen, nicht ganzzahlige Mengen, Einkaufspreis ab p:** nicht gerechnet und nicht gemessen.
- **Bestellgrenze:** die Rückwärtsrechnung hat keine; die Gegenprobe mit dem vollen Zustand braucht eine (Bestellmengen bis 20) und rechnet nur im endlichen Horizont.
- **PDF-Export:** die Demo hat keinen; die Ergebnisse stehen in Tabellen der App.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Bestandspolitiken: von Base-Stock bis Regelwahl](https://sebastianhanisch.net/konzepte-bestandspolitiken.html).
