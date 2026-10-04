"""
app.py — Entry point Value Investing Dashboard (Maximos).

Single-page layout tanpa sidebar. Orkestrasi:
    1. Load .env
    2. Render ticker input (autocomplete) & parameter DCF di atas halaman
    3. Fetch data dari Sectors API v2
    4. Hitung 9 pilar value investing secara komprehensif
    5. Render header harga + nama perusahaan + sektor
    6. Generate narasi analis AI (dengan fallback otomatis)
    7. Render grid kartu scorecard 9 pilar
    8. Render grafik interaktif Plotly (Historical vs Intrinsic & DCF Projection)
"""

from datetime import datetime
import os
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.sectors_service import (
    get_company_report, get_financial_statements, get_historical_price,
)
from src.services.llm_service import generate_narrative, fallback_narrative
from src.engine.engine import (
    calculate_profitability, calculate_revenue_growth_yoy,
    calculate_profit_growth_yoy, calculate_cashflow_growth_yoy, calculate_cagr,
    calculate_roe, calculate_roic, calculate_debt_health,
    calculate_dcf, project_future_value_recurrence, calculate_margin_of_safety,
    _find_column,
)
from src.ui.sidebar import render_ticker_input
from src.ui.scorecard import render_scorecard
from src.ui.charts import plot_historical_vs_intrinsic, plot_future_projection
from src.utils.formatter import format_rupiah, format_rupiah_short

