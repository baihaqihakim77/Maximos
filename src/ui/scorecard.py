"""
scorecard.py — Grid visual 10 pilar value investing dalam kartu dashboard.

Layout mengikuti desain referensi:
    Left (3×3 grid): Business, Revenue, Profit, CashFlow, ROIC/ROE, Debt,
                      Growth, Management, Valuation
    Right (stacked):  Margin of Safety (gauge) + Summary (narasi)
"""

import pandas as pd
import streamlit as st

from src.ui.charts import svg_sparkline, svg_bar_chart, svg_gauge, svg_dual_gauge
from src.utils.formatter import format_rupiah_short, format_percent


# ═══════════════════════════════════════════════════════
# CSS untuk kartu dashboard
# ═══════════════════════════════════════════════════════

_CARD_CSS = """
<style>
.vi-card {
    background: #222226;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.6rem;
    position: relative;
    overflow: hidden;
    min-height: 170px;
}
.vi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(198,130,179,0.35), transparent);
}
.vi-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
}
.vi-card-title {
    display: flex;
    align-items: center;
    gap: 6px;
}
.vi-card-title .icon { font-size: 1.1rem; }
.vi-card-title .label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: 0.03em;
}
.vi-card-value {
    font-size: 0.75rem;
    font-weight: 500;
    color: #999999;
}
.vi-card-big-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 2px;
}
.vi-card-desc {
    font-size: 0.7rem;
    color: #999999;
    line-height: 1.45;
    margin-top: 4px;
}
.vi-card-chart {
    margin: 6px 0;
    display: flex;
    justify-content: center;
}
.vi-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.vi-badge-pass {
    background: rgba(105,179,122,0.15);
    color: #69B37A;
    border: 1px solid rgba(105,179,122,0.2);
}
.vi-badge-fail {
    background: rgba(255,82,82,0.12);
    color: #FF5E5E;
    border: 1px solid rgba(255,82,82,0.15);
}
.vi-badge-warn {
    background: rgba(255,214,0,0.10);
    color: #FFD600;
    border: 1px solid rgba(255,214,0,0.15);
}
.vi-badge-info {
    background: rgba(198,130,179,0.12);
    color: #C682B3;
    border: 1px solid rgba(198,130,179,0.2);
}
.vi-stats-row {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 6px;
}
.vi-stat {
    text-align: center;
}
.vi-stat-val {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
}
.vi-stat-label {
    font-size: 0.62rem;
    color: #999999;
    margin-top: 1px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.vi-card-footer {
    margin-top: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
/* Kartu besar untuk MoS dan Summary */
.vi-card-tall {
    background: #222226;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 14px;
    padding: 1.2rem;
    margin-bottom: 0.6rem;
    position: relative;
    overflow: hidden;
}
.vi-card-tall::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(198,130,179,0.4), transparent);
}
.vi-summary-text {
    font-size: 0.72rem;
    color: #999999;
    line-height: 1.6;
    margin-top: 8px;
}
.vi-summary-action {
    font-size: 0.8rem;
    font-weight: 700;
    color: #C682B3;
    margin-top: 10px;
}
</style>
"""

_CSS_INJECTED = False


def _inject_css() -> None:
    """Inject CSS sekali saja."""
    global _CSS_INJECTED
    if not _CSS_INJECTED:
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        _CSS_INJECTED = True


