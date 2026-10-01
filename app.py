"""
app.py — Entry point Value Investing Dashboard.

Single-page layout tanpa sidebar. Orkestrasi:
    1. Load .env
    2. Render ticker input (autocomplete) di atas halaman
    3. Fetch data dari Sectors API
    4. Hitung 10 pilar value investing
    5. Render header harga + nama perusahaan
    6. Render grid kartu scorecard
    7. Render grafik interaktif Plotly
    8. Generate narasi AI (dengan fallback otomatis)
"""

import os
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ── Load .env sebelum import modul lain ──
load_dotenv()

# ── sys.path agar bisa import src.* ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.sectors_service import (
    get_company_report, get_financial_statements, get_historical_price,
)
from src.services.llm_service import generate_narrative, fallback_narrative
from src.engine.growth import (
    calculate_profitability, calculate_revenue_growth_yoy,
    calculate_profit_growth_yoy, calculate_cashflow_growth_yoy, calculate_cagr,
)
from src.engine.health import (
    calculate_roe, calculate_roic, calculate_debt_health, calculate_management_efficiency,
)
from src.engine.valuation import (
    calculate_dcf, project_future_value_recurrence, calculate_margin_of_safety,
)
from src.ui.sidebar import render_ticker_input
from src.ui.scorecard import render_scorecard
from src.ui.charts import plot_historical_vs_intrinsic, plot_future_projection
from src.utils.formatter import format_rupiah, format_rupiah_short

# ════════════════════════════════════════════════════════
# Page Config — single page, no sidebar
# ════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Value Investing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──
st.markdown("""
<style>
    /* Sembunyikan sidebar, header, footer default */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Reduce spacing antar kolom Streamlit */
    .stColumn > div { padding: 0 0.25rem !important; }

    /* Kurangi padding atas */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }

    /* Header price section */
    .price-header {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin: 0.3rem 0 0.2rem 0;
    }
    .price-value {
        font-size: 2rem;
        font-weight: 700;
        color: #e8eaed;
        font-family: 'Inter', sans-serif;
    }
    .price-change-up {
        font-size: 0.95rem;
        font-weight: 600;
        color: #00E676;
        background: rgba(0,230,118,0.1);
        padding: 2px 10px;
        border-radius: 6px;
    }
    .price-change-down {
        font-size: 0.95rem;
        font-weight: 600;
        color: #FF5252;
        background: rgba(255,82,82,0.1);
        padding: 2px 10px;
        border-radius: 6px;
    }
    .price-label {
        font-size: 0.78rem;
        color: #8892b0;
        margin-top: 2px;
    }
    .company-name {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 1.6rem;
        font-weight: 600;
        color: #c8cdd8;
        text-align: right;
    }
    .meta-info {
        font-size: 0.7rem;
        color: #5a6272;
        text-align: center;
        margin-top: 2px;
    }
    .section-line {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin: 1rem 0;
    }
    /* Tombol ANALYSIS styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a1d2e, #252840) !important;
        border: 1px solid rgba(68,138,255,0.3) !important;
        color: #448AFF !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        border-radius: 8px !important;
        height: 42px !important;
    }
    .stButton > button[kind="primary"]:hover {
        border-color: #448AFF !important;
        background: linear-gradient(135deg, #1e2136, #2a2d4a) !important;
    }
</style>
""", unsafe_allow_html=True)


