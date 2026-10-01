"""
health.py — Mesin kalkulasi kesehatan keuangan perusahaan.

Menghitung: ROE, ROIC, Debt-to-Equity, Debt-to-Assets,
dan proxy efisiensi manajemen (Asset Turnover + margin trend).
"""

import numpy as np
import pandas as pd


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
        "cash", "cash_and_short_term_investments",
        "total_cash_and_due_from_banks",
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
        interp = "Sangat sehat"
        risk = "LOW RISK"
    elif de < 1.0:
        interp = "Sehat"
        risk = "LOW RISK"
    elif de < 2.0:
        interp = "Perlu perhatian"
        risk = "MEDIUM RISK"
    else:
        interp = "Berisiko tinggi"
        risk = "HIGH RISK"

    return {
        "value": de, "de_ratio": de, "da_ratio": da,
        "pass_fail": de < 1.0, "threshold": "< 1.0",
        "interpretasi": interp, "risk_label": risk,
    }


def calculate_management_efficiency(
    income_df: pd.DataFrame, balance_df: pd.DataFrame,
) -> dict:
    """
    Proxy efisiensi manajemen — Asset Turnover + margin trend.

    Rumus: Asset Turnover = Revenue / Total Assets
    Threshold LULUS: > 0.5 ATAU margin trend positif (3 tahun).
    """
    rev_col = _find_column(income_df, ["revenue", "total_revenue", "totalRevenue"])
    asset_col = _find_column(balance_df, ["total_assets", "totalAssets"])
    profit_col = _find_column(income_df, ["earnings", "net_income", "netIncome", "net_profit"])

    at = 0.0
    margin_trend_positive = False

    if rev_col and asset_col and len(income_df) >= 1 and len(balance_df) >= 1:
        revenue = _safe_float(income_df[rev_col].iloc[-1])
        assets = _safe_float(balance_df[asset_col].iloc[-1])
        if assets > 0:
            at = revenue / assets

    if rev_col and profit_col and len(income_df) >= 3:
        revs = _safe_series_float(income_df[rev_col]).values[-3:]
        profs = _safe_series_float(income_df[profit_col]).values[-3:]
        margins = [p / r if r != 0 else 0 for r, p in zip(revs, profs)]
        if len(margins) >= 2:
            diffs = [margins[i] - margins[i - 1] for i in range(1, len(margins))]
            margin_trend_positive = all(d > 0 for d in diffs)

    return {
        "value": at,
        "pass_fail": at > 0.5 or margin_trend_positive,
        "threshold": "> 0.5 atau margin trend ↑",
        "margin_trend_positive": margin_trend_positive,
    }


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Cari nama kolom yang cocok (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None
