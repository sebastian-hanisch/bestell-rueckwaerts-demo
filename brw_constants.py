"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# Feste Annahmen des Modells (Lagerkosten je Stück und Periode; Strafkosten p ergeben sich aus dem Verhältnis p/h)
H_COST = 1.0

# Regler
L_MIN, L_MAX, DEFAULT_L = 0, 3, 0                  # Lieferzeit in Perioden
PH_OPTIONS = (1, 2, 4, 9, 19)                      # Strafverhältnis p/h (h = 1)
DEFAULT_PH = 9
MEAN_MIN, MEAN_MAX, DEFAULT_MEAN = 2, 5, 3         # Mittel der Poisson-Nachfrage je Periode
C_OPTIONS = (0, 1, 3, 5)                           # Einkaufspreis c je bestelltem Stück (Rest am Ende unbewertet)
DEFAULT_C = 0
N_MIN, N_MAX, DEFAULT_N = 1, 60, 52                # Zahl der noch zu entscheidenden Perioden
PATHS_OPTIONS = (1000, 5000, 20000, 100000)        # Pfade der Live-Simulation
DEFAULT_PATHS = 20000
SEED_MAX, DEFAULT_SEED = 999999, 11                # Zufalls-Seed der Simulation
HAND_C_OPTIONS = (0, 1)                            # Einkaufspreis im Handbeispiel

# Rechenumfang
NMAX = 60                                          # Rest-Perioden, die jede Rückwärtsrechnung mitrechnet
STATIONARY_TOL = 1e-9                              # Toleranz, mit der Minima als gleich gelten (Kosten)

# Handbeispiel: Nachfrage 0, 1, 2 mit je 1/3, h = 1, p = 3, Lieferzeit 0, drei Perioden
HAND_DEMAND = (0, 1, 2)
HAND_H, HAND_P, HAND_ROUNDS = 1, 3, 3
HAND_Y = (0, 1, 2, 3)                              # gezeigte Bestandsniveaus nach der Bestellung

# Vorgerechnete Simulation (tools/measure_simulation.py): 4 Zufalls-Seeds mit je 100.000 Pfaden
SIM_SEEDS = (11, 12, 13, 14)
SIM_PATHS_PRECOMPUTED = 100000
SIM_HORIZON = 52
SIM_MEAN, SIM_PH = 3, 9
SIM_C_VALUES = (0, 3)

COLOR_DP = "#2F6B65"
COLOR_QUANTILE = "#c0392b"
COLOR_FIXED = "#4c78a8"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_BAND = "rgba(76,120,168,0.18)"

DEFAULT_SETTINGS = {"L": DEFAULT_L, "ph": DEFAULT_PH, "mean": DEFAULT_MEAN, "c": DEFAULT_C, "n": DEFAULT_N,
                    "paths": DEFAULT_PATHS, "seed": DEFAULT_SEED, "hand_c": 0}

PRESETS = {
    "Vehikel (Voreinstellung)": dict(DEFAULT_SETTINGS),
    "Handbeispiel mit Einkaufspreis": {**DEFAULT_SETTINGS, "hand_c": 1},
    "Lieferzeit 3": {**DEFAULT_SETTINGS, "L": 3},
    "Einkaufspreis und Lieferzeit 3": {**DEFAULT_SETTINGS, "L": 3, "c": 3},
}
PRESET_HELP = {
    "Vehikel (Voreinstellung)": "Poisson-Nachfrage mit Mittel 3, Strafverhältnis p/h = 9, Lieferzeit 0, Einkaufspreis 0, 52 Perioden: die Messreihe der Demo. Das Handbeispiel steht auf c = 0.",
    "Handbeispiel mit Einkaufspreis": "Schaltet nur das Handbeispiel (Abschnitt 1) auf Einkaufspreis 1: dort weicht die letzte Periode von den beiden davor ab. Die Rechnung darunter bleibt beim Vehikel.",
    "Lieferzeit 3": "Wie das Vehikel (Einkaufspreis 0), aber Lieferzeit 3: das Niveau steigt von 5 auf 17, die Regel bleibt dieselbe.",
    "Einkaufspreis und Lieferzeit 3": "Einkaufspreis 3 bei Lieferzeit 3: die letzten Perioden bestellen weniger (Niveaus 13, 15, 16, danach 17).",
}
