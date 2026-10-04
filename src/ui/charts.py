"""
charts.py — Grafik interaktif Plotly dan SVG sparkline generators.

Menyediakan:
1. SVG sparkline (line, bar, gauge) untuk embed dalam kartu dashboard
2. Plotly chart untuk harga historis vs Intrinsic Value
3. Plotly chart untuk proyeksi Future Value
"""

import math
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.utils.formatter import format_rupiah


# ═══════════════════════════════════════════════════════
# SVG SPARKLINE GENERATORS — untuk kartu dashboard
# ═══════════════════════════════════════════════════════

def svg_sparkline(
    values: list[float],
    width: int = 140,
    height: int = 45,
    color: str = "#00E676",
    fill: bool = True,
) -> str:
    """
    Generate SVG sparkline (line chart) kecil untuk embed di kartu.

    Args:
        values: List nilai numerik.
        width: Lebar SVG dalam pixel.
        height: Tinggi SVG dalam pixel.
        color: Warna garis.
        fill: Jika True, isi area di bawah garis.

    Returns:
        String SVG yang bisa di-embed dalam HTML.
    """
    if not values or len(values) < 2:
        return ""

    padding = 4
    w = width - padding * 2
    h = height - padding * 2

    min_v = min(values)
    max_v = max(values)
    range_v = max_v - min_v if max_v != min_v else 1

    points = []
    for i, v in enumerate(values):
        x = padding + (i / (len(values) - 1)) * w
        y = padding + h - ((v - min_v) / range_v) * h
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)

    fill_path = ""
    if fill:
        # Area fill di bawah garis
        fill_points = f"{padding:.1f},{padding + h:.1f} " + polyline + f" {padding + w:.1f},{padding + h:.1f}"
        fill_path = f'<polygon points="{fill_points}" fill="{color}" fill-opacity="0.08" />'

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
        xmlns="http://www.w3.org/2000/svg" style="display:block;">
        {fill_path}
        <polyline points="{polyline}" fill="none" stroke="{color}"
            stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
    </svg>"""


def svg_bar_chart(
    values: list[float],
    labels: list[str] | None = None,
    width: int = 140,
    height: int = 55,
    color: str = "#448AFF",
) -> str:
    """
    Generate SVG bar chart kecil untuk embed di kartu.

    Args:
        values: List nilai numerik per bar.
        labels: Opsional, label di bawah setiap bar.
        width: Lebar SVG.
        height: Tinggi SVG.
        color: Warna bar.

    Returns:
        String SVG.
    """
    if not values:
        return ""

    n = len(values)
    padding = 4
    label_h = 14 if labels else 0
    bar_area_w = width - padding * 2
    bar_area_h = height - padding * 2 - label_h

    bar_w = max(8, (bar_area_w / n) * 0.6)
    gap = (bar_area_w - bar_w * n) / max(1, n - 1) if n > 1 else 0

    min_v = min(values)
    max_v = max(values)
    range_v = max_v - min_v if max_v != min_v else 1

    bars = []
    for i, v in enumerate(values):
        x = padding + i * (bar_w + gap)
        bar_h = max(3, ((v - min_v) / range_v) * bar_area_h)
        y = padding + bar_area_h - bar_h

        # Opacity ramp: older bars are more transparent
        opacity = 0.3 + 0.5 * (i / max(1, n - 1))
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'rx="2" fill="{color}" fill-opacity="{opacity:.2f}" />'
        )

        if labels and i < len(labels):
            lx = x + bar_w / 2
            ly = padding + bar_area_h + label_h - 2
            bars.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                f'font-size="7" fill="#999999" font-family="Inter,sans-serif">{labels[i]}</text>'
            )

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
        xmlns="http://www.w3.org/2000/svg" style="display:block;">
        {"".join(bars)}
    </svg>"""