st.set_page_config(
    page_title="Maximos",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* ── Reset: hide Streamlit chrome ── */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Typography ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #131315 !important;
        color: #FFFFFF !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* ── Background ── */
    .stApp, .stApp > div {
        background-color: #131315 !important;
    }

    /* ── Layout spacing ── */
    .stColumn > div { padding: 0 0.25rem !important; }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* ════════════════════════════════════════════════
       HEADER TOP BAR — clean, minimal
       ════════════════════════════════════════════════ */
    .top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #222226;
        border-radius: 10px;
        padding: 0.85rem 1.5rem;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255,255,255,0.04);
        transition: border-color 0.25s ease;
    }
    .top-header:hover {
        border-color: rgba(198,130,179,0.12);
    }
    .header-ticker {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .ticker-badge {
        background: rgba(198,130,179,0.08);
        border: 1px solid rgba(198,130,179,0.2);
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #C682B3;
        letter-spacing: 0.06em;
    }
    .header-company-name {
        font-size: 0.95rem;
        font-weight: 500;
        color: #FFFFFF;
        letter-spacing: 0.01em;
    }
    .header-sub {
        font-size: 0.65rem;
        color: #999999;
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .header-price-block {
        text-align: right;
    }
    .header-price-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    .header-price-label {
        font-size: 0.62rem;
        color: #999999;
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .price-change-up {
        font-size: 0.72rem;
        font-weight: 500;
        color: #69B37A;
        background: rgba(105,179,122,0.08);
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 8px;
    }
    .price-change-down {
        font-size: 0.72rem;
        font-weight: 500;
        color: #FF5252;
        background: rgba(255,82,82,0.08);
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 8px;
    }

    /* ── Divider ── */
    .section-line {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.04);
        margin: 1.2rem 0;
    }

    /* ════════════════════════════════════════════════
       BUTTON — flat accent, no gradient
       ════════════════════════════════════════════════ */
    .stButton > button[kind="primary"] {
        background: #C682B3 !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em !important;
        border-radius: 8px !important;
        height: 42px !important;
        font-size: 0.78rem !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #d494c4 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background: #222226 !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        transition: border-color 0.2s ease !important;
    }
    .stSelectbox > div > div:focus-within {
        border-color: rgba(198,130,179,0.3) !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: #18181D !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        margin-bottom: 1.2rem !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }
    .streamlit-expanderHeader {
        background: #1E1E24 !important;
        border-radius: 8px !important;
        color: #E2E2EA !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    .streamlit-expanderHeader:hover {
        color: #FFFFFF !important;
        border-color: rgba(198, 130, 179, 0.3) !important;
    }

    /* ════════════════════════════════════════════════
       SLIDER — High Contrast & Clear Value Popups
       ════════════════════════════════════════════════ */
    .stSlider {
        padding: 0.4rem 0.2rem !important;
    }
    .stSlider [data-testid="stWidgetLabel"] p {
        color: #D6D6E0 !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
    }
    
    /* Inactive Track */
    .stSlider [data-baseweb="slider"] > div {
        background: #2D2D38 !important;
        height: 6px !important;
        border-radius: 4px !important;
    }
    
    /* Active Track (Filled) */
    .stSlider [data-baseweb="slider"] > div > div:first-child {
        background: #C682B3 !important;
        height: 6px !important;
        border-radius: 4px !important;
    }
    
    /* Thumb Handle */
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background: #FFFFFF !important;
        border: 3px solid #C682B3 !important;
        width: 18px !important;
        height: 18px !important;
        top: calc(50% - 9px) !important;
        box-shadow: 0 0 10px rgba(198, 130, 179, 0.6) !important;
        transition: transform 0.15s ease !important;
    }
    .stSlider [data-baseweb="slider"] div[role="slider"]:hover {
        transform: scale(1.15) !important;
    }
    
    /* Thumb Value Popup / Tooltip (Angka Persentase) */
    .stSlider div[data-testid="stSliderThumbValue"],
    .stSlider [data-baseweb="slider"] div[role="slider"] ~ div,
    .stSlider [data-baseweb="slider"] div[data-testid="stSliderThumbValue"] {
        background: #141418 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #C682B3 !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        padding: 2px 7px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7) !important;
    }
    .stSlider div[data-testid="stSliderThumbValue"] *,
    .stSlider [data-baseweb="slider"] div[role="slider"] ~ div * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        background: transparent !important;
    }
    
    /* Slider Min & Max text */
    .stSlider [data-testid="stSliderTickBarMin"],
    .stSlider [data-testid="stSliderTickBarMax"] {
        color: #8A8A96 !important;
        font-size: 0.68rem !important;
        font-weight: 500 !important;
    }

    /* ── Global transitions ── */
    * {
        transition-timing-function: ease;
    }

    /* ════════════════════════════════════════════════
       SCORECARD & SUMMARY CARD STYLING (9 Pillars Grid)
       ════════════════════════════════════════════════ */
    .vi-card {
        background: #1B1B20 !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-top: 2.5px solid rgba(198, 130, 179, 0.45) !important;
        border-radius: 12px !important;
        padding: 1rem 1.15rem !important;
        margin-bottom: 0.85rem !important;
        position: relative !important;
        overflow: hidden !important;
        height: 220px !important;
        min-height: 220px !important;
        max-height: 220px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.25s ease !important;
        box-sizing: border-box !important;
    }
    .vi-card:hover {
        border-color: rgba(198, 130, 179, 0.55) !important;
        border-top-color: #C682B3 !important;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.55), 0 0 1px rgba(198, 130, 179, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    .vi-card-head {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        margin-bottom: 0.4rem !important;
    }
    .vi-card-title {
        display: flex !important;
        align-items: center !important;
        gap: 7px !important;
    }
    .vi-pillar-num {
        font-size: 0.62rem !important;
        font-weight: 700 !important;
        color: #C682B3 !important;
        background: rgba(198, 130, 179, 0.12) !important;
        border: 1px solid rgba(198, 130, 179, 0.3) !important;
        padding: 1px 5px !important;
        border-radius: 4px !important;
        letter-spacing: 0.04em !important;
    }
    .vi-card-title .icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 24px !important;
        height: 24px !important;
        border-radius: 6px !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }
    .vi-card-title .label {
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        color: #E2E2EA !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
    }
    .vi-card-value {
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        color: #A4A4B2 !important;
    }
    .vi-card-big-value {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        margin-bottom: 2px !important;
        letter-spacing: -0.01em !important;
    }
    .vi-card-desc {
        font-size: 0.68rem !important;
        color: #9A9AA6 !important;
        line-height: 1.45 !important;
    }
    .vi-card-footer {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding-top: 0.5rem !important;
        border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
        margin-top: auto !important;
    }
    .vi-card-chart {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 2px 0 !important;
        flex: 1 !important;
    }
    .vi-badge {
        display: inline-flex !important;
        align-items: center !important;
        padding: 2px 8px !important;
        border-radius: 4px !important;
        font-size: 0.62rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        line-height: 1.3 !important;
    }
    .vi-badge-pass {
        background: rgba(105, 179, 122, 0.16) !important;
        color: #69B37A !important;
        border: 1px solid rgba(105, 179, 122, 0.35) !important;
    }
    .vi-badge-fail {
        background: rgba(255, 94, 94, 0.16) !important;
        color: #FF5E5E !important;
        border: 1px solid rgba(255, 94, 94, 0.35) !important;
    }
    .vi-badge-warn {
        background: rgba(255, 214, 0, 0.16) !important;
        color: #FFD600 !important;
        border: 1px solid rgba(255, 214, 0, 0.35) !important;
    }
    .vi-stats-row {
        display: flex !important;
        align-items: center !important;
        justify-content: space-around !important;
        padding: 0.25rem 0 !important;
    }
    .vi-stat {
        text-align: center !important;
        flex: 1 !important;
    }
    .vi-stat-val {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.01em !important;
    }
    .vi-stat-label {
        font-size: 0.58rem !important;
        color: #8E8E9C !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-top: 2px !important;
    }
    .vi-card-tall {
        background: #1B1B20 !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-top: 2.5px solid #C682B3 !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        margin-bottom: 0.85rem !important;
        position: relative !important;
        overflow: hidden !important;
        height: 686px !important;
        min-height: 686px !important;
        max-height: 686px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.25s ease !important;
        box-sizing: border-box !important;
    }
    .vi-card-tall:hover {
        border-color: rgba(198, 130, 179, 0.55) !important;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.55) !important;
    }
    .vi-summary-scroll {
        overflow-y: auto !important;
        padding-right: 6px !important;
        flex: 1 !important;
        margin: 10px 0 !important;
    }
    .vi-summary-scroll::-webkit-scrollbar {
        width: 4px !important;
    }
    .vi-summary-scroll::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.18) !important;
        border-radius: 4px !important;
    }
    .vi-summary-text {
        font-size: 0.73rem !important;
        color: #B4B4C2 !important;
        line-height: 1.65 !important;
    }
    .vi-divider {
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
        margin: 6px 0 !important;
    }
    .vi-progress-track {
        background: rgba(255, 255, 255, 0.06) !important;
        border-radius: 2px !important;
        height: 4px !important;
        overflow: hidden !important;
    }
    .vi-progress-fill {
        height: 100% !important;
        border-radius: 2px !important;
        transition: width 0.4s ease !important;
    }
