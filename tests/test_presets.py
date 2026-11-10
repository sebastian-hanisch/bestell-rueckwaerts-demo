"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink (Begrenzen und Einrasten)."""

import pytest

import brw_constants as C
import brw_evaluation as ev
import brw_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regulator_ranges():
    for name, p in C.PRESETS.items():
        assert C.L_MIN <= p["L"] <= C.L_MAX and p["ph"] in C.PH_OPTIONS and C.MEAN_MIN <= p["mean"] <= C.MEAN_MAX, name
        assert p["c"] in C.C_OPTIONS and C.N_MIN <= p["n"] <= C.N_MAX and p["paths"] in C.PATHS_OPTIONS, name
        assert 0 <= p["seed"] <= C.SEED_MAX and p["hand_c"] in C.HAND_C_OPTIONS, name
        assert p["c"] < p["ph"] * C.H_COST, f"{name}: Einkaufspreis muss unter p liegen (sonst nicht gerechnet)"


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS))
    assert ev.Settings(**C.PRESETS[first]) == ev.Settings()


def test_presets_differ_from_the_default_in_exactly_what_the_help_says():
    default = C.PRESETS["Vehikel (Voreinstellung)"]
    diff = lambda name: {k for k in default if C.PRESETS[name][k] != default[k]}  # noqa: E731
    assert diff("Handbeispiel mit Einkaufspreis") == {"hand_c"}
    assert diff("Lieferzeit 3") == {"L"}
    assert diff("Einkaufspreis und Lieferzeit 3") == {"L", "c"}


def test_preset_help_numbers_match_the_computation():
    """Hilfetexte sind Behauptungen: Niveau 5 (L = 0) und 17 (L = 3), Niveaus 13, 15, 16 bei c = 3 und L = 3."""
    assert ev.analyse(ev.Settings()).level == 5 and ev.analyse(ev.Settings(L=3)).level == 17
    assert ev.analyse(ev.Settings(L=3, c=3)).bw.S[1:5] == [13, 15, 16, 17]
    assert "von 5 auf 17" in C.PRESET_HELP["Lieferzeit 3"] and "13, 15, 16, danach 17" in C.PRESET_HELP["Einkaufspreis und Lieferzeit 3"]


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_selection_regulators_have_their_options_inside_their_bounds():
    for key, spec in P.SETTING_SPECS.items():
        if spec.options is not None:
            assert min(spec.options) == spec.lo and max(spec.options) == spec.hi, key
            assert spec.default in spec.options, key


def test_permalink_clamps_and_snaps_to_allowed_options(monkeypatch):
    """Ein Wert aus der Adresszeile wird begrenzt und bei Auswahlreglern auf den nächsten erlaubten Wert gesetzt (sonst wirft st.select_slider)."""
    state = {}
    monkeypatch.setattr(P.st, "session_state", state)
    monkeypatch.setattr(P.st, "query_params", {"L": "9", "ph": "3", "mean": "0", "c": "4", "n": "999", "paths": "30000", "seed": "-5", "hand_c": "1"})
    P.load_permalink_settings()
    assert state["L_slider"] == C.L_MAX and state["mean_slider"] == C.MEAN_MIN and state["n_slider"] == C.N_MAX and state["seed_input"] == 0
    assert state["ph_select"] == 2          # 3 liegt zwischen 2 und 4: der kleinere gewinnt bei Gleichstand
    assert state["c_select"] == 3           # 4 liegt zwischen 3 und 5
    assert state["paths_select"] == 20000   # 30000 liegt näher an 20000 als an 100000
    assert state["hand_c_radio"] == 1


def test_permalink_ignores_unparsable_values(monkeypatch):
    state = {}
    monkeypatch.setattr(P.st, "session_state", state)
    monkeypatch.setattr(P.st, "query_params", {"L": "abc"})
    P.load_permalink_settings()
    assert "L_slider" not in state and state["permalink_loaded"]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_can_be_analysed(name):
    p = C.PRESETS[name]
    assert ev.analyse(ev.Settings(**p)).level > 0
