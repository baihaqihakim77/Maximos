"""
scorecard.py — Grid visual 9 pilar value investing dalam kartu dashboard.

Desain Fixed Grid Cockpit:
    Left (3×3 grid):
        Row 1: [01 Business]  | [02 Revenue]   | [03 Profit]
        Row 2: [04 Cash Flow] | [05 ROIC / ROE]| [06 Debt Health]
        Row 3: [07 Growth]    | [08 Valuation] | [09 Margin of Safety]
    Right (Fixed Height Column):
        Summary (Narasi AI Analis, Action Badge, dan Skor Fundamental)
"""

from datetime import datetime
import textwrap
import pandas as pd
import streamlit as st

from src.ui.charts import svg_sparkline, svg_bar_chart
from src.utils.formatter import format_rupiah_short, format_percent


# ═══════════════════════════════════════════════════════
# INLINE SVG ICONS (Lucide-style, 16×16, stroke-based)
# ═══════════════════════════════════════════════════════

_ICON = {
    "business": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="12.01"/></svg>',
    "revenue": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "profit": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "cashflow": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/><path d="M2 12h4m12 0h4"/></svg>',
    "target": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "debt": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20.2 7.8l-7.7 7.7-4-4-5.7 5.7"/><path d="M15 7h6v6"/></svg>',
    "growth": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/></svg>',
    "diamond": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M2 9h20"/></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "summary": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A6A6B4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
}


# ═══════════════════════════════════════════════════════
# CSS DESIGN SYSTEM — FIXED CARD GEOMETRY & DISTINCT BOUNDARIES
# ═══════════════════════════════════════════════════════

_CARD_CSS = """
<style>
/* ── Kartu Dasar Fixed Grid ── */
.vi-card {
    background: #1B1B20;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-top: 2.5px solid rgba(198, 130, 179, 0.45);
    border-radius: 12px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.85rem;
    position: relative;
    overflow: hidden;
    height: 220px;
    min-height: 220px;
    max-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4);
    transition: all 0.25s ease;
}
.vi-card:hover {
    border-color: rgba(198, 130, 179, 0.55);
    border-top-color: #C682B3;
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.55), 0 0 1px rgba(198, 130, 179, 0.3);
    transform: translateY(-2px);
}
.vi-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}
.vi-card-title {
    display: flex;
    align-items: center;
    gap: 7px;
}
.vi-pillar-num {
    font-size: 0.62rem;
    font-weight: 700;
    color: #C682B3;
    background: rgba(198, 130, 179, 0.12);
    border: 1px solid rgba(198, 130, 179, 0.3);
    padding: 1px 5px;
    border-radius: 4px;
    letter-spacing: 0.04em;
}
.vi-card-title .icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.04);
}
.vi-card-title .label {
    font-size: 0.74rem;
    font-weight: 600;
    color: #E2E2EA;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.vi-card-value {
    font-size: 0.72rem;
    font-weight: 500;
    color: #A4A4B2;
}
.vi-card-big-value {
    font-size: 1.05rem;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 2px;
    letter-spacing: -0.01em;
}
.vi-card-desc {
    font-size: 0.68rem;
    color: #9A9AA6;
    line-height: 1.45;
}
.vi-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin-top: auto;
}
.vi-card-chart {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 2px 0;
    flex: 1;
}

/* ── Badges ── */
.vi-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    line-height: 1.3;
}
.vi-badge-pass {
    background: rgba(105, 179, 122, 0.16);
    color: #69B37A;
    border: 1px solid rgba(105, 179, 122, 0.35);
}
.vi-badge-fail {
    background: rgba(255, 94, 94, 0.16);
    color: #FF5E5E;
    border: 1px solid rgba(255, 94, 94, 0.35);
}
.vi-badge-warn {
    background: rgba(255, 214, 0, 0.16);
    color: #FFD600;
    border: 1px solid rgba(255, 214, 0, 0.35);
}

/* ── Dua / Tiga Nilai Berdampingan ── */
.vi-stats-row {
    display: flex;
    align-items: center;
    justify-content: space-around;
    padding: 0.25rem 0;
}
.vi-stat {
    text-align: center;
    flex: 1;
}
.vi-stat-val {
    font-size: 0.95rem;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: -0.01em;
}
.vi-stat-label {
    font-size: 0.58rem;
    color: #8E8E9C;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 2px;
}

/* ── Kartu Ringkasan Fixed Height (Kanan) ── */
.vi-card-tall {
    background: #1B1B20;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-top: 2.5px solid #C682B3;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 0.85rem;
    position: relative;
    overflow: hidden;
    height: 686px;
    min-height: 686px;
    max-height: 686px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4);
    transition: all 0.25s ease;
}
.vi-card-tall:hover {
    border-color: rgba(198, 130, 179, 0.55);
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.55);
}
.vi-summary-scroll {
    overflow-y: auto;
    padding-right: 6px;
    flex: 1;
    margin: 10px 0;
}
.vi-summary-scroll::-webkit-scrollbar {
    width: 4px;
}
.vi-summary-scroll::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 4px;
}
.vi-summary-text {
    font-size: 0.73rem;
    color: #B4B4C2;
    line-height: 1.65;
}

/* ── Divider ── */
.vi-divider {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin: 6px 0;
}

/* ── Progress Bar ── */
.vi-progress-track {
    background: rgba(255, 255, 255, 0.06);
    border-radius: 2px;
    height: 4px;
    overflow: hidden;
}
.vi-progress-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}
</style>
"""