def svg_gauge(
    percentage: float,
    size: int = 130,
    color: str = "#00E676",
    bg_color: str = "#2a2d3e",
    label: str = "",
) -> str:
    """
    Generate SVG gauge (semicircle) untuk Margin of Safety.

    Args:
        percentage: Nilai 0.0 - 1.0 (akan di-clamp).
        size: Ukuran SVG.
        color: Warna gauge aktif.
        bg_color: Warna latar gauge.
        label: Label di tengah gauge.

    Returns:
        String SVG.
    """
    pct = max(0.0, min(1.0, abs(percentage)))
    cx, cy = size / 2, size * 0.55
    r = size * 0.38

    # Arc semicircle (180 derajat)
    # Titik awal (kiri) dan akhir (kanan)
    start_angle = math.pi  # 180 derajat
    end_angle = 0  # 0 derajat

    # Background arc (full semicircle)
    bg_x1 = cx + r * math.cos(start_angle)
    bg_y1 = cy - r * math.sin(start_angle)
    bg_x2 = cx + r * math.cos(end_angle)
    bg_y2 = cy - r * math.sin(end_angle)

    bg_path = f"M {bg_x1:.1f} {bg_y1:.1f} A {r:.1f} {r:.1f} 0 1 1 {bg_x2:.1f} {bg_y2:.1f}"

    # Filled arc (berdasarkan persentase)
    fill_angle = start_angle - pct * math.pi
    fill_x = cx + r * math.cos(fill_angle)
    fill_y = cy - r * math.sin(fill_angle)
    large_arc = 1 if pct > 0.5 else 0

    fill_path = f"M {bg_x1:.1f} {bg_y1:.1f} A {r:.1f} {r:.1f} 0 {large_arc} 1 {fill_x:.1f} {fill_y:.1f}"

    # Tampilkan persentase di tengah
    pct_text = f"{percentage * 100:.1f}%"

    return f"""<svg width="{size}" height="{int(size * 0.65)}" viewBox="0 0 {size} {int(size * 0.65)}"
        xmlns="http://www.w3.org/2000/svg" style="display:block;margin:0 auto;">
        <path d="{bg_path}" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="8" stroke-linecap="round" />
        <path d="{fill_path}" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" />
        <text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="18" font-weight="600"
            fill="#ffffff" font-family="Inter,sans-serif">{pct_text}</text>
        <text x="{cx}" y="{cy + 13}" text-anchor="middle" font-size="8" font-weight="500"
            fill="#999999" font-family="Inter,sans-serif">{label}</text>
    </svg>"""


def svg_dual_gauge(
    val1: float,
    val2: float,
    label1: str = "ROE",
    label2: str = "ROIC",
    size: int = 60,
    color: str = "#448AFF",
) -> str:
    """
    Generate dua gauge kecil berdampingan untuk ROE/ROIC.

    Args:
        val1, val2: Nilai desimal (misal 0.243 = 24.3%).
        label1, label2: Label masing-masing gauge.
        size: Ukuran per gauge.
        color: Warna gauge.

    Returns:
        String SVG gabungan.
    """
    total_w = size * 2 + 20
    g1 = _mini_gauge(val1, label1, cx=size * 0.5 + 2, cy=size * 0.45, r=size * 0.35, size=size, color=color)
    g2 = _mini_gauge(val2, label2, cx=size * 1.5 + 18, cy=size * 0.45, r=size * 0.35, size=size, color=color)

    gauge_h = int(size * 0.7)
    return f"""<svg width="{total_w}" height="{gauge_h}" viewBox="0 0 {total_w} {gauge_h}"
        xmlns="http://www.w3.org/2000/svg" style="display:block;margin:0 auto;">
        {g1}{g2}
    </svg>"""


def _mini_gauge(
    value: float, label: str, cx: float, cy: float, r: float, size: int, color: str
) -> str:
    """Helper: satu gauge kecil."""
    pct = max(0.0, min(1.0, abs(value)))
    start_angle = math.pi
    bg_x1 = cx + r * math.cos(start_angle)
    bg_y1 = cy - r * math.sin(start_angle)
    bg_x2 = cx + r * math.cos(0)
    bg_y2 = cy - r * math.sin(0)
    bg_path = f"M {bg_x1:.1f} {bg_y1:.1f} A {r:.1f} {r:.1f} 0 1 1 {bg_x2:.1f} {bg_y2:.1f}"

    fill_angle = start_angle - pct * math.pi
    fill_x = cx + r * math.cos(fill_angle)
    fill_y = cy - r * math.sin(fill_angle)
    la = 1 if pct > 0.5 else 0
    fill_path = f"M {bg_x1:.1f} {bg_y1:.1f} A {r:.1f} {r:.1f} 0 {la} 1 {fill_x:.1f} {fill_y:.1f}"

    pct_text = f"{value * 100:.1f}%"

    return f"""
        <path d="{bg_path}" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="5" stroke-linecap="round" />
        <path d="{fill_path}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round" />
        <text x="{cx}" y="{cy + 1}" text-anchor="middle" font-size="10" font-weight="600"
            fill="#fff" font-family="Inter,sans-serif">{pct_text}</text>
        <text x="{cx}" y="{cy + 12}" text-anchor="middle" font-size="7" font-weight="500"
            fill="#999999" font-family="Inter,sans-serif">{label}</text>
    """


