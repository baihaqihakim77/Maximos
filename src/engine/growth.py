"""
growth.py — Mesin kalkulasi pertumbuhan keuangan.

Menghitung: Revenue Growth YoY, Profit Growth YoY, Cash Flow Growth YoY,
CAGR multi-tahun, dan Profitabilitas (Net Profit Margin).
"""

import numpy as np
import pandas as pd


def _safe_series_float(series: pd.Series) -> pd.Series:
    """Konversi series ke float dengan aman, replace None/NaN → 0.0."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _safe_float(value) -> float:
    """Konversi nilai ke float, kembalikan 0.0 jika None/NaN/tidak valid."""
    try:
        if value is None:
            return 0.0
        f = float(value)
        return 0.0 if (np.isnan(f) or np.isinf(f)) else f
    except (TypeError, ValueError):
        return 0.0


def calculate_revenue_growth_yoy(df: pd.DataFrame) -> dict:
    """
    Hitung pertumbuhan pendapatan Year-over-Year.

    Rumus: Revenue Growth YoY = (Revenue[t] - Revenue[t-1]) / Revenue[t-1]
    Threshold LULUS: > 0%
    """
    rev_col = _find_column(df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    if rev_col is None or len(df) < 2:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 0%", "detail": []}

    revenues = _safe_series_float(df[rev_col]).values
    growths = []
    for i in range(1, len(revenues)):
        if revenues[i - 1] != 0:
            growths.append((revenues[i] - revenues[i - 1]) / abs(revenues[i - 1]))
        else:
            growths.append(0.0)

    latest = growths[-1] if growths else 0.0
    return {"value": latest, "pass_fail": latest > 0, "threshold": "> 0%", "detail": growths}


def calculate_profit_growth_yoy(df: pd.DataFrame) -> dict:
    """
    Hitung pertumbuhan laba bersih Year-over-Year.

    Rumus: Profit Growth YoY = (NetProfit[t] - NetProfit[t-1]) / |NetProfit[t-1]|
    Threshold LULUS: > 0%
    """
    col = _find_column(df, ["earnings", "net_income", "netIncome", "net_profit", "Net Income"])
    if col is None or len(df) < 2:
        return {"value": 0.0, "pass_fail": False, "threshold": "> 0%", "detail": []}

    values = _safe_series_float(df[col]).values
    growths = []
    for i in range(1, len(values)):
        if values[i - 1] != 0:
            growths.append((values[i] - values[i - 1]) / abs(values[i - 1]))
        else:
            growths.append(0.0)

    latest = growths[-1] if growths else 0.0
    return {"value": latest, "pass_fail": latest > 0, "threshold": "> 0%", "detail": growths}


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

    values = _safe_series_float(df[col]).values
    growths = []
    for i in range(1, len(values)):
        if values[i - 1] != 0:
            growths.append((values[i] - values[i - 1]) / abs(values[i - 1]))
        else:
            growths.append(0.0)

    latest = growths[-1] if growths else 0.0
    return {"value": latest, "pass_fail": latest > 0, "threshold": "> 0%", "detail": growths}


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


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Cari nama kolom yang cocok (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None
