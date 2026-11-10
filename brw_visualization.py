"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import brw_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_levels(levels: list, quantile: int, n_show: int):
    """Aufziehniveau S_n je Rest-Periodenzahl n (n = 1 ist die letzte Periode) und das Quantil als waagerechte Linie."""
    n_show = max(1, min(n_show, len(levels) - 1))
    xs = list(range(1, n_show + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=levels[1:n_show + 1], mode="lines+markers", line=dict(color=C.COLOR_DP, width=3), name="Rückwärtsrechnung S_n",
                             hovertemplate="noch %{x} Perioden: S = %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[1, max(n_show, 2)], y=[quantile, quantile], mode="lines", line=dict(color=C.COLOR_QUANTILE, width=2, dash="dash"),
                             name="Quantil (geschlossene Formel)", hoverinfo="skip"))
    fig.update_xaxes(title_text="Rest-Perioden n (1 = letzte Periode)")
    fig.update_yaxes(title_text="Aufziehniveau S_n")
    return _base(fig)


def build_cdf(cdf, ratio: float, level: int, mean_total: float):
    """Verteilungsfunktion der Nachfrage über L + 1 Perioden als Treppe, das kritische Verhältnis und das Niveau S."""
    kmax = max(int(level + 3 * mean_total ** 0.5 + 3), level + 4)
    ks = list(range(0, min(kmax, len(cdf) - 1) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[float(cdf[k]) for k in ks], mode="lines", line=dict(color=C.COLOR_FIXED, width=3, shape="hv"), name="Verteilungsfunktion F(k)",
                             hovertemplate="F(%{x}) = %{y:.4f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[ks[0], ks[-1]], y=[ratio, ratio], mode="lines", line=dict(color=C.COLOR_QUANTILE, dash="dash"), name="kritisches Verhältnis",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[level], y=[float(cdf[level])], mode="markers", marker=dict(color=C.COLOR_DP, size=12), name=f"S = {level}",
                             hovertemplate="S = %{x}<extra></extra>"))
    fig.update_xaxes(title_text="Nachfrage k über die Wiederbeschaffungszeit")
    fig.update_yaxes(title_text="F(k)", range=[0, 1.02])
    return _base(fig)


def build_cost_growth(values: list, g: float, n_show: int):
    """Steuerbare Kosten V_n(0) über die Rest-Periodenzahl n und die Gerade n mal Periodenkosten beim Niveau S."""
    n_show = max(1, min(n_show, len(values) - 1))
    xs = list(range(1, n_show + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=values[1:n_show + 1], mode="lines", line=dict(color=C.COLOR_DP, width=3), name="V_n(0), Rückwärtsrechnung",
                             hovertemplate="n = %{x}: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[n * g for n in xs], mode="lines", line=dict(color=C.COLOR_QUANTILE, dash="dot"), name="n · G(S)", hoverinfo="skip"))
    fig.update_xaxes(title_text="Rest-Perioden n")
    fig.update_yaxes(title_text="Kosten")
    return _base(fig)


def build_purchase_levels(rows: list[dict]):
    """Niveaus S_1, S_2, ... der letzten Perioden, je eine Linie je Einkaufspreis."""
    fig = go.Figure()
    palette = ["#2F6B65", "#4c78a8", "#e07b39", "#9c4f96"]
    for color, row in zip(palette, rows):
        xs = list(range(1, len(row["levels"]) + 1))
        fig.add_trace(go.Scatter(x=xs, y=row["levels"], mode="lines+markers", line=dict(color=color, width=2), name=f"Einkaufspreis {row['c']}",
                                 hovertemplate="noch %{x} Perioden: S = %{y}<extra></extra>"))
    fig.update_xaxes(title_text="Rest-Perioden n (1 = letzte Periode)", dtick=1)
    fig.update_yaxes(title_text="Aufziehniveau S_n")
    return _base(fig)


def build_simulation(rows: list[dict]):
    """Exakter Gesamtwert (Raute) und Simulationsmittel mit Fehlerbalken (± 2 Standardfehler) je Politik."""
    names = [r["policy"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=names, y=[r["sim"] for r in rows], mode="markers", marker=dict(color=C.COLOR_FIXED, size=10), name="Simulation",
                             error_y=dict(type="data", array=[2 * r["se"] for r in rows], visible=True),
                             hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=names, y=[r["exact"] for r in rows], mode="markers", marker=dict(color=C.COLOR_QUANTILE, size=12, symbol="diamond"),
                             name="exakt", hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title_text="Gesamtkosten")
    return _base(fig, height=300)
