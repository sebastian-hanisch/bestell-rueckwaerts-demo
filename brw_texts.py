"""Feste Texte der App, die die README wörtlich wiederholt (ein Test vergleicht beide Fassungen)."""

import brw_constants as C

INTRO_MARKDOWN = """
**Wie viel bestellen, wenn jede Periode zählt?** Diese Demo gibt die Bestellregel nicht vor, sie **findet** sie: Erst werden von Hand drei Perioden **rückwärts** gerechnet (Bellman-Rechnung: vom Ende des Horizonts zum Anfang), dann dieselbe Rechnung über bis zu 60 Perioden. Heraus kommt keine beliebige Tabelle, sondern eine einfache Regel: **bis zum Niveau S auffüllen** (Base-Stock), und S ist das **Quantil der Nachfrage über die Wiederbeschaffungszeit** (Lieferzeit plus eine Periode) zum Verhältnis p / (p + h). Bei Einkaufspreis 0 verschiebt die Lieferzeit das Niveau, sie ändert die Regel nicht.

Das gilt im Modell der Demo: Poisson-Nachfrage, Rückstand statt verlorener Nachfrage, Einkaufspreis 0, keine Bestellgrenze. Mit einem **Einkaufspreis** je Stück weichen die letzten Perioden ab; wie viele, zeigt das Experiment 3. Dies ist die erste Demo der Linie „Bestandspolitiken“; nach Abgleich der README-Texte der älteren Nachbar-Demos des Portfolios **bestimmt** keine von ihnen eine Bestellregel per exakter Rückwärtsrechnung, statt sie vorzugeben.

Weiter unten: das **Handbeispiel von Hand**, das **Ergebnis** für Ihre Einstellung, vier **🔬 Experimente**, **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""

HOW_IT_WORKS_MARKDOWN = """
1. **Zustand:** die **Bestandsposition** x = Bestand + bestellte, noch nicht angekommene Ware − Rückstand (Menge, die Kunden noch zusteht). Eine einzige Zahl genügt als Zustand; die Probe mit dem vollen Zustand (Bestand und jede einzelne Bestellung unterwegs) steht in den Tests.
2. **Rückwärts rechnen:** Für die letzte Periode kennt man die Kosten jedes Niveaus y, auf das man auffüllt. Für die vorletzte Periode kommt der beste Wert der letzten dazu, und so weiter bis zum Anfang. Das kleinste Minimum je Runde ist das Aufziehniveau S_n (n = Zahl der noch zu entscheidenden Perioden).
3. **Das Ergebnis hat eine feste Form** (im Modell der Demo in allen gerechneten Zellen): In jeder Runde ist die beste Bestellung max(S_n − x, 0), also „bis S_n auffüllen“. Bei Einkaufspreis 0 ist S_n schon ab einer Rest-Periode dasselbe S, und S ist ein **Quantil**: das kleinste Niveau, bei dem die Verteilungsfunktion der Nachfrage über Lieferzeit + 1 Perioden mindestens p / (p + h) erreicht. p sind die Kosten je fehlendem Stück und Periode, h die Lagerkosten je Stück und Periode.
4. **Warum das so ausgeht:** Bei Einkaufspreis 0 und ohne Restwert hat jede Periode dieselbe untere Schranke der Kosten, und das Auffüllen auf S erreicht sie jedes Mal (Herleitung im Expander „📐 Mathematische Formulierung“).
"""

DELIMIT_MARKDOWN = """
**Abgrenzung zu Nachbar-Demos** (nach deren README gelesen):
- `newsvendor-evpi-demo` behandelt eine einzige Entscheidung vor der Nachfrage (ein Standort in geschlossener Form, dann sechs Standorte als LP). Hier folgen mehrere Perioden aufeinander, mit Rückstand, Lieferzeit und der Frage nach der **Politik** statt einer Menge.
- `rolling-horizon-demo` gibt das bedingte Quantil als Regel vor und prüft es gegen eine dynamische Programmierung. Hier ist die Rückwärtsrechnung der Gegenstand und die Quantil-Regel ihr Ergebnis; die Persistenz der Nachfrage (AR(1)) bleibt dort.
- `value-iteration-demo` und `dynamic-programming-demo` erklären das Verfahren an einem Raster und an einem Rucksack; das Verfahren wird hier nicht noch einmal erklärt, sondern auf den Bestandszustand angewandt.
"""

ASSUMPTIONS_MARKDOWN = f"""
**Annahmen**
- **Ein Artikel**, **Poisson-Nachfrage** mit ganzzahligem Mittel {C.MEAN_MIN} bis {C.MEAN_MAX} je Periode, unabhängig und gleich verteilt; Lagerkosten h = 1 je Stück und Periode, Strafkosten p = (p/h) · h je fehlendem Stück und Periode.
- **Rückstand:** Fehlmengen werden nachgeliefert und kosten p je Stück und Periode; verlorene Nachfrage ist ein anderes Modell und hier nicht gerechnet.
- **Zeitablauf:** Bestellung zu Beginn der Periode, sie steht für die Nachfrage der Periode t + L bereit (L = 0: sofort). Start bei Bestandsposition 0 mit nichts unterwegs.
- **Einkaufspreis c** je bestelltem Stück ({", ".join(str(c) for c in C.C_OPTIONS)}), der Rest am Ende des Horizonts ist **nichts wert**. Bestellungen der letzten L Perioden kämen nach dem Horizont an und werden nicht gerechnet.
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
"""

MATH_MARKDOWN = r"""
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