# ═══════════════════════════════════════════════════════
# FUNGSI UTAMA
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
    Tampilkan grid dashboard 10 pilar dalam layout kartu.

    Layout:
        Left 3×3: Business, Revenue, Profit, CashFlow, ROIC/ROE, Debt,
                   Growth, Management, Valuation
        Right:     Margin of Safety + Summary
    """
    _inject_css()

    # === Main layout: left grid (3×3) + right column (Summary) ===
    main_left, main_right = st.columns([3, 1.2])

    with main_left:
        # Row 1: Business | Revenue | Profit
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            _card_business(pilar_scores, company_name)
        with r1c2:
            _card_revenue(pilar_scores, income_df)
        with r1c3:
            _card_profit(pilar_scores, income_df)

        # Row 2: Cash Flow | ROIC/ROE | Debt
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            _card_cashflow(pilar_scores, cashflow_df)
        with r2c2:
            _card_roic_roe(pilar_scores)
        with r2c3:
            _card_debt(pilar_scores)

        # Row 3: Growth | Valuation | Margin of Safety
        r3c1, r3c2, r3c3 = st.columns(3)
        with r3c1:
            _card_growth(pilar_scores, income_df)
        with r3c2:
            _card_valuation(pilar_scores, company_report)
        with r3c3:
            _card_margin_of_safety(pilar_scores, current_price)

    with main_right:
        _card_summary(narrative, action, pilar_scores)



# ═══════════════════════════════════════════════════════
# KARTU INDIVIDUAL
# ═══════════════════════════════════════════════════════

def _card_business(scores: dict, company_name: str) -> None:
    """Kartu Business / Profitabilitas."""
    data = scores.get("profitabilitas", {})
    npm = data.get("value", 0)
    passed = data.get("pass_fail", False)
    total = len(scores)
    passed_count = sum(1 for v in scores.values() if v.get("pass_fail", False))

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    badge_text = "HEALTHY" if passed_count >= 6 else ("MODERATE" if passed_count >= 4 else "WEAK")
    badge_color = "vi-badge-pass" if passed_count >= 6 else ("vi-badge-warn" if passed_count >= 4 else "vi-badge-fail")

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">🏢</span>
                <span class="label">Business</span>
            </div>
        </div>
        <div class="vi-card-desc" style="font-weight:600;color:#FFFFFF;font-size:0.76rem;">
            {company_name.upper() if company_name else 'N/A'}
        </div>
        <div class="vi-card-desc">
            Profit Margin: {format_percent(npm)}<br>
            Diversified portfolio.
        </div>
        <div class="vi-card-footer" style="margin-top:12px;">
            <span class="vi-card-desc">Rating: <b style="color:#FFFFFF;">{passed_count}/{total}</b></span>
            <span class="vi-badge {badge_color}">{badge_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_revenue(scores: dict, income_df: pd.DataFrame) -> None:
    """Kartu Revenue Growth."""
    data = scores.get("revenue_growth", {})
    growth = data.get("value", 0)
    passed = data.get("pass_fail", False)

    # Ambil data revenue historis untuk bar chart
    rev_col = _find_col(income_df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    bar_svg = ""
    rev_latest = 0
    if rev_col and len(income_df) >= 2:
        revs = income_df[rev_col].astype(float).tolist()
        rev_latest = revs[-1]
        n = len(revs)
        years = [str(2024 - n + 1 + i) for i in range(n)]
        bar_svg = svg_bar_chart(revs[-5:], labels=years[-5:], width=150, height=60, color="#C682B3")

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    rev_text = format_rupiah_short(rev_latest) if rev_latest else "N/A"

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">💰</span>
                <span class="label">Revenue</span>
            </div>
            <span class="vi-card-value">{rev_text} <span style="font-size:0.6rem;">(TTM)</span></span>
        </div>
        <div class="vi-card-chart">{bar_svg}</div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">YoY Growth</span>
            <span class="vi-badge {badge_cls}">{format_percent(growth)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_profit(scores: dict, income_df: pd.DataFrame) -> None:
    """Kartu Profit Growth."""
    data = scores.get("profit_growth", {})
    growth = data.get("value", 0)
    passed = data.get("pass_fail", False)

    npm_data = scores.get("profitabilitas", {})
    npm = npm_data.get("value", 0)

    prof_col = _find_col(income_df, ["net_income", "netIncome", "net_profit", "Net Income"])
    sparkline = ""
    prof_latest = 0
    if prof_col and len(income_df) >= 2:
        profs = income_df[prof_col].astype(float).tolist()
        prof_latest = profs[-1]
        sparkline = svg_sparkline(profs[-5:], width=150, height=45, color="#69B37A", fill=True)

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">📊</span>
                <span class="label">Profit</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.65rem;color:#8892b0;">Net Profit</div>
                <div class="vi-card-big-value" style="font-size:0.95rem;">{format_rupiah_short(prof_latest)}</div>
            </div>
        </div>
        <div class="vi-card-chart">{sparkline}</div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Profit Margin ({format_percent(npm)})</span>
            <span class="vi-badge {badge_cls}">{format_percent(growth)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_cashflow(scores: dict, cashflow_df: pd.DataFrame) -> None:
    """Kartu Cash Flow Growth."""
    data = scores.get("cashflow_growth", {})
    growth = data.get("value", 0)
    passed = data.get("pass_fail", False)

    cf_col = _find_col(cashflow_df, [
        "free_cash_flow", "freeCashFlow", "operating_cash_flow",
        "operatingCashFlow", "cash_from_operations",
    ]) if cashflow_df is not None and not cashflow_df.empty else None

    sparkline = ""
    cf_latest = 0
    if cf_col:
        cfs = cashflow_df[cf_col].astype(float).tolist()
        cf_latest = cfs[-1]
        sparkline = svg_sparkline(cfs[-5:], width=150, height=45, color="#C682B3", fill=True)

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    rating_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    rating = "HEALTHY" if passed else "WEAK"

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">💵</span>
                <span class="label">Cash Flow</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.65rem;color:#8892b0;">FCF</div>
                <div class="vi-card-big-value" style="font-size:0.95rem;">{format_rupiah_short(cf_latest)}</div>
            </div>
        </div>
        <div class="vi-card-chart">{sparkline}</div>
        <div class="vi-card-footer">
            <span class="vi-badge {rating_cls}">{rating}</span>
            <span class="vi-badge {badge_cls}">{format_percent(growth)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_roic_roe(scores: dict) -> None:
    """Kartu ROIC / ROE — CSS-only, tanpa SVG."""
    data = scores.get("roic_roe", {})
    roe_val = data.get("roe", data.get("value", 0))
    roic_val = data.get("roic", data.get("value", 0) * 0.85)
    passed = data.get("pass_fail", False)

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"
    badge_text = "LULUS" if passed else "PERLU PERHATIAN"

    # Progress bar width (cap at 100%)
    roe_bar = min(100, abs(roe_val) * 100 * 3)   # scale: 33% ROE = full bar
    roic_bar = min(100, abs(roic_val) * 100 * 3)
    roe_color = "#69B37A" if roe_val >= 0.10 else "#FF5E5E"
    roic_color = "#69B37A" if roic_val >= 0.10 else "#FF5E5E"

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">🎯</span>
                <span class="label">ROIC / ROE</span>
            </div>
            <span class="vi-badge {badge_cls}">{badge_text}</span>
        </div>
        <div style="margin-top:14px;">
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
                    <span style="font-size:0.65rem;color:#999999;text-transform:uppercase;letter-spacing:0.04em;">ROE</span>
                    <span style="font-size:1rem;font-weight:700;color:{roe_color};">{format_percent(roe_val)}</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:3px;height:5px;">
                    <div style="width:{roe_bar:.1f}%;height:100%;border-radius:3px;background:{roe_color};"></div>
                </div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
                    <span style="font-size:0.65rem;color:#999999;text-transform:uppercase;letter-spacing:0.04em;">ROIC</span>
                    <span style="font-size:1rem;font-weight:700;color:{roic_color};">{format_percent(roic_val)}</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:3px;height:5px;">
                    <div style="width:{roic_bar:.1f}%;height:100%;border-radius:3px;background:{roic_color};"></div>
                </div>
            </div>
        </div>
        <div class="vi-card-desc" style="margin-top:10px;">
            Ideal: ROE &amp; ROIC &gt; 10%
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_debt(scores: dict) -> None:
    """Kartu Debt Health."""
    data = scores.get("debt_health", {})
    de = data.get("de_ratio", data.get("value", 0))
    da = data.get("da_ratio", 0)
    passed = data.get("pass_fail", False)
    risk = data.get("risk_label", "LOW RISK" if passed else "HIGH RISK")

    risk_cls = "vi-badge-pass" if "LOW" in risk else ("vi-badge-warn" if "MEDIUM" in risk else "vi-badge-fail")

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">⚖️</span>
                <span class="label">Debt</span>
            </div>
            <span class="vi-badge {risk_cls}">{risk}</span>
        </div>
        <div class="vi-stats-row" style="margin-top:18px;">
            <div class="vi-stat">
                <div class="vi-stat-val">{de:.2f}</div>
                <div class="vi-stat-label">Debt/Equity</div>
            </div>
            <div class="vi-stat">
                <div class="vi-stat-val">{da:.2f}</div>
                <div class="vi-stat-label">Debt/Assets</div>
            </div>
        </div>
        <div class="vi-card-desc" style="text-align:center;margin-top:12px;">
            {data.get("interpretasi", "")}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_growth(scores: dict, income_df: pd.DataFrame) -> None:
    """Kartu Growth CAGR."""
    cagr_data = scores.get("growth_cagr", {})
    cagr = cagr_data.get("value", 0)
    passed = cagr_data.get("pass_fail", False)

    profit_data = scores.get("profit_growth", {})
    profit_growth = profit_data.get("value", 0)

    # Bar chart multi-tahun (growth detail)
    rev_data = scores.get("revenue_growth", {})
    detail = rev_data.get("detail", [])
    bar_svg = ""
    if detail and len(detail) >= 2:
        labels = [f"{i+1}yr" for i in range(len(detail[-5:]))]
        bar_svg = svg_bar_chart(detail[-5:], labels=labels, width=150, height=55, color="#69B37A")

    badge_cls = "vi-badge-pass" if passed else "vi-badge-fail"

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">📈</span>
                <span class="label">Growth</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.65rem;color:#8892b0;">5yr CAGR: <b style="color:#e8eaed;">{format_percent(cagr)}</b></div>
                <div style="font-size:0.65rem;color:#8892b0;">Net Profit: <b style="color:#e8eaed;">{format_percent(profit_growth)}</b></div>
            </div>
        </div>
        <div class="vi-card-chart">{bar_svg}</div>
        <div class="vi-card-footer">
            <span class="vi-card-desc">Growth Rate</span>
            <span class="vi-badge {badge_cls}">{"GROWING" if passed else "SLOW"}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def _card_valuation(scores: dict, company_report: dict) -> None:
    """Kartu Valuation / Intrinsic Value."""
    iv_data = scores.get("intrinsic_value", {})
    iv = iv_data.get("intrinsic_value", iv_data.get("value", 0))

    mos_data = scores.get("margin_of_safety", {})
    mos = mos_data.get("value", 0)
    passed = mos_data.get("pass_fail", False)

    # Coba ambil P/E dan P/B dari company report
    pe, pb = 0, 0
    try:
        valuation = company_report.get("valuation", {})
        hist = valuation.get("historical_valuation", {})
        pe = hist.get("pe_ratio", hist.get("pe", 0)) or 0
        pb = hist.get("pb_ratio", hist.get("pb", 0)) or 0
    except (AttributeError, TypeError):
        pass

    badge_cls = "vi-badge-pass" if passed else "vi-badge-warn"
    badge_text = "UNDERVALUED" if mos > 0.25 else ("FAIR VALUE" if mos > 0 else "OVERVALUED")

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">💎</span>
                <span class="label">Valuation</span>
            </div>
        </div>
        <div class="vi-stats-row" style="margin-top:8px;">
            <div class="vi-stat">
                <div class="vi-stat-val">{pe:.1f}x</div>
                <div class="vi-stat-label">P/E</div>
            </div>
            <div class="vi-stat">
                <div class="vi-stat-val">{pb:.1f}x</div>
                <div class="vi-stat-label">P/B</div>
            </div>
        </div>
        <div class="vi-card-desc" style="text-align:center;margin-top:8px;">
            Intrinsic Value: <b style="color:#FFFFFF;">{format_rupiah_short(iv)}</b>
        </div>
        <div style="text-align:center;margin-top:10px;">
            <span class="vi-badge {badge_cls}">{badge_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_margin_of_safety(scores: dict, current_price: float) -> None:
    """Kartu Margin of Safety — CSS conic-gradient, tanpa SVG."""
    data = scores.get("margin_of_safety", {})
    mos = data.get("value", 0)
    iv = data.get("intrinsic_value", 0)

    if mos > 0.25:
        gauge_color = "#69B37A"
    elif mos > 0:
        gauge_color = "#FFD600"
    else:
        gauge_color = "#FF5E5E"

    mos_badge_cls = "vi-badge-pass" if mos > 0.25 else ("vi-badge-warn" if mos > 0 else "vi-badge-fail")
    mos_badge_text = "AMAN" if mos > 0.25 else ("CUKUP" if mos > 0 else "MAHAL")

    pct_display = f"{abs(mos)*100:.1f}%"
    # CSS conic-gradient donut: fill proportional to MoS (cap at 100%)
    fill_deg = min(360, abs(mos) * 360)

    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">🛡️</span>
                <span class="label">Margin of Safety</span>
            </div>
            <span class="vi-badge {mos_badge_cls}">{mos_badge_text}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:center;margin:10px 0;">
            <div style="
                width:72px;height:72px;
                border-radius:50%;
                background:conic-gradient({gauge_color} {fill_deg:.1f}deg, rgba(255,255,255,0.06) 0deg);
                display:flex;align-items:center;justify-content:center;
            ">
                <div style="
                    width:52px;height:52px;
                    border-radius:50%;
                    background:#222226;
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.72rem;font-weight:700;color:{gauge_color};
                ">{pct_display}</div>
            </div>
        </div>
        <div class="vi-stats-row" style="margin-top:4px;">
            <div class="vi-stat">
                <div class="vi-stat-val" style="font-size:0.82rem;">{format_rupiah_short(current_price)}</div>
                <div class="vi-stat-label">Harga</div>
            </div>
            <div class="vi-stat">
                <div class="vi-stat-val" style="font-size:0.82rem;">{format_rupiah_short(iv)}</div>
                <div class="vi-stat-label">Intrinsic</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_summary(narrative: str, action: str, scores: dict) -> None:
    """Kartu besar Summary / narasi AI."""
    total = len(scores)
    passed = sum(1 for v in scores.values() if v.get("pass_fail", False))

    # Warna action
    action_color = "#69B37A" if action in ("Hold", "Buy") else ("#FFD600" if action == "Watch" else "#FF5E5E")

    # Bersihkan markdown formatting untuk HTML
    narrative_html = narrative.replace("\n\n", "<br><br>").replace("\n", "<br>")
    narrative_html = narrative_html.replace("**", "")

    st.markdown(f"""
    <div class="vi-card-tall" style="min-height:300px;">
        <div class="vi-card-head">
            <div class="vi-card-title">
                <span class="icon">📋</span>
                <span class="label">Summary</span>
            </div>
            <span style="font-size:0.78rem;font-weight:700;color:{action_color};">
                Action: {action}
            </span>
        </div>
        <div class="vi-summary-text">{narrative_html}</div>
        <div class="vi-summary-action" style="color:{action_color};margin-top:14px;">
            Score: {passed}/{total} — Action: <span style="color:#C682B3;">{action}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# HELPER
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