def _inject_css() -> None:
    """Inject CSS pada setiap render agar styles selalu aktif di browser."""
    st.markdown(_CARD_CSS, unsafe_allow_html=True)


def _render_html(html_str: str) -> None:
    """Helper render HTML aman via st.markdown dengan membersihkan indentasi tanpa memotong whitespace."""
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# FUNGSI UTAMA RENDER SCORECARD
# ═══════════════════════════════════════════════════════

def render_scorecard(
    pilar_scores: dict,
    income_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    cashflow_df: pd.DataFrame,
    company_report: dict,
    current_price: float,
    price_change_pct: float,
    narrative: str,
    action: str,
    company_name: str,
) -> None:
    """
    Tampilkan grid dashboard 9 pilar dalam layout fixed 3×3 + Summary.
    """
    _inject_css()

    # Layout utama: left grid (3×3) + right column (Summary)
    main_left, main_right = st.columns([3, 1.25])

    with main_left:
        # Baris 1: 01 Business | 02 Revenue | 03 Profit
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            _card_business(pilar_scores, company_name)
        with r1c2:
            _card_revenue(pilar_scores, income_df)
        with r1c3:
            _card_profit(pilar_scores, income_df)

        # Baris 2: 04 Cash Flow | 05 ROIC/ROE | 06 Debt Health
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            _card_cashflow(pilar_scores, cashflow_df)
        with r2c2:
            _card_roic_roe(pilar_scores)
        with r2c3:
            _card_debt(pilar_scores)

        # Baris 3: 07 Growth CAGR | 08 Valuation DCF | 09 Margin of Safety
        r3c1, r3c2, r3c3 = st.columns(3)
        with r3c1:
            _card_growth(pilar_scores, income_df)
        with r3c2:
            _card_valuation(pilar_scores, company_report, current_price)
        with r3c3:
            _card_margin_of_safety(pilar_scores, current_price)

    with main_right:
        _card_summary(narrative, action, pilar_scores)


# ═══════════════════════════════════════════════════════
# KARTU INDIVIDUAL 9 PILAR
# ═══════════════════════════════════════════════════════

