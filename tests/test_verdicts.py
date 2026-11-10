"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier; dazu je Preset die erwartete Verdikt-Zeile (§11a Punkt 7)."""

import brw_constants as C
import brw_evaluation as ev
import brw_hand as H
from streamlit.testing.v1 import AppTest
from pathlib import Path

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_quantile_verdict_success_names_level_and_where():
    kind, text = ev.verdict_quantile(9, 9, ratio=0.9, L=1, mean=3)
    assert kind == "success" and "**S = 9**" in text
    assert "über 2 Perioden (Mittel 6,0)" in text and "0,900" in text


def test_quantile_verdict_uses_the_singular_for_lead_time_zero():
    assert "über 1 Periode (Mittel 3,0)" in ev.verdict_quantile(5, 5, ratio=0.9, L=0, mean=3)[1]


def test_quantile_verdict_warns_when_the_two_levels_differ():
    kind, text = ev.verdict_quantile(8, 9, ratio=0.9, L=1, mean=3)
    assert kind == "warning" and "S = 8" in text and "ist 9" in text


def test_stationary_verdict_one_rest_period():
    kind, text = ev.verdict_stationary(1, 5, [5, 5, 5], 0)
    assert kind == "success" and "**einer** Rest-Periode" in text and "S = 5" in text and "keine Mehrkosten" in text and "Einkaufspreis 0" in text


def test_stationary_verdict_lists_the_deviating_last_periods():
    kind, text = ev.verdict_stationary(4, 17, [13, 15, 16, 17, 17], 3)
    assert kind == "info" and "Die letzten 3 Perioden weichen ab" in text and "S_1 bis S_3 = 13, 15, 16" in text and "ab 4 Rest-Perioden gilt S = 17" in text
    assert "Deutung, nicht gemessen" in text and "Einkaufspreis 3" in text


def test_stationary_verdict_two_rest_periods_uses_the_singular():
    kind, text = ev.verdict_stationary(2, 5, [3, 5, 5], 3)
    assert kind == "info" and "Die letzten 1 Periode weichen ab" in text and "S_1 bis S_1 = 3" in text


def test_stationary_verdict_not_reached():
    kind, text = ev.verdict_stationary(None, 5, [3, 4], 3)
    assert kind == "warning" and "Niveau 5" in text


def test_grid_verdict_threshold_all_or_not():
    kind, text = ev.verdict_grid(20, 20, 3)
    assert kind == "success" and "**20 von 20** Zellen" in text and "Mittel 3" in text
    kind, text = ev.verdict_grid(19, 20, 3)
    assert kind == "warning" and "**19 von 20**" in text


def test_equivalence_verdict_three_cases():
    same = [{"L": 1, "mean": 3, "product": 6, "level": 9, "g": 4.6126}, {"L": 2, "mean": 2, "product": 6, "level": 9, "g": 4.6126}]
    kind, text = ev.verdict_equivalence(same)
    assert kind == "success" and "2 Kombinationen" in text and "(L + 1) · Mittel = 6" in text and "S = 9" in text and "4,6126" in text and "Poisson" in text
    kind, text = ev.verdict_equivalence([same[0], {**same[1], "level": 10}])
    assert kind == "warning" and "unterscheiden sich" in text
    kind, text = ev.verdict_equivalence([{**same[0], "product": 5}])
    assert kind == "info" and "= 5 gibt es" in text


def test_equivalence_verdict_names_the_conditions_of_the_statement():
    """Die Tabelle rechnet bei Einkaufspreis 0; Anlaufkosten hängen an Lieferzeit und Mittel einzeln (Prüfbericht P1)."""
    same = [{"L": 1, "mean": 3, "product": 6, "level": 9, "g": 4.6126}, {"L": 2, "mean": 2, "product": 6, "level": 9, "g": 4.6126}]
    text = ev.verdict_equivalence(same)[1]
    assert "Einkaufspreis 0" in text and "Anlaufkosten" in text and "nur über dieses Produkt" in text