</style>
""", unsafe_allow_html=True)



def main() -> None:
    """Fungsi utama orkestrasi dashboard."""
    params = render_ticker_input()
    ticker = params["ticker"]
    company_name = params["company_name"]
    discount_rate = params["discount_rate"]
    growth_rate = params["growth_rate"]
    terminal_growth = params.get("terminal_growth", 0.03)
    projection_years = params.get("projection_years", 5)

    if not params.get("analyze", False):
        return

    if not ticker:
        st.error("Silakan pilih kode saham terlebih dahulu.")
        return

    with st.spinner(f"Mengambil data {ticker} dari Sectors API..."):
        try:
            company_report = get_company_report(ticker)
            financial_data = get_financial_statements(ticker)
            price_history = get_historical_price(ticker)
        except (ConnectionError, ValueError) as e:
            st.error(f"Gagal mengambil data: {e}")
            st.stop()
            return

    income_df = financial_data.get("income_statement")
    balance_df = financial_data.get("balance_sheet")
    cashflow_df = financial_data.get("cash_flow")

    if income_df is None or income_df.empty:
        st.error("Data laporan keuangan tidak tersedia untuk ticker ini.")
        st.stop()
        return

    sector = ""
    try:
        sector = (
            company_report.get("sector", "")
            or company_report.get("overview", {}).get("sector", "")
        )
    except (AttributeError, TypeError):
        sector = ""

    current_price = _get_current_price(price_history)
    price_change_pct = _get_price_change(price_history)

    pilar_scores = _evaluate_all_pillars(
        income_df=income_df,
        balance_df=balance_df,
        cashflow_df=cashflow_df,
        company_report=company_report,
        discount_rate=discount_rate,
        growth_rate=growth_rate,
        terminal_growth=terminal_growth,
        projection_years=projection_years,
        current_price=current_price,
        sector=sector,
    )

    api_name = ""
    try:
        api_name = (
            company_report.get("company_name", "")
            or company_report.get("overview", {}).get("company_name", "")
        )
    except (AttributeError, TypeError):
        pass
    display_name = api_name if api_name else company_name

    change_cls = "price-change-up" if price_change_pct >= 0 else "price-change-down"
    change_sign = "+" if price_change_pct >= 0 else ""

    st.markdown(f"""
    <div class="top-header">
        <div class="header-ticker">
            <span class="ticker-badge">{ticker}</span>
            <div>
                <div class="header-company-name">{display_name}</div>
                <div class="header-sub">{sector if sector else 'IDX &bull; Fundamental Analysis'}</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:1.5rem;">
            <div style="text-align:center;">
                <div style="font-size:0.58rem; color:#999999; text-transform:uppercase; letter-spacing:0.05em;">Updated</div>
                <div style="font-size:0.78rem; color:#FFFFFF; font-weight:500;">{datetime.now().strftime("%b %Y")}</div>
            </div>
            <div style="width:1px;height:28px;background:rgba(255,255,255,0.06);"></div>
            <div class="header-price-block">
                <div style="display:flex; align-items:baseline; justify-content:flex-end; gap:6px;">
                    <span class="header-price-value">{format_rupiah(current_price)}</span>
                    <span class="{change_cls}">{change_sign}{price_change_pct*100:.2f}%</span>
                </div>
                <div class="header-price-label">Current Market Price</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    narrative = ""
    action = "Hold"
    try:
        narrative = generate_narrative(pilar_scores)
        passed_count = sum(1 for v in pilar_scores.values() if v.get("pass_fail", False))
        if passed_count >= 7:
            action = "Buy"
        elif passed_count >= 5:
            action = "Hold"
        else:
            action = "Avoid"
    except Exception:
        result = fallback_narrative(pilar_scores)
        if isinstance(result, tuple):
            narrative, action = result
        else:
            narrative = result

    render_scorecard(
        pilar_scores=pilar_scores,
        income_df=income_df,
        balance_df=balance_df,
        cashflow_df=cashflow_df,
        company_report=company_report,
        current_price=current_price,
        price_change_pct=price_change_pct,
        narrative=narrative,
        action=action,
        company_name=display_name,
    )

    iv = pilar_scores.get("intrinsic_value", {}).get("intrinsic_value", 0.0)
    with st.expander("📈 Grafik Interaktif: Pergerakan Harga vs Nilai Intrinsik & Proyeksi FCF", expanded=False):
        c_left, c_right = st.columns(2)
        with c_left:
            plot_historical_vs_intrinsic(price_history, iv)
        with c_right:
            dcf_data = pilar_scores.get("intrinsic_value", {})
            proj_fcfs = dcf_data.get("projected_fcf", [])
            proj_years = dcf_data.get("projected_years", [])
            if proj_fcfs:
                if proj_years and len(proj_years) == len(proj_fcfs):
                    proj_data = [{"year": str(y), "value": val} for y, val in zip(proj_years, proj_fcfs)]
                else:
                    curr_y = datetime.now().year
                    proj_data = [{"year": str(curr_y + 1 + i), "value": val} for i, val in enumerate(proj_fcfs)]
                plot_future_projection(
                    proj_data,
                    label=f"Proyeksi Free Cash Flow ({proj_data[0]['year']}–{proj_data[-1]['year']})",
                )
            else:
                st.info("Proyeksi arus kas masa depan tidak tersedia.")