def _card_business(scores: dict, company_name: str) -> None:
    """Pilar 01 — Profitabilitas (Net Profit Margin)."""
    data = scores.get("profitabilitas", {})
    npm = data.get("value", 0)
    avg_npm = data.get("avg_npm", npm)
    trend = data.get("trend", "")
    passed = data.get("pass_fail", False)

    total = len(scores)
    passed_count = sum(1 for v in scores.values() if v.get("pass_fail", False))

    badge_text = "HEALTHY" if passed_count >= 6 else ("MODERATE" if passed_count >= 4 else "WEAK")
    badge_color = "vi-badge-pass" if passed_count >= 6 else ("vi-badge-warn" if passed_count >= 4 else "vi-badge-fail")
    trend_html = f'<div style="font-size:0.62rem;color:#C682B3;margin-top:2px;">{trend}</div>' if trend else ""

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">01</span>
                <span class="icon">{_ICON['business']}</span>
                <span class="label">Business</span>
            </div>
            <span class="vi-badge {'vi-badge-pass' if passed else 'vi-badge-fail'}">{'PASS' if passed else 'FAIL'}</span>
        </div>
        <div style="font-weight:600;color:#FFFFFF;font-size:0.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            {company_name.upper() if company_name else 'N/A'}
        </div>
        <hr class="vi-divider">
        <div class="vi-card-desc">
            NPM Terkini: <span style="color:#FFFFFF;font-weight:500;">{format_percent(npm)}</span>
            <span style="opacity:0.65;font-size:0.62rem;">(Avg: {format_percent(avg_npm)})</span>
            {trend_html}
        </div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Score: <span style="color:#FFFFFF;font-weight:600;">{passed_count}/{total}</span></span>
            <span class="vi-badge {badge_color}">{badge_text}</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_revenue(scores: dict, income_df: pd.DataFrame) -> None:
    """Pilar 02 — Revenue Growth YoY."""
    data = scores.get("revenue_growth", {})
    growth = data.get("value", 0)
    consistency = data.get("consistency_ratio", 0)
    growth_years = data.get("growth_years", [])
    passed = data.get("pass_fail", False)

    rev_col = _find_col(income_df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    bar_svg = ""
    rev_latest = 0

    if rev_col and len(income_df) >= 2:
        revs = income_df[rev_col].astype(float).tolist()
        rev_latest = revs[-1]
        n = len(revs)

        if growth_years and len(growth_years) >= n:
            years = growth_years[-n:]
        else:
            year_col = _find_col(income_df, ["year", "Year", "fiscal_year"])
            if year_col and len(income_df[year_col]) == n:
                years = [str(int(y)) if str(y).replace('.','').isdigit() else str(y) for y in income_df[year_col]]
            else:
                curr_y = datetime.now().year
                years = [str(curr_y - n + 1 + i) for i in range(n)]

        bar_svg = svg_bar_chart(revs[-5:], labels=years[-5:], width=145, height=52, color="#C682B3")

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    rev_text = format_rupiah_short(rev_latest) if rev_latest else "N/A"
    cons_text = f"Konsisten {consistency*100:.0f}%" if consistency > 0 else "YoY Growth"

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">02</span>
                <span class="icon">{_ICON['revenue']}</span>
                <span class="label">Revenue</span>
            </div>
            <span class="vi-card-value">{rev_text} <span style="font-size:0.58rem;opacity:0.6;">TTM</span></span>
        </div>
        <div class="vi-card-chart">{bar_svg}</div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">{cons_text}</span>
            <span class="vi-badge {badge_cls}">{format_percent(growth)}</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_profit(scores: dict, income_df: pd.DataFrame) -> None:
    """Pilar 03 — Profit Growth YoY."""
    data = scores.get("profit_growth", {})
    growth = data.get("value", 0)
    consistency = data.get("consistency_ratio", 0)
    passed = data.get("pass_fail", False)

    npm_data = scores.get("profitabilitas", {})
    npm = npm_data.get("value", 0)

    prof_col = _find_col(income_df, ["earnings", "net_income", "netIncome", "net_profit", "Net Income"])
    sparkline = ""
    prof_latest = 0

    if prof_col and len(income_df) >= 2:
        profs = income_df[prof_col].astype(float).tolist()
        prof_latest = profs[-1]
        sparkline = svg_sparkline(profs[-5:], width=145, height=42, color="#69B37A", fill=True)

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    cons_info = f" • Positif {consistency*100:.0f}%" if consistency > 0 else ""

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">03</span>
                <span class="icon">{_ICON['profit']}</span>
                <span class="label">Profit</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.58rem;color:#8E8E9C;text-transform:uppercase;letter-spacing:0.04em;">Net Profit</div>
                <div class="vi-card-big-value" style="font-size:0.92rem;">{format_rupiah_short(prof_latest)}</div>
            </div>
        </div>
        <div class="vi-card-chart">{sparkline}</div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Margin {format_percent(npm)}{cons_info}</span>
            <span class="vi-badge {badge_cls}">{format_percent(growth)}</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_cashflow(scores: dict, cashflow_df: pd.DataFrame) -> None:
    """Pilar 04 — Cash Flow Growth YoY."""
    data = scores.get("cashflow_growth", {})
    growth = data.get("value", 0)
    passed = data.get("pass_fail", False)
    metric = data.get("metric_used", "FCF")

    cf_col = _find_col(cashflow_df, [
        "free_cash_flow", "freeCashFlow", "operating_cash_flow",
        "operatingCashFlow", "cash_from_operations",
    ]) if cashflow_df is not None and not cashflow_df.empty else None

    sparkline = ""
    cf_latest = 0
    if cf_col:
        cfs = cashflow_df[cf_col].astype(float).tolist()
        cf_latest = cfs[-1]
        sparkline = svg_sparkline(cfs[-5:], width=145, height=42, color="#C682B3", fill=True)

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    rating_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    rating = "HEALTHY" if passed else "WEAK"

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">04</span>
                <span class="icon">{_ICON['cashflow']}</span>
                <span class="label">Cash Flow</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.58rem;color:#8E8E9C;text-transform:uppercase;letter-spacing:0.04em;">{metric}</div>
                <div class="vi-card-big-value" style="font-size:0.92rem;">{format_rupiah_short(cf_latest)}</div>
            </div>
        </div>
        <div class="vi-card-chart">{sparkline}</div>
        <div class="vi-card-footer">
            <span class="vi-badge {rating_cls}">{rating}</span>
            <span class="vi-badge {badge_cls}">{format_percent(growth)}</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_roic_roe(scores: dict) -> None:
    """Pilar 05 — ROIC / ROE (Warren Buffett Benchmark)."""
    data = scores.get("roic_roe", {})
    roe_val = data.get("roe", 0.0)
    roic_val = data.get("roic", 0.0)
    passed = data.get("pass_fail", False)
    leverage_warn = data.get("leverage_warning", False)

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    badge_text = "PASS" if passed else "BELOW"

    roe_bar = min(100, max(0, abs(roe_val) * 100 * 3.33))
    roic_bar = min(100, max(0, abs(roic_val) * 100 * 3.33))
    roe_color = "#69B37A" if roe_val >= 0.15 else "#FF5E5E"
    roic_color = "#69B37A" if roic_val >= 0.10 else "#FF5E5E"

    warn_html = '<div style="font-size:0.58rem;color:#FFD600;margin-top:2px;">⚠️ ROE tinggi via leverage hutang</div>' if leverage_warn else ""

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">05</span>
                <span class="icon">{_ICON['target']}</span>
                <span class="label">ROIC / ROE</span>
            </div>
            <span class="vi-badge {badge_cls}">{badge_text}</span>
        </div>
        <div style="margin-top:4px;">
            <div style="margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">
                    <span style="font-size:0.62rem;color:#9E9EAA;text-transform:uppercase;letter-spacing:0.04em;">ROE (Target &ge; 15%)</span>
                    <span style="font-size:0.88rem;font-weight:600;color:{roe_color};">{format_percent(roe_val)}</span>
                </div>
                <div class="vi-progress-track">
                    <div class="vi-progress-fill" style="width:{roe_bar:.1f}%;background:{roe_color};"></div>
                </div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">
                    <span style="font-size:0.62rem;color:#9E9EAA;text-transform:uppercase;letter-spacing:0.04em;">ROIC (Target &gt; 10%)</span>
                    <span style="font-size:0.88rem;font-weight:600;color:{roic_color};">{format_percent(roic_val)}</span>
                </div>
                <div class="vi-progress-track">
                    <div class="vi-progress-fill" style="width:{roic_bar:.1f}%;background:{roic_color};"></div>
                </div>
            </div>
            {warn_html}
        </div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Standar Warren Buffett</span>
            <span class="vi-card-desc" style="opacity:0.8;">Moat Kuat</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_debt(scores: dict) -> None:
    """Pilar 06 — Debt Health (D/E, D/A, & ICR atau Metrik Bank)."""
    data = scores.get("debt_health", {})
    is_bank = data.get("is_bank", False)
    de = data.get("de_ratio", data.get("value", 0))
    da = data.get("da_ratio", 0)
    icr = data.get("interest_coverage", 0)
    passed = data.get("pass_fail", False)
    risk = data.get("risk_label", "LOW RISK" if passed else "HIGH RISK")

    risk_cls = "vi-badge-pass" if "LOW" in risk else ("vi-badge-warn" if "MEDIUM" in risk else "vi-badge-fail")
    icr_text = f"{icr:.1f}x" if icr < 100 else ">100x"

    if is_bank:
        lev = data.get("financial_leverage", de)
        ldr = data.get("ldr")
        car = data.get("car")

        stat1_val = f"{lev:.2f}x"
        stat1_lbl = "LEVERAGE (L/E)"

        stat2_val = f"{ldr:.1f}%" if ldr is not None else f"{da:.2f}"
        stat2_lbl = "LDR (KREDIT/DPK)" if ldr is not None else "L/A"

        stat3_val = f"{car:.1f}%" if car is not None else icr_text
        stat3_lbl = "CAR (MODAL)" if car is not None else "ICR"

        footer_left = "Batas: Leverage &lt; 8.0x"
        footer_right = "LDR 75–92% • CAR &gt; 12%"
    else:
        stat1_val = f"{de:.2f}"
        stat1_lbl = "D/E"
        stat2_val = f"{da:.2f}"
        stat2_lbl = "D/A"
        stat3_val = icr_text
        stat3_lbl = "ICR"
        footer_left = "Batas Aman: D/E &lt; 1.0x"
        footer_right = "ICR &gt; 3.0x"

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">06</span>
                <span class="icon">{_ICON['debt']}</span>
                <span class="label">Debt Health</span>
            </div>
            <span class="vi-badge {risk_cls}">{risk}</span>
        </div>
        <div class="vi-stats-row">
            <div class="vi-stat">
                <div class="vi-stat-val">{stat1_val}</div>
                <div class="vi-stat-label">{stat1_lbl}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);align-self:stretch;"></div>
            <div class="vi-stat">
                <div class="vi-stat-val">{stat2_val}</div>
                <div class="vi-stat-label">{stat2_lbl}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);align-self:stretch;"></div>
            <div class="vi-stat">
                <div class="vi-stat-val">{stat3_val}</div>
                <div class="vi-stat-label">{stat3_lbl}</div>
            </div>
        </div>
        <div class="vi-card-desc" style="text-align:center;opacity:0.85;">
            {data.get("interpretasi", "")}
        </div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">{footer_left}</span>
            <span class="vi-card-desc">{footer_right}</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_growth(scores: dict, income_df: pd.DataFrame) -> None:
    """Pilar 07 — Growth CAGR (Multi-Metric)."""
    cagr_data = scores.get("growth_cagr", {})
    cagr = cagr_data.get("value", 0)
    cagr_profit = cagr_data.get("cagr_profit", 0)
    n_years = cagr_data.get("years_count", 5)
    passed = cagr_data.get("pass_fail", False)

    rev_data = scores.get("revenue_growth", {})
    detail = rev_data.get("detail", [])
    growth_years = rev_data.get("growth_years", [])
    bar_svg = ""
    if detail and len(detail) >= 2:
        if growth_years and len(growth_years) >= len(detail):
            labels = growth_years[-len(detail[-5:]):]
        else:
            curr_y = datetime.now().year
            k = len(detail[-5:])
            labels = [str(curr_y - k + 1 + i) for i in range(k)]
        bar_svg = svg_bar_chart(detail[-5:], labels=labels, width=145, height=52, color="#69B37A")

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    start_y = cagr_data.get("start_year")
    end_y = cagr_data.get("end_year")
    cagr_header = f"{start_y}–{end_y}" if start_y and end_y else f"{n_years} Thn"

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">07</span>
                <span class="icon">{_ICON['growth']}</span>
                <span class="label">Growth CAGR</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.58rem;color:#8E8E9C;text-transform:uppercase;letter-spacing:0.04em;">{cagr_header}</div>
                <div style="font-size:0.86rem;font-weight:600;color:#FFFFFF;">{format_percent(cagr)}</div>
            </div>
        </div>
        <div class="vi-card-chart">{bar_svg}</div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Profit CAGR: <span style="color:#FFFFFF;font-weight:500;">{format_percent(cagr_profit)}</span></span>
            <span class="vi-badge {badge_cls}">{"GROWING" if passed else "SLOW"}</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_valuation(scores: dict, company_report: dict, current_price: float = 0.0) -> None:
    """Pilar 08 — Valuation (P/E, P/B & Intrinsic Value)."""
    iv_data = scores.get("intrinsic_value", {})
    iv = iv_data.get("intrinsic_value", iv_data.get("value", 0))

    mos_data = scores.get("margin_of_safety", {})
    mos = mos_data.get("value", 0)
    passed = iv_data.get("pass_fail", False)

    pe, pb = 0.0, 0.0
    try:
        valuation = company_report.get("valuation", {}) if isinstance(company_report, dict) else {}
        hist = valuation.get("historical_valuation", [])

        # Di v2, historical_valuation adalah list of dicts per tahun
        if isinstance(hist, list) and len(hist) > 0:
            latest = hist[-1]
            pe = float(latest.get("pe") or latest.get("pe_ratio") or 0.0)
            pb = float(latest.get("pb") or latest.get("pb_ratio") or 0.0)
        elif isinstance(hist, dict):
            pe = float(hist.get("pe") or hist.get("pe_ratio") or 0.0)
            pb = float(hist.get("pb") or hist.get("pb_ratio") or 0.0)

        # Fallback 1: forward_pe jika pe masih <= 0
        if pe <= 0:
            pe = float(valuation.get("forward_pe") or 0.0)

        # Fallback 2: kalkulasi langsung dari current_price, EPS, dan BVPS
        if (pe <= 0 or pb <= 0) and isinstance(company_report, dict):
            price = current_price or float(valuation.get("last_close_price") or 0.0)
            fin = company_report.get("financials", {})
            if pe <= 0:
                eps = float(fin.get("eps") or 0.0)
                if eps > 0 and price > 0:
                    pe = price / eps
            if pb <= 0:
                h_fin = fin.get("historical_financials", [])
                if isinstance(h_fin, list) and len(h_fin) > 0:
                    last_h = h_fin[-1]
                    eq = float(last_h.get("total_equity") or 0.0)
                    shs = float(last_h.get("outstanding_shares") or 0.0)
                    if eq > 0 and shs > 0 and price > 0:
                        bvps = eq / shs
                        pb = price / bvps
    except Exception:
        pass

    badge_cls = "vi-badge-pass" if passed else "vi-badge-warn"
    badge_text = "UNDERVALUED" if mos >= 0.25 else ("FAIR VALUE" if mos > 0 else "OVERVALUED")

    pe_display = f"{pe:.1f}" if pe > 0 else "N/A"
    pb_display = f"{pb:.1f}" if pb > 0 else "N/A"

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">08</span>
                <span class="icon">{_ICON['diamond']}</span>
                <span class="label">Valuation</span>
            </div>
            <span class="vi-badge {badge_cls}">{badge_text}</span>
        </div>
        <div class="vi-stats-row">
            <div class="vi-stat">
                <div class="vi-stat-val">{pe_display}<span style="font-size:0.65rem;color:#8E8E9C;">x</span></div>
                <div class="vi-stat-label">P/E</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);align-self:stretch;"></div>
            <div class="vi-stat">
                <div class="vi-stat-val">{pb_display}<span style="font-size:0.65rem;color:#8E8E9C;">x</span></div>
                <div class="vi-stat-label">P/B</div>
            </div>
        </div>
        <div class="vi-card-desc" style="text-align:center;">
            Nilai Intrinsik: <span style="color:#FFFFFF;font-weight:600;">{format_rupiah_short(iv)}</span>
        </div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Model Dua Tahap DCF</span>
            <span class="vi-card-desc" style="opacity:0.8;">EV &rarr; Equity</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_margin_of_safety(scores: dict, current_price: float) -> None:
    """Pilar 09 — Margin of Safety (Benjamin Graham)."""
    data = scores.get("margin_of_safety", {})
    mos = data.get("value", 0)
    iv = data.get("intrinsic_value", 0)

    if mos >= 0.25:
        gauge_color = "#69B37A"
        mos_badge_cls = "vi-badge-pass"
        mos_badge_text = "SAFE (&ge;25%)"
    elif mos > 0:
        gauge_color = "#FFD600"
        mos_badge_cls = "vi-badge-warn"
        mos_badge_text = "FAIR (0-25%)"
    else:
        gauge_color = "#FF5E5E"
        mos_badge_cls = "vi-badge-fail"
        mos_badge_text = "EXPENSIVE"

    pct_display = f"{mos*100:+.1f}%"
    fill_deg = min(360, max(0, abs(mos) * 360))

    html = f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="vi-pillar-num">09</span>
                <span class="icon">{_ICON['shield']}</span>
                <span class="label">Margin of Safety</span>
            </div>
            <span class="vi-badge {mos_badge_cls}">{mos_badge_text}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:center;margin:2px 0;">
            <div style="
                width:58px;height:58px;
                border-radius:50%;
                background:conic-gradient({gauge_color} {fill_deg:.1f}deg, rgba(255,255,255,0.05) 0deg);
                display:flex;align-items:center;justify-content:center;
            ">
                <div style="
                    width:44px;height:44px;
                    border-radius:50%;
                    background:#1B1B20;
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.68rem;font-weight:600;color:{gauge_color};
                    letter-spacing:-0.01em;
                ">{pct_display}</div>
            </div>
        </div>
        <div class="vi-stats-row">
            <div class="vi-stat">
                <div class="vi-stat-val" style="font-size:0.8rem;">{format_rupiah_short(current_price)}</div>
                <div class="vi-stat-label">Market Price</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);align-self:stretch;"></div>
            <div class="vi-stat">
                <div class="vi-stat-val" style="font-size:0.8rem;">{format_rupiah_short(iv)}</div>
                <div class="vi-stat-label">Intrinsic</div>
            </div>
        </div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Standar Benjamin Graham</span>
            <span class="vi-card-desc" style="opacity:0.8;">Diskon Aman</span>
        </div>
    </div>
    """
    _render_html(html)


def _card_summary(narrative: str, action: str, scores: dict) -> None:
    """Kartu besar Summary / narasi analis di kolom kanan (Fixed Height)."""
    total = len(scores)
    passed = sum(1 for v in scores.values() if v.get("pass_fail", False))

    action_color = "#69B37A" if action in ("Buy", "Hold") else ("#FFD600" if action == "Watch" else "#FF5E5E")

    narrative_html = narrative.replace("\n\n", "<br><br>").replace("\n", "<br>")
    narrative_html = narrative_html.replace("**", "")

    if action == "Buy":
        action_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
    elif action == "Hold":
        action_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>'
    else:
        action_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></svg>'

    html = f"""
    <div class="vi-card-tall">
        <div>
            <div class="vi-card-head">
                <div class="vi-card-title">
                    <span class="icon">{_ICON['summary']}</span>
                    <span class="label">Summary Analis</span>
                </div>
                <span style="display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;font-weight:600;color:{action_color};background:rgba(255,255,255,0.04);padding:3px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.08);">
                    {action_icon} {action}
                </span>
            </div>
            <hr class="vi-divider">
        </div>
        <div class="vi-summary-scroll">
            <div class="vi-summary-text">{narrative_html}</div>
        </div>
        <div>
            <hr class="vi-divider">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
                <span style="font-size:0.68rem;color:#8E8E9C;">Skor Fundamental</span>
                <span style="font-size:0.85rem;font-weight:600;color:#FFFFFF;">{passed}<span style="color:#8E8E9C;font-weight:400;">/{total} LULUS</span></span>
            </div>
            <div class="vi-progress-track" style="margin-top:6px;">
                <div class="vi-progress-fill" style="width:{(passed/max(total,1))*100:.1f}%;background:#C682B3;"></div>
            </div>
            <div style="margin-top:12px; font-size:0.65rem; color:#8E8E9C; font-style:italic; text-align:center; line-height:1.3;">
                ⚠️ Ini bukan rekomendasi untuk membeli atau menjual saham. Lakukan riset lebih lanjut sebelum mengambil keputusan investasi.
            </div>
        </div>
    </div>
    """
    _render_html(html)


# ═══════════════════════════════════════════════════════
# HELPER INTERNAL
# ═══════════════════════════════════════════════════════

def _find_col(df: pd.DataFrame | None, candidates: list[str]) -> str | None:
    """Cari kolom yang cocok (case-insensitive)."""
    if df is None or df.empty:
        return None
    cols_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None
