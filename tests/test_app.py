"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Preset-Button, fährt jeden
Regler (Slider, Auswahlregler, Radio) an seine Grenzen und prüft, dass kein Python-Fehler auftritt - insbesondere `StreamlitDuplicateElementId`
(mehrere st.plotly_chart ohne eindeutiges key=) und `StreamlitAPIException` bei Auswahlreglern mit ungültigem Wert."""

import os

from streamlit.testing.v1 import AppTest

import brw_constants as C
from brw_texts import ASSUMPTIONS_MARKDOWN, MATH_MARKDOWN

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert len(labels) == 3, labels
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_every_selection_regulator_at_its_first_and_last_option_does_not_raise():
    options = {"ph_select": C.PH_OPTIONS, "c_select": C.C_OPTIONS, "paths_select": C.PATHS_OPTIONS, "hand_c_radio": C.HAND_C_OPTIONS}
    for key, allowed in options.items():
        for value in (allowed[0], allowed[-1]):
            at = _fresh_app()
            widget = next(w for kind in ("select_slider", "radio") for w in getattr(at.sidebar, kind) if w.key == key)
            widget.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (key, value, [str(e) for e in at.exception])


def test_every_preset_runs_and_shows_all_sections():
    for name in C.PRESETS:
        at = _fresh_app()
        at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, name
        headings = " ".join(m.value for m in at.markdown)
        for wanted in ("🧮 Handbeispiel von Hand", "🎯 Ergebnis", "❓ Kernfrage"):
            assert wanted in headings, (name, wanted)
        subs = [s.value for s in at.subheader]
        assert [s.split(":")[0] for s in subs[:4]] == [f"🔬 Experiment {i}" for i in range(1, 5)] and "🚧 Wo die Annahmen enden" in subs, name


def test_purchase_price_not_below_the_penalty_shows_a_message_instead_of_numbers():
    at = _fresh_app()
    next(w for w in at.sidebar.select_slider if w.key == "ph_select").set_value(2)
    next(w for w in at.sidebar.select_slider if w.key == "c_select").set_value(3)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("nicht kleiner als die Strafkosten" in w.value for w in at.warning)
    assert not at.subheader or all(not s.value.startswith("🔬") for s in at.subheader)     # keine Experimente ohne Rechnung
    assert any("Handbeispiel" in m.value for m in at.markdown)                               # das Handbeispiel bleibt


def test_expanders_by_title_carry_the_shared_texts():
    at = _fresh_app()
    by_title = {e.label: e for e in at.expander}
    for wanted in ("⚠️ Annahmen, Grenzen und bekannte Probleme", "📐 Mathematische Formulierung"):
        assert wanted in by_title, list(by_title)
    assert by_title["⚠️ Annahmen, Grenzen und bekannte Probleme"].markdown[0].value.strip() == ASSUMPTIONS_MARKDOWN.strip()
    assert MATH_MARKDOWN.strip() in [m.value.strip() for m in by_title["📐 Mathematische Formulierung"].markdown]  # Lesehilfe-Block steht davor


def test_every_display_equation_is_its_own_block():
    """Je Display-Gleichung ein $$-Block (sonst KaTeX-Fehler, nur im Browser sichtbar): in jedem $$-Block steht keine zweite Gleichung, und die Zahl der $$ ist gerade."""
    for text in (MATH_MARKDOWN,) + tuple(m.value for m in _fresh_app().markdown):
        assert text.count("$$") % 2 == 0


def test_handbeispiel_switches_with_its_regulator():
    at = _fresh_app()
    next(w for w in at.sidebar.radio if w.key == "hand_c_radio").set_value(1)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("S_1, S_2, S_3 = 1, 2, 2" in s.value for s in at.info)