def _evaluate_all_pillars(
    income_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    cashflow_df: pd.DataFrame,
    company_report: dict,
    discount_rate: float,
    growth_rate: float,
    terminal_growth: float,
    projection_years: int,
    current_price: float,
    sector: str,
) -> dict:
    """Evaluasi seluruh 9 pilar value investing secara menyeluruh & adaptif sektor."""
    scores = {}

    scores["profitabilitas"] = calculate_profitability(income_df, sector=sector)
    scores["revenue_growth"] = calculate_revenue_growth_yoy(income_df, sector=sector)
    scores["profit_growth"] = calculate_profit_growth_yoy(income_df, sector=sector)

    if cashflow_df is not None and not cashflow_df.empty:
        scores["cashflow_growth"] = calculate_cashflow_growth_yoy(cashflow_df, sector=sector)
    else:
        scores["cashflow_growth"] = {
            "value": 0.0, "consistency_ratio": 0.0, "avg_growth": 0.0,
            "metric_used": "N/A", "trend": "N/A", "detail": [], "growth_years": [],
            "pass_fail": False, "threshold": "> 0% (Konsisten >=60%)",
        }

    is_bank = "financial" in sector.lower() or "bank" in sector.lower()
    if balance_df is not None and not balance_df.empty:
        roe = calculate_roe(income_df, balance_df, sector=sector)
        roic = calculate_roic(income_df, balance_df, sector=sector)

        if is_bank:
            passed = roe["pass_fail"]
            threshold_label = "ROE >= 15% (Bank)"
        else:
            passed = roe["pass_fail"] and roic["pass_fail"]
            threshold_label = "ROE >= 15%, ROIC > 10%"

        scores["roic_roe"] = {
            "value": roe["value"],
            "roe": roe["value"],
            "roic": roic["value"],
            "avg_roe": roe.get("avg_roe", roe["value"]),
            "avg_roic": roic.get("avg_roic", roic["value"]),
            "leverage_multiplier": roe.get("leverage_multiplier", 1.0),
            "leverage_warning": roe.get("leverage_warning", False),
            "pass_fail": passed,
            "threshold": threshold_label,
        }
    else:
        scores["roic_roe"] = {
            "value": 0.0, "roe": 0.0, "roic": 0.0,
            "pass_fail": False, "threshold": "ROE >= 15%, ROIC > 10%",
        }

    if balance_df is not None and not balance_df.empty:
        scores["debt_health"] = calculate_debt_health(balance_df, income_df=income_df, sector=sector)
    else:
        scores["debt_health"] = {
            "value": 0.0, "de_ratio": 0.0, "da_ratio": 0.0, "interest_coverage": 0.0,
            "pass_fail": False, "threshold": "< 1.0x", "interpretasi": "Data tidak tersedia",
        }

    scores["growth_cagr"] = calculate_cagr(income_df, column_hint="revenue", sector=sector)

    fcf_list = _extract_fcf(cashflow_df)
    shares = _extract_shares(company_report)

    base_year = datetime.now().year
    if "year" in income_df.columns and len(income_df["year"]) > 0:
        try:
            base_year = int(income_df["year"].iloc[-1])
        except (ValueError, TypeError):
            pass

    total_debt = 0.0
    cash_and_equivalents = 0.0
    if balance_df is not None and not balance_df.empty:
        debt_col = _find_column(balance_df, ["total_debt", "totalDebt", "long_term_debt"])
        if debt_col:
            total_debt = float(pd.to_numeric(balance_df[debt_col].iloc[-1], errors="coerce") or 0.0)
        cash_col = _find_column(balance_df, ["cash_and_equivalents", "cashAndEquivalents", "cash_only", "cash", "total_cash_and_due_from_banks"])
        if cash_col:
            cash_and_equivalents = float(pd.to_numeric(balance_df[cash_col].iloc[-1], errors="coerce") or 0.0)

    scores["intrinsic_value"] = calculate_dcf(
        free_cash_flows=fcf_list,
        discount_rate=discount_rate,
        growth_rate=growth_rate,
        terminal_growth=terminal_growth,
        shares_outstanding=shares,
        projection_years=projection_years,
        current_price=current_price,
        total_debt=total_debt,
        cash_and_equivalents=cash_and_equivalents,
        base_year=base_year,
        is_bank=is_bank,
    )

    iv = scores["intrinsic_value"].get("intrinsic_value", 0.0)
    scores["margin_of_safety"] = calculate_margin_of_safety(iv, current_price, sector=sector)

    return scores