**Kosten einer Periode.** Wer auf $y$ auffüllt, zahlt für die Periode, in der die Bestellung ankommt:

$$G(y) = \mathbb{E}\left[\, h\,(y - D^{(L+1)})^{+} + p\,(D^{(L+1)} - y)^{+} \right]$$

**Bellman-Gleichung** (rückwärts, $V_0 = 0$):

$$V_n(x) = \min_{y \ge x} \Big\{ c\,(y - x) + G(y) + \mathbb{E}\,V_{n-1}(y - D) \Big\}$$

**Quantil-Satz** ($c = 0$, Rückstand, keine Bestellgrenze; Herleitung unten, gemessen für Poisson-Nachfrage in 80 Zellen): Für jedes $n \ge 1$ gilt

$$S_n = S = \min\Big\{ k : \Pr\big(D^{(L+1)} \le k\big) \ge \frac{p}{p + h} \Big\}$$

Mit Einkaufspreis $c$ und unbewertetem Rest gilt dieselbe Form für die letzte Periode mit dem Verhältnis $(p - c)/(p + h)$ (Messbefund); die Niveaus der davorliegenden Perioden unterscheiden sich von $S$ nur in den letzten $n^* - 1$ Perioden ($n^* = 2$ bis $5$ in den 32 Zellen der Mehrkosten-Tabelle der README).

**Herleitung der Stationarität bei $c = 0$** (eigene Rechnung, keine Quellenaussage): Für jede Position $z$ gilt $V_{n-1}(z) \ge (n-1)\min G$, denn jede der $n - 1$ Perioden kostet mindestens $\min G$. Also ist $V_n(x) \ge \min G + (n-1)\min G = n \min G$. Für $x \le S$ erreicht das Auffüllen auf $S$ diese Schranke, weil die nächste Position $S - D$ wieder höchstens $S$ beträgt. Dass $S$ das kleinste Minimum von $G$ ist, folgt aus $G(y + 1) - G(y) = (p + h)\,\Pr\big(D^{(L+1)} \le y\big) - p$: Die Differenz ist negativ, solange die Verteilungsfunktion unter $p/(p + h)$ liegt, und erst ab dem Quantil nicht mehr. Daher ist $S$ in jeder Rest-Periode dasselbe und $V_n(x) = n\,G(S)$ für $x \le S$. Mit Einkaufspreis lässt sich das Auffüllen auf das Niveau der nächsten Periode nicht mehr voraussetzen, die Herleitung fällt.

**Literatur.** Xin und Goldberg (arXiv 1409.1499, S. 2) nennen für Rückstand mit positiver Lieferzeit Base-Stock als optimal und verweisen auf Scarf (1960), Iglehart (1963) und Veinott (1966); diese drei Originale wurden hier nicht gelesen (Angabe nach Xin und Goldberg). Die Quantil-Formel für das Niveau ist die Newsvendor-Formel für die Nachfrage über $L + 1$ Perioden; ihre Gleichheit mit der Rückwärtsrechnung folgt bei $c = 0$ aus der Herleitung oben und ist in den 80 Zellen gemessen, nicht aus einer Quelle übernommen.
"""
