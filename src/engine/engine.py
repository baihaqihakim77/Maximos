"""
engine.py — Mesin kalkulasi fundamental value investing.

Menggabungkan semua perhitungan 9 pilar:
  1. Profitabilitas (Net Profit Margin)
  2. Revenue Growth YoY
  3. Profit Growth YoY
  4. Cash Flow Growth YoY
  5. ROE (Return on Equity)
  6. ROIC (Return on Invested Capital)
  7. Debt Health (D/E & D/A)
  8. Growth CAGR
  9. Intrinsic Value via DCF + Margin of Safety
"""

import numpy as np
import pandas as pd


# ═══════════════════════════════════════════════════════
# HELPERS INTERNAL
# ═══════════════════════════════════════════════════════

def _safe_float(value) -> float:
    """Konversi nilai ke float, kembalikan 0.0 jika None/NaN/tidak valid."""
    try:
        if value is None:
            return 0.0
        f = float(value)
        return 0.0 if (np.isnan(f) or np.isinf(f)) else f
    except (TypeError, ValueError):
        return 0.0


def _safe_series_float(series: pd.Series) -> pd.Series:
    """Konversi series ke float dengan aman, replace None/NaN → 0.0."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Cari nama kolom yang cocok (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


def _yoy_growth(df: pd.DataFrame, col: str) -> tuple[float, list[float]]:
    """Helper: hitung YoY growth untuk satu kolom, return (latest, [growths])."""
    values = _safe_series_float(df[col]).values
    growths = []
    for i in range(1, len(values)):
        if values[i - 1] != 0:
            growths.append((values[i] - values[i - 1]) / abs(values[i - 1]))
        else:
            growths.append(0.0)
    latest = growths[-1] if growths else 0.0
    return latest, growths


# ═══════════════════════════════════════════════════════
# PILAR 1 — PROFITABILITAS
# ═══════════════════════════════════════════════════════

def calculate_profitability(df: pd.DataFrame) -> dict:
    """
    Evaluasi profitabilitas — Net Profit Margin.

    Rumus: NPM = Net Income / Revenue
    Threshold LULUS: > 5%
    """
    rev_col = _find_column(df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    profit_col = _find_column(df, ["earnings", "net_income", "netIncome", "net_profit", "Net Income"])

    if rev_col is None or profit_col is None or len(df) < 1:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 5%"}

    revenue = _safe_float(df[rev_col].iloc[-1])
    profit = _safe_float(df[profit_col].iloc[-1])

    if revenue == 0:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 5%"}

    npm = profit / revenue
    return {"value": npm, "pass_fail": npm > 0.05, "threshold": "> 5%"}


# ═══════════════════════════════════════════════════════
# PILAR 2 — REVENUE GROWTH YoY
# ═══════════════════════════════════════════════════════

def calculate_revenue_growth_yoy(df: pd.DataFrame) -> dict:
    """
    Hitung pertumbuhan pendapatan Year-over-Year.

    Rumus: Revenue Growth YoY = (Revenue[t] - Revenue[t-1]) / Revenue[t-1]
    Threshold LULUS: > 0%
    """
    rev_col = _find_column(df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    if rev_col is None or len(df) < 2:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 0%", "detail": []}

    latest, growths = _yoy_growth(df, rev_col)
    return {"value": latest, "pass_fail": latest > 0, "threshold": "> 0%", "detail": growths}


# ═══════════════════════════════════════════════════════
# PILAR 3 — PROFIT GROWTH YoY
# ═══════════════════════════════════════════════════════

def calculate_profit_growth_yoy(df: pd.DataFrame) -> dict:
    """
    Hitung pertumbuhan laba bersih Year-over-Year.

    Rumus: Profit Growth YoY = (NetProfit[t] - NetProfit[t-1]) / |NetProfit[t-1]|
    Threshold LULUS: > 0%
    """
    col = _find_column(df, ["earnings", "net_income", "netIncome", "net_profit", "Net Income"])
    if col is None or len(df) < 2:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 0%", "detail": []}

    latest, growths = _yoy_growth(df, col)
    return {"value": latest, "pass_fail": latest > 0, "threshold": "> 0%", "detail": growths}


# ═══════════════════════════════════════════════════════
# PILAR 4 — CASH FLOW GROWTH YoY
# ═══════════════════════════════════════════════════════

def calculate_cashflow_growth_yoy(df: pd.DataFrame) -> dict:
    """
    Hitung pertumbuhan arus kas operasi Year-over-Year.

    Rumus: CFO Growth YoY = (CFO[t] - CFO[t-1]) / |CFO[t-1]|
    Threshold LULUS: > 0%
    """
    col = _find_column(df, [
        "free_cash_flow", "operating_cash_flow", "operatingCashFlow",
        "cash_from_operations", "freeCashFlow",
    ])
    if col is None or len(df) < 2:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 0%", "detail": []}

    latest, growths = _yoy_growth(df, col)
    return {"value": latest, "pass_fail": latest > 0, "threshold": "> 0%", "detail": growths}


# ═══════════════════════════════════════════════════════
# PILAR 5 — ROE
# ═══════════════════════════════════════════════════════

def calculate_roe(income_df: pd.DataFrame, balance_df: pd.DataFrame) -> dict:
    """
    Hitung Return on Equity.

    Rumus: ROE = Net Income / Total Equity
    Threshold LULUS: > 10%
    """
    profit_col = _find_column(income_df, ["earnings", "net_income", "netIncome", "net_profit"])
    equity_col = _find_column(balance_df, [
        "total_equity", "totalEquity", "stockholders_equity",
        "total_shareholders_equity", "totalStockholdersEquity",
    ])

    if not profit_col or not equity_col or len(income_df) < 1 or len(balance_df) < 1:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 10%"}

    ni = _safe_float(income_df[profit_col].iloc[-1])
    eq = _safe_float(balance_df[equity_col].iloc[-1])

    if eq == 0:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 10%"}

    roe = ni / eq
    return {"value": roe, "pass_fail": roe > 0.10, "threshold": "> 10%"}


# ═══════════════════════════════════════════════════════
# PILAR 5 — ROIC
# ═══════════════════════════════════════════════════════

def calculate_roic(income_df: pd.DataFrame, balance_df: pd.DataFrame) -> dict:
    """
    Hitung Return on Invested Capital.

    Rumus:
        NOPAT ≈ Operating Income × (1 - 0.25)  (asumsi tax 25%)
        Invested Capital = Total Equity + Total Debt - Cash
        ROIC = NOPAT / Invested Capital
    Threshold LULUS: > 10%
    """
    op_col = _find_column(income_df, ["operating_pnl", "operating_income", "operatingIncome", "ebit", "EBIT"])
    profit_col = _find_column(income_df, ["earnings", "net_income", "netIncome", "net_profit"])
    equity_col = _find_column(balance_df, [
        "total_equity", "totalEquity", "stockholders_equity", "total_shareholders_equity",
    ])
    debt_col = _find_column(balance_df, ["total_debt", "totalDebt", "long_term_debt", "longTermDebt", "net_debt"])
    cash_col = _find_column(balance_df, [
        "cash_and_equivalents", "cashAndEquivalents", "cash_only",
        "cash", "cash_and_short_term_investments", "total_cash_and_due_from_banks",
    ])

    if not equity_col or len(balance_df) < 1:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 10%"}

    if op_col and len(income_df) >= 1:
        nopat = _safe_float(income_df[op_col].iloc[-1]) * 0.75
    elif profit_col and len(income_df) >= 1:
        nopat = _safe_float(income_df[profit_col].iloc[-1])
    else:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 10%"}

    equity = _safe_float(balance_df[equity_col].iloc[-1])
    debt = _safe_float(balance_df[debt_col].iloc[-1]) if debt_col else 0.0
    cash = _safe_float(balance_df[cash_col].iloc[-1]) if cash_col else 0.0
    ic = equity + debt - cash

    if ic <= 0:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 10%"}

    roic = nopat / ic
    return {"value": roic, "pass_fail": roic > 0.10, "threshold": "> 10%"}


# ═══════════════════════════════════════════════════════
# PILAR 6 — DEBT HEALTH
# ═══════════════════════════════════════════════════════

def calculate_debt_health(balance_df: pd.DataFrame) -> dict:
    """
    Hitung Debt-to-Equity Ratio dan Debt-to-Assets Ratio.

    Rumus:
        D/E = Total Debt / Total Equity
        D/A = Total Debt / Total Assets
    Threshold LULUS: D/E < 1.0
    """
    debt_col = _find_column(balance_df, [
        "total_debt", "totalDebt", "long_term_debt", "longTermDebt",
        "total_liabilities", "totalLiabilities", "net_debt",
    ])
    equity_col = _find_column(balance_df, [
        "total_equity", "totalEquity", "stockholders_equity", "total_shareholders_equity",
    ])
    asset_col = _find_column(balance_df, ["total_assets", "totalAssets"])

    if not debt_col or not equity_col or len(balance_df) < 1:
        return {"value": 0.0, "de_ratio": 0.0, "da_ratio": 0.0,
                "pass_fail": False, "threshold": "< 1.0", "interpretasi": "Data tidak tersedia"}

    total_debt = _safe_float(balance_df[debt_col].iloc[-1])
    total_equity = _safe_float(balance_df[equity_col].iloc[-1])
    total_assets = _safe_float(balance_df[asset_col].iloc[-1]) if asset_col else 0.0

    if total_equity == 0:
        return {"value": float("inf"), "de_ratio": float("inf"), "da_ratio": 0.0,
                "pass_fail": False, "threshold": "< 1.0", "interpretasi": "Ekuitas nol"}

    de = total_debt / total_equity
    da = total_debt / total_assets if total_assets > 0 else 0.0

    if de < 0.5:
        interp, risk = "Sangat sehat", "LOW RISK"
    elif de < 1.0:
        interp, risk = "Sehat", "LOW RISK"
    elif de < 2.0:
        interp, risk = "Perlu perhatian", "MEDIUM RISK"
    else:
        interp, risk = "Berisiko tinggi", "HIGH RISK"

    return {
        "value": de, "de_ratio": de, "da_ratio": da,
        "pass_fail": de < 1.0, "threshold": "< 1.0",
        "interpretasi": interp, "risk_label": risk,
    }


# ═══════════════════════════════════════════════════════
# PILAR 7 — GROWTH CAGR
# ═══════════════════════════════════════════════════════

def calculate_cagr(df: pd.DataFrame, column_hint: str = "revenue") -> dict:
    """
    Hitung Compound Annual Growth Rate multi-tahun.

    Rumus: CAGR = (EndValue / BeginValue) ^ (1/n) - 1
    Threshold LULUS: > 5%
    """
    hint_map = {
        "revenue": ["revenue", "total_revenue", "totalRevenue", "Revenue"],
        "net_income": ["earnings", "net_income", "netIncome", "net_profit", "Net Income"],
        "cash_flow": ["free_cash_flow", "operating_cash_flow", "operatingCashFlow", "freeCashFlow"],
    }
    candidates = hint_map.get(column_hint, [column_hint])
    col = _find_column(df, candidates)

    if col is None or len(df) < 2:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 5%"}

    values = _safe_series_float(df[col]).values
    begin, end, n = values[0], values[-1], len(values) - 1

    if begin <= 0 or end <= 0 or n == 0:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 5%"}

    cagr = (end / begin) ** (1 / n) - 1
    return {"value": cagr, "pass_fail": cagr > 0.05, "threshold": "> 5%"}


# ═══════════════════════════════════════════════════════
# PILAR 8 — INTRINSIC VALUE (DCF)
# ═══════════════════════════════════════════════════════

def calculate_dcf(
    free_cash_flows: list[float],
    discount_rate: float,
    growth_rate: float,
    terminal_growth: float = 0.03,
    shares_outstanding: float | None = None,
) -> dict:
    """
    Hitung Intrinsic Value via Discounted Cash Flow (Two-Stage Model).

    Tahap 1 — Explicit Period (5 tahun):
        Projected_FCF[t] = FCF_terakhir × (1 + growth_rate)^t
        PV[t] = Projected_FCF[t] / (1 + discount_rate)^t

    Tahap 2 — Terminal Value (Gordon Growth Model):
        TV = FCF[5] × (1 + terminal_growth) / (discount_rate - terminal_growth)
        PV_TV = TV / (1 + discount_rate)^5

    Intrinsic Value = (Σ PV[t] + PV_TV) / shares_outstanding
    """
    if not free_cash_flows or discount_rate <= terminal_growth:
        return {
            "intrinsic_value": 0.0, "enterprise_value": 0.0,
            "projected_fcf": [], "present_values": [], "terminal_value": 0.0,
            "value": 0.0, "pass_fail": False, "threshold": "DCF > Harga Pasar",
        }

    last_fcf = free_cash_flows[-1]
    if last_fcf <= 0:
        positive = [f for f in free_cash_flows if f > 0]
        last_fcf = float(np.mean(positive)) if positive else 0.0

    if last_fcf <= 0:
        return {
            "intrinsic_value": 0.0, "enterprise_value": 0.0,
            "projected_fcf": [], "present_values": [], "terminal_value": 0.0,
            "value": 0.0, "pass_fail": False, "threshold": "DCF > Harga Pasar",
        }

    proj_years = 5
    projected_fcf, present_values = [], []
    for t in range(1, proj_years + 1):
        proj = last_fcf * (1 + growth_rate) ** t
        pv = proj / (1 + discount_rate) ** t
        projected_fcf.append(proj)
        present_values.append(pv)

    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
    tv = terminal_fcf / (discount_rate - terminal_growth)
    pv_tv = tv / (1 + discount_rate) ** proj_years

    ev = sum(present_values) + pv_tv
    iv = ev / shares_outstanding if shares_outstanding and shares_outstanding > 0 else ev

    return {
        "intrinsic_value": iv, "enterprise_value": ev,
        "projected_fcf": projected_fcf, "present_values": present_values,
        "terminal_value": tv,
        "value": iv, "pass_fail": True, "threshold": "DCF > Harga Pasar",
    }


# ═══════════════════════════════════════════════════════
# PILAR 9 — MARGIN OF SAFETY
# ═══════════════════════════════════════════════════════

def calculate_margin_of_safety(intrinsic_value: float, current_price: float) -> dict:
    """
    Hitung Margin of Safety (MoS).

    Rumus: MoS = (Intrinsic Value - Current Price) / Intrinsic Value
    Threshold LULUS: MoS > 25% (standar Benjamin Graham).
    """
    if intrinsic_value <= 0 or current_price <= 0:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 25%",
                "intrinsic_value": intrinsic_value, "current_price": current_price}

    mos = (intrinsic_value - current_price) / intrinsic_value
    return {
        "value": mos, "pass_fail": mos > 0.25, "threshold": "> 25%",
        "intrinsic_value": intrinsic_value, "current_price": current_price,
    }


# ═══════════════════════════════════════════════════════
# UTIL — PROYEKSI FUTURE VALUE
# ═══════════════════════════════════════════════════════

def project_future_value_recurrence(
    initial_value: float, growth_rate: float, periods: int,
) -> list[dict]:
    """
    Proyeksi nilai masa depan menggunakan relasi rekurensi.

    FV[n] = FV[n-1] × (1 + growth_rate)
    """
    projections = [{"period": 0, "value": initial_value}]
    current = initial_value
    for n in range(1, periods + 1):
        current = current * (1 + growth_rate)
        projections.append({"period": n, "value": current})
    return projections