def _extract_fcf(cashflow_df: pd.DataFrame | None) -> list[float]:
    """
    Ekstrak Free Cash Flow dari DataFrame (v2: flat historical_financials).
    Memprioritaskan free_cash_flow murni, atau menghitung OCF - CapEx jika tersedia.
    """
    if cashflow_df is None or cashflow_df.empty:
        return []

    cols_lower = {c.lower(): c for c in cashflow_df.columns}

    for name in ["free_cash_flow", "freecashflow"]:
        if name in cols_lower:
            series = pd.to_numeric(cashflow_df[cols_lower[name]], errors="coerce").dropna()
            if not series.empty:
                return series.tolist()

    ocf_col = None
    for name in ["operating_cash_flow", "operatingcashflow", "cash_from_operations"]:
        if name in cols_lower:
            ocf_col = cols_lower[name]
            break

    capex_col = None
    for name in ["realized_capital_goods_investment", "capex", "capital_expenditure"]:
        if name in cols_lower:
            capex_col = cols_lower[name]
            break

    if ocf_col and capex_col:
        ocf_s = pd.to_numeric(cashflow_df[ocf_col], errors="coerce").fillna(0.0)
        capex_s = pd.to_numeric(cashflow_df[capex_col], errors="coerce").fillna(0.0).abs()
        fcf_calc = (ocf_s - capex_s).tolist()
        if fcf_calc:
            return fcf_calc

    if ocf_col:
        series = pd.to_numeric(cashflow_df[ocf_col], errors="coerce").dropna()
        return series.tolist()

    return []