def main() -> None:
    """Fungsi utama orkestrasi dashboard."""

    # ── Ticker Input (atas halaman, tanpa sidebar) ──
    params = render_ticker_input()
    ticker = params["ticker"]
    company_name = params["company_name"]
    discount_rate = params["discount_rate"]
    growth_rate = params["growth_rate"]
    projection_years = params["projection_years"]

    if not params.get("analyze", False):
        # Tampilan awal sebelum analisis
        st.markdown("""
        <div style="text-align:center; padding:4rem 2rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
            <div style="font-size:1.3rem; font-weight:600; color:#c8cdd8;">
                Value Investing Dashboard
            </div>
            <div style="font-size:0.85rem; color:#8892b0; margin-top:0.5rem;">
                Pilih saham dan klik <b>ANALYSIS</b> untuk memulai analisis 10 pilar value investing
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    if not ticker:
        st.error("⚠️ Silakan pilih kode saham terlebih dahulu.")
        return

    # ══════════════════════════════════════════════════
    # STEP 1: Fetch Data dari Sectors API
    # ══════════════════════════════════════════════════
    with st.spinner(f"Mengambil data {ticker} dari Sectors API..."):
        try:
            company_report = get_company_report(ticker)
            financial_data = get_financial_statements(ticker)
            price_history = get_historical_price(ticker)
        except (ConnectionError, ValueError) as e:
            st.error(f"❌ Gagal mengambil data: {e}")
            st.stop()
            return

    income_df = financial_data.get("income_statement")
    balance_df = financial_data.get("balance_sheet")
    cashflow_df = financial_data.get("cash_flow")

    if income_df is None or income_df.empty:
        st.error("❌ Data income statement tidak tersedia untuk ticker ini.")
        st.stop()
        return

    # ══════════════════════════════════════════════════
    # STEP 2: Hitung 10 Pilar
    # ══════════════════════════════════════════════════
    pilar_scores = _evaluate_all_pillars(
        income_df, balance_df, cashflow_df, company_report,
        discount_rate, growth_rate, price_history,
    )

    # ══════════════════════════════════════════════════
    # STEP 3: Header — Harga + Nama Perusahaan
    # ══════════════════════════════════════════════════
    current_price = _get_current_price(price_history)
    price_change_pct = _get_price_change(price_history)

    col_price, col_meta, col_name = st.columns([3, 3, 3])

    with col_price:
        change_cls = "price-change-up" if price_change_pct >= 0 else "price-change-down"
        change_sign = "+" if price_change_pct >= 0 else ""
        change_arrow = "↗" if price_change_pct >= 0 else "↘"
        st.markdown(f"""
        <div class="price-header">
            <span class="price-value">{format_rupiah(current_price)}</span>
            <span class="{change_cls}">{change_arrow} {change_sign}{price_change_pct*100:.1f}%</span>
        </div>
        <div class="price-label">Current Price</div>
        """, unsafe_allow_html=True)

    with col_meta:
        from datetime import datetime
        st.markdown(f"""
        <div class="meta-info" style="margin-top:12px;">
            Last Updated: {datetime.now().strftime("%B %Y")}<br>
            Data Source: Sectors API
        </div>
        """, unsafe_allow_html=True)

    with col_name:
        # v2: company_name ada di root response, fallback ke daftar lokal
        api_name = ""
        try:
            api_name = (
                company_report.get("company_name", "")
                or company_report.get("overview", {}).get("company_name", "")
            )
        except (AttributeError, TypeError):
            pass
        display_name = api_name if api_name else company_name
        st.markdown(f'<div class="company-name">{display_name}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="section-line">', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # STEP 4: Narasi AI (hitung dulu, tampilkan di kartu)
    # ══════════════════════════════════════════════════
    narrative = ""
    action = "Hold"
    try:
        narrative = generate_narrative(pilar_scores)
        # Tentukan action dari jumlah pilar lulus
        passed_count = sum(1 for v in pilar_scores.values() if v.get("pass_fail", False))
        if passed_count >= 8:
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

    # ══════════════════════════════════════════════════
    # STEP 5: Render Scorecard Grid
    # ══════════════════════════════════════════════════
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
        company_name=company_name,
    )

    # ══════════════════════════════════════════════════
    # STEP 6: Grafik Plotly (di bawah kartu)
    # ══════════════════════════════════════════════════
    st.markdown('<hr class="section-line">', unsafe_allow_html=True)

    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        iv = pilar_scores.get("intrinsic_value", {}).get("intrinsic_value", 0)
        plot_historical_vs_intrinsic(price_history, iv)

    with chart_c2:
        projected = project_future_value_recurrence(
            initial_value=current_price if current_price > 0 else 1000,
            growth_rate=growth_rate,
            periods=projection_years,
        )
        plot_future_projection(projected, label="Proyeksi Future Value (Relasi Rekurensi)")

    # Footer
    st.markdown("""
    <div style="text-align:center;margin-top:2rem;padding:1rem;">
        <span style="font-size:0.7rem;color:#5a6272;">
            Value Investing Dashboard — Data dari Sectors API — Bukan rekomendasi investasi
        </span>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def _evaluate_all_pillars(
    income_df, balance_df, cashflow_df, company_report,
    discount_rate, growth_rate, price_history,
) -> dict:
    """Evaluasi seluruh 10 pilar value investing."""
    scores = {}

    # 1. Profitabilitas
    scores["profitabilitas"] = calculate_profitability(income_df)

    # 2. Revenue Growth
    scores["revenue_growth"] = calculate_revenue_growth_yoy(income_df)

    # 3. Profit Growth
    scores["profit_growth"] = calculate_profit_growth_yoy(income_df)

    # 4. Cash Flow Growth
    if cashflow_df is not None and not cashflow_df.empty:
        scores["cashflow_growth"] = calculate_cashflow_growth_yoy(cashflow_df)
    else:
        scores["cashflow_growth"] = {"value": 0.0, "pass_fail": False, "threshold": "> 0%"}

    # 5. ROIC / ROE
    if balance_df is not None and not balance_df.empty:
        roe = calculate_roe(income_df, balance_df)
        roic = calculate_roic(income_df, balance_df)
        best = max(roe["value"], roic["value"])
        scores["roic_roe"] = {
            "value": best, "roe": roe["value"], "roic": roic["value"],
            "pass_fail": roe["pass_fail"] or roic["pass_fail"],
            "threshold": "> 10%",
        }
    else:
        scores["roic_roe"] = {"value": 0.0, "roe": 0.0, "roic": 0.0,
                               "pass_fail": False, "threshold": "> 10%"}

    # 6. Debt Health
    if balance_df is not None and not balance_df.empty:
        scores["debt_health"] = calculate_debt_health(balance_df)
    else:
        scores["debt_health"] = {"value": 0.0, "de_ratio": 0.0, "da_ratio": 0.0,
                                  "pass_fail": False, "threshold": "< 1.0"}

    # 7. Growth CAGR
    scores["growth_cagr"] = calculate_cagr(income_df, column_hint="revenue")

    # 8. Efisiensi Manajemen
    if balance_df is not None and not balance_df.empty:
        scores["efisiensi_manajemen"] = calculate_management_efficiency(income_df, balance_df)
    else:
        scores["efisiensi_manajemen"] = {"value": 0.0, "pass_fail": False,
                                          "threshold": "> 0.5", "margin_trend_positive": False}

    # 9. Intrinsic Value (DCF)
    fcf_list = _extract_fcf(cashflow_df)
    shares = _extract_shares(company_report)
    scores["intrinsic_value"] = calculate_dcf(
        free_cash_flows=fcf_list, discount_rate=discount_rate,
        growth_rate=growth_rate, terminal_growth=0.03, shares_outstanding=shares,
    )

    # 10. Margin of Safety
    current_price = _get_current_price(price_history)
    iv = scores["intrinsic_value"].get("intrinsic_value", 0)
    scores["margin_of_safety"] = calculate_margin_of_safety(iv, current_price)

    return scores


def _extract_fcf(cashflow_df) -> list[float]:
    """Ekstrak Free Cash Flow dari DataFrame (v2: flat historical_financials)."""
    if cashflow_df is None or cashflow_df.empty:
        return []
    # v2 field names diutamakan
    for name in ["free_cash_flow", "operating_cash_flow", "freeCashFlow",
                  "operatingCashFlow", "cash_from_operations"]:
        col_map = {c.lower(): c for c in cashflow_df.columns}
        if name.lower() in col_map:
            series = pd.to_numeric(cashflow_df[col_map[name.lower()]], errors="coerce").dropna()
            return series.tolist()
    return []


def _extract_shares(report: dict) -> float | None:
    """Ekstrak jumlah saham beredar dari company report v2."""
    try:
        # v2: outstanding_shares ada di financials.historical_financials (ambil yang terbaru)
        hist = report.get("financials", {}).get("historical_financials", [])
        if hist:
            # ambil entri terbaru yang punya outstanding_shares
            for row in reversed(hist):
                val = row.get("outstanding_shares")
                if val:
                    return float(val)
        # Fallback: cari di overview (kadang ada di key_stats versi lama)
        overview = report.get("overview", {})
        for f in ["shares_outstanding", "outstanding_shares", "total_shares"]:
            v = overview.get(f)
            if v:
                return float(v)
    except (TypeError, ValueError):
        pass
    return None


def _get_current_price(price_history) -> float:
    """Ambil harga penutupan terakhir."""
    if price_history is None or price_history.empty:
        return 0.0
    if "close" in price_history.columns:
        return float(price_history["close"].iloc[-1])
    return 0.0


def _get_price_change(price_history) -> float:
    """Hitung perubahan harga terakhir (persentase)."""
    if price_history is None or price_history.empty or len(price_history) < 2:
        return 0.0
    if "close" in price_history.columns:
        current = float(price_history["close"].iloc[-1])
        previous = float(price_history["close"].iloc[-2])
        if previous != 0:
            return (current - previous) / previous
    return 0.0


# ── Entry Point ──
if __name__ == "__main__":
    main()
else:
    main()