# ═══════════════════════════════════════════════════════
# PLOTLY CHARTS — minimalist styling
# ═══════════════════════════════════════════════════════

def plot_historical_vs_intrinsic(
    price_history: pd.DataFrame,
    intrinsic_value: float,
) -> None:
    """
    Line chart Plotly: harga historis vs garis Intrinsic Value.

    Args:
        price_history: DataFrame kolom 'date', 'close'.
        intrinsic_value: Nilai intrinsik per saham dari DCF.
    """
    if price_history.empty or "close" not in price_history.columns:
        st.warning("Data harga historis tidak tersedia.")
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=price_history["date"], y=price_history["close"],
        mode="lines", name="Market Price",
        line=dict(color="#C682B3", width=1.5),
        fill="tozeroy", fillcolor="rgba(198,130,179,0.04)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Rp %{y:,.0f}<extra></extra>",
    ))

    if intrinsic_value and intrinsic_value > 0:
        fig.add_hline(
            y=intrinsic_value,
            line=dict(color="#69B37A", width=1.5, dash="dash"),
            annotation_text=f"Intrinsic: {format_rupiah(intrinsic_value)}",
            annotation_position="top right",
            annotation_font=dict(color="#69B37A", size=10, family="Inter"),
        )

    fig.update_layout(
        title=dict(
            text="Price vs Intrinsic Value",
            font=dict(size=13, color="#FFFFFF", family="Inter"),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.03)",
            showgrid=True,
            color="#999999",
            tickfont=dict(size=10, family="Inter"),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.03)",
            showgrid=True,
            tickformat=",",
            color="#999999",
            tickfont=dict(size=10, family="Inter"),
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(34,34,38,0.4)",
        height=360,
        hovermode="x unified",
        margin=dict(l=50, r=15, t=45, b=30),
        legend=dict(
            orientation="h", y=1.08, x=0.5, xanchor="center",
            font=dict(size=10, family="Inter", color="#999999"),
        ),
        font=dict(family="Inter"),
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_future_projection(
    projected_values: list[dict],
    label: str = "Future Value Projection",
) -> None:
    """
    Chart proyeksi Future Value dari relasi rekurensi.

    Args:
        projected_values: List of dict { "period": int, "value": float }
        label: Judul grafik.
    """
    if not projected_values:
        st.warning("Data proyeksi tidak tersedia.")
        return

    df = pd.DataFrame(projected_values)
    n = len(df)
    # Monochrome accent ramp
    colors = [f"rgba(198, 130, 179, {0.25 + 0.55*(i/max(1,n-1)):.2f})" for i in range(n)]
    x_col = "year" if "year" in df.columns else ("period" if "period" in df.columns else df.columns[0])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df[x_col], y=df["value"], name="Future Value",
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.06)", width=1)),
        hovertemplate="<b>Tahun %{x}</b><br>Rp %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df[x_col], y=df["value"], mode="lines+markers", name="Trend",
        line=dict(color="#C682B3", width=1.5), marker=dict(size=4, color="#C682B3"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(
            text=label,
            font=dict(size=13, color="#FFFFFF", family="Inter"),
        ),
        xaxis=dict(
            title="Tahun",
            type="category",
            gridcolor="rgba(255,255,255,0.03)",
            color="#999999",
            tickfont=dict(size=10, family="Inter"),
            title_font=dict(size=10, family="Inter", color="#999999"),
        ),
        yaxis=dict(
            title="Nilai (Rp)",
            gridcolor="rgba(255,255,255,0.03)",
            tickformat=",",
            color="#999999",
            tickfont=dict(size=10, family="Inter"),
            title_font=dict(size=10, family="Inter", color="#999999"),
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(34,34,38,0.4)",
        height=360,
        showlegend=False,
        margin=dict(l=50, r=15, t=45, b=30),
        font=dict(family="Inter"),
    )

    st.plotly_chart(fig, use_container_width=True)