def _extract_shares(report: dict) -> float | None:
    """Ekstrak jumlah saham beredar dari company report v2."""
    try:
        hist = report.get("financials", {}).get("historical_financials", [])
        if hist:
            for row in reversed(hist):
                val = row.get("outstanding_shares")
                if val:
                    return float(val)
        overview = report.get("overview", {})
        for f in ["shares_outstanding", "outstanding_shares", "total_shares"]:
            v = overview.get(f)
            if v:
                return float(v)
    except (TypeError, ValueError):
        pass
    return None


def _get_current_price(price_history: pd.DataFrame | None) -> float:
    """Ambil harga penutupan terakhir."""
    if price_history is None or price_history.empty:
        return 0.0
    if "close" in price_history.columns:
        return float(price_history["close"].iloc[-1])
    return 0.0


def _get_price_change(price_history: pd.DataFrame | None) -> float:
    """Hitung perubahan harga penutupan terakhir (persentase)."""
    if price_history is None or price_history.empty or len(price_history) < 2:
        return 0.0
    if "close" in price_history.columns:
        current = float(price_history["close"].iloc[-1])
        previous = float(price_history["close"].iloc[-2])
        if previous != 0:
            return (current - previous) / previous
    return 0.0


if __name__ == "__main__":
    main()
else:
    main()