def test_grid_verdict_says_purchase_price_zero_not_order_cost_zero():
    """„Bestellkosten 0“ wäre mit Fixkosten je Bestellung verwechselbar; gemeint ist der Einkaufspreis c = 0."""
    text = ev.verdict_grid(20, 20, 3)[1]
    assert "Einkaufspreis 0" in text and "Bestellkosten" not in text


def test_purchase_verdict_zero_branch_and_threshold():
    row = {"c": 0, "level": 5, "extra": 0.0, "extra_g": 0.0, "extra_pct": 0.0}
    kind, text = ev.verdict_purchase(row, 52)
    assert kind == "success" and "Einkaufspreis 0" in text and "52 Rest-Perioden" in text and "keine Mehrkosten" in text
    kind, text = ev.verdict_purchase({**row, "extra": 1e-10}, 1)
    assert kind == "success" and "1 Rest-Periode " in text                           # Schwelle 1e-9, Singular bei n = 1
    kind, text = ev.verdict_purchase({"c": 3, "level": 17, "extra": 7.1348, "extra_g": 1.106, "extra_pct": 0.85}, 52)
    assert kind == "info" and "S = 17" in text and "**7,13**" in text and "1,11 Periodenkosten" in text and "0,85 %" in text


def test_simulation_verdict_threshold_three_standard_errors():
    rows = [{"z": 1.5, "paths": 20000}, {"z": -3.0, "paths": 20000}]
    kind, text = ev.verdict_simulation(rows)
    assert kind == "success" and "20.000 Pfade" in text and "3,00 Standardfehler" in text           # genau 3: noch im Rahmen
    kind, text = ev.verdict_simulation([{"z": 3.01, "paths": 1000}])
    assert kind == "warning" and "1.000 Pfade" in text and "3,01" in text


def test_hand_verdict_both_branches():
    kind, text = ev.verdict_hand(H.solve(0))
    assert kind == "success" and "**auf 2 auffüllen**" in text and "Quantil (2)" in text and "= 3/4" in text and "G(2) = 1" in text
    kind, text = ev.verdict_hand(H.solve(1))
    assert kind == "info" and "S_1, S_2, S_3 = 1, 2, 2" in text and "(p − c)/(p + h) = 1/2" in text and "Quantil 1" in text


def test_de_formats_with_decimal_comma_and_thousands_with_dot():
    assert ev.de(3.346205, 4) == "3,3462" and ev.de(2.0, 0) == "2" and ev.thousands(100000) == "100.000" and ev.thousands(999) == "999"


def _verdicts_of(preset_name):
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    at.sidebar.button(key=f"preset_{preset_name}").click().run()
    assert not at.exception
    return [(kind, el.value) for kind in ("success", "info", "warning") for el in getattr(at, kind)]


def test_each_preset_shows_the_expected_verdict_lines():
    """Ein Preset ohne Effekt darf keinen Effekt melden: Stationarität nur ohne Einkaufspreis, Abweichung nur mit."""
    expectations = {
        "Vehikel (Voreinstellung)": ("Schon bei **einer** Rest-Periode gilt S = 5", "Die letzten"),
        "Handbeispiel mit Einkaufspreis": ("Schon bei **einer** Rest-Periode gilt S = 5", "S_1, S_2, S_3 = 1, 2, 2"),
        "Lieferzeit 3": ("Schon bei **einer** Rest-Periode gilt S = 17", "Die letzten"),
        "Einkaufspreis und Lieferzeit 3": ("S_1 bis S_3 = 13, 15, 16", "Schon bei **einer**"),
    }
    for name, (present, absent) in expectations.items():
        texts = [t for _, t in _verdicts_of(name)]
        assert any(present in t for t in texts), name
        if name == "Handbeispiel mit Einkaufspreis":
            assert any(absent in t for t in texts), name
        else:
            assert not any(absent in t for t in texts if "Handbeispiel" not in t and "Runden" not in t), name


def test_every_preset_equals_a_complete_setting():
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(C.DEFAULT_SETTINGS), name
