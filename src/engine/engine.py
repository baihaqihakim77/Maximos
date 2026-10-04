"""
engine.py — Mesin kalkulasi fundamental value investing 9 Pilar.

Menggabungkan semua perhitungan 9 pilar analisis fundamental:
  1. Profitabilitas (Net Profit Margin — Multi-Year & Trend)
  2. Revenue Growth YoY (Konsistensi Pertumbuhan Kalender)
  3. Profit Growth YoY (Konsistensi Pertumbuhan Laba)
  4. Cash Flow Growth YoY (Arus Kas Bebas / Operasi)
  5. ROE (Return on Equity — Buffett Standard >=15% & Leverage Check)
  6. ROIC (Return on Invested Capital — Effective Tax Rate & Invested Capital)
  7. Debt Health (D/E, D/A, ICR & Sector-Aware)
  8. Growth CAGR (Multi-Year Compound Growth: Revenue, Profit, FCF)
  9. Intrinsic Value via DCF (Two-Stage Model: EV to Equity Bridge) & Margin of Safety
"""

from datetime import datetime
from typing import Any
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_CORPORATE_TAX_RATE,
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_GROWTH_RATE,
    DEFAULT_PROJECTION_YEARS,
    DEFAULT_TERMINAL_GROWTH,
    MIN_CONSISTENCY_RATIO,
    get_threshold,
)


# ═══════════════════════════════════════════════════════
# HELPERS INTERNAL
# ═══════════════════════════════════════════════════════

def _safe_float(value: Any) -> float:
    """Konversi nilai ke float, kembalikan 0.0 jika None/NaN/inf/tidak valid."""
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


def _find_column(df: pd.DataFrame | None, candidates: list[str]) -> str | None:
    """Cari nama kolom yang cocok (case-insensitive)."""
    if df is None or df.empty:
        return None
    cols_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


def _yoy_growth(df: pd.DataFrame, col: str) -> tuple[float, list[float], list[str]]:
    """
    Hitung YoY growth untuk satu kolom.
    
    Returns:
        (latest_growth, list_of_growths, list_of_years)
        Contoh list_of_years: ['2021', '2022', '2023', '2024', '2025']
    """
    values = _safe_series_float(df[col]).values
    growths: list[float] = []

    year_col = _find_column(df, ["year", "Year", "fiscal_year"])
    if year_col and len(df[year_col]) == len(values):
        years_raw = [str(int(y)) if str(y).replace('.', '').isdigit() else str(y) for y in df[year_col]]
        growth_years = [years_raw[i] for i in range(1, len(values))]
    else:
        curr_y = datetime.now().year
        growth_years = [str(curr_y - len(values) + 1 + i) for i in range(1, len(values))]

    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if prev != 0:
            growths.append((curr - prev) / abs(prev))
        else:
            growths.append(0.0)

    latest = growths[-1] if growths else 0.0
    return latest, growths, growth_years


def _calculate_consistency(growths: list[float]) -> tuple[float, float, str]:
    """
    Hitung rasio konsistensi pertumbuhan positif dan tren arah.

    Returns:
        (consistency_ratio, avg_growth, trend_label)
    """
    if not growths:
        return 0.0, 0.0, "Netral"

    positive_years = sum(1 for g in growths if g > 0)
    consistency_ratio = positive_years / len(growths)
    avg_growth = float(np.mean(growths))

    if len(growths) >= 2:
        recent_trend = growths[-1] - growths[0]
        if recent_trend > 0.05:
            trend_label = "Meningkat"
        elif recent_trend < -0.05:
            trend_label = "Menurun"
        else:
            trend_label = "Stabil"
    else:
        trend_label = "Meningkat" if growths[-1] > 0 else "Menurun"

    return consistency_ratio, avg_growth, trend_label


def _calculate_effective_tax_rate(df: pd.DataFrame) -> float:
    """
    Hitung tarif pajak efektif dari laporan laba rugi.
    Formula: Tax Expense / Earnings Before Tax
    Fallback ke tarif pajak standar Indonesia (UU HPP 22%).
    """
    tax_col = _find_column(df, ["tax", "income_tax", "tax_expense", "income_tax_expense"])
    ebt_col = _find_column(df, ["earnings_before_tax", "ebt", "pretax_income", "pre_tax_income"])

    if tax_col and ebt_col and len(df) >= 1:
        tax_val = _safe_float(df[tax_col].iloc[-1])
        ebt_val = _safe_float(df[ebt_col].iloc[-1])
        if ebt_val > 0 and tax_val > 0:
            rate = tax_val / ebt_val
            # Batas wajar tarif pajak korporasi: 5% - 40%
            if 0.05 <= rate <= 0.40:
                return rate

    return DEFAULT_CORPORATE_TAX_RATE


# ═══════════════════════════════════════════════════════
# PILAR 1 — PROFITABILITAS (NET PROFIT MARGIN)
# ═══════════════════════════════════════════════════════

def calculate_profitability(df: pd.DataFrame, sector: str | None = None) -> dict[str, Any]:
    """
    Evaluasi profitabilitas — Net Profit Margin (multi-tahun & tren).

    Rumus: NPM = Net Income / Revenue
    Threshold LULUS: NPM Terakhir > 5% dan Rata-rata Multi-Tahun > 5%
    """
    cfg = get_threshold("profitabilitas", sector)
    min_npm = cfg.get("min_npm", 0.05)

    rev_col = _find_column(df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    profit_col = _find_column(df, ["earnings", "net_income", "netIncome", "net_profit", "Net Income"])

    if rev_col is None or profit_col is None or len(df) < 1:
        return {
            "value": 0.0,
            "avg_npm": 0.0,
            "median_npm": 0.0,
            "trend": "Tidak tersedia",
            "historical_npm": [],
            "historical_years": [],
            "pass_fail": False,
            "threshold": cfg.get("label", "> 5%"),
        }

    rev_series = _safe_series_float(df[rev_col])
    profit_series = _safe_series_float(df[profit_col])

    # Ambil tahun kalender
    year_col = _find_column(df, ["year", "Year", "fiscal_year"])
    if year_col and len(df[year_col]) == len(rev_series):
        years = [str(int(y)) if str(y).replace('.', '').isdigit() else str(y) for y in df[year_col]]
    else:
        curr_y = datetime.now().year
        years = [str(curr_y - len(rev_series) + 1 + i) for i in range(len(rev_series))]

    # Hitung NPM historis
    historical_npm = []
    for r, p in zip(rev_series, profit_series):
        historical_npm.append(p / r if r > 0 else 0.0)

    latest_npm = historical_npm[-1] if historical_npm else 0.0
    avg_npm = float(np.mean(historical_npm)) if historical_npm else 0.0
    median_npm = float(np.median(historical_npm)) if historical_npm else 0.0

    # Analisis tren
    if len(historical_npm) >= 2:
        npm_delta = historical_npm[-1] - historical_npm[0]
        if npm_delta > 0.02:
            trend = "Ekspansi Margin"
        elif npm_delta < -0.02:
            trend = "Kompresi Margin"
        else:
            trend = "Margin Stabil"
    else:
        trend = "Cukup" if latest_npm >= min_npm else "Rendah"

    passed = (latest_npm >= min_npm) and (avg_npm >= min_npm if len(historical_npm) >= 3 else True)

    return {
        "value": latest_npm,
        "avg_npm": avg_npm,
        "median_npm": median_npm,
        "trend": trend,
        "historical_npm": historical_npm,
        "historical_years": years,
        "pass_fail": passed,
        "threshold": cfg.get("label", "> 5%"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 2 — REVENUE GROWTH YoY (KONSISTENSI MULTI-TAHUN)
# ═══════════════════════════════════════════════════════

def calculate_revenue_growth_yoy(df: pd.DataFrame, sector: str | None = None) -> dict[str, Any]:
    """
    Hitung pertumbuhan pendapatan YoY beserta konsistensi historis.

    Rumus: YoY = (Revenue[t] - Revenue[t-1]) / Revenue[t-1]
    Threshold LULUS: YoY Terakhir > 0% DAN Konsistensi Pertumbuhan >= 60%
    """
    cfg = get_threshold("revenue_growth", sector)
    min_consistency = cfg.get("min_consistency", MIN_CONSISTENCY_RATIO)

    rev_col = _find_column(df, ["revenue", "total_revenue", "totalRevenue", "Revenue"])
    if rev_col is None or len(df) < 2:
        return {
            "value": 0.0,
            "consistency_ratio": 0.0,
            "avg_growth": 0.0,
            "trend": "N/A",
            "detail": [],
            "growth_years": [],
            "pass_fail": False,
            "threshold": cfg.get("label", "> 0% (Konsisten >=60%)"),
        }

    latest, growths, growth_years = _yoy_growth(df, rev_col)
    consistency, avg_growth, trend = _calculate_consistency(growths)

    passed = (latest > 0) and (consistency >= min_consistency if len(growths) >= 2 else True)

    return {
        "value": latest,
        "consistency_ratio": consistency,
        "avg_growth": avg_growth,
        "trend": trend,
        "detail": growths,
        "growth_years": growth_years,
        "pass_fail": passed,
        "threshold": cfg.get("label", "> 0% (Konsisten >=60%)"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 3 — PROFIT GROWTH YoY (KONSISTENSI MULTI-TAHUN)
# ═══════════════════════════════════════════════════════

def calculate_profit_growth_yoy(df: pd.DataFrame, sector: str | None = None) -> dict[str, Any]:
    """
    Hitung pertumbuhan laba bersih YoY beserta konsistensi historis.

    Rumus: YoY = (NetIncome[t] - NetIncome[t-1]) / |NetIncome[t-1]|
    Threshold LULUS: YoY Terakhir > 0% DAN Konsistensi Pertumbuhan >= 60%
    """
    cfg = get_threshold("profit_growth", sector)
    min_consistency = cfg.get("min_consistency", MIN_CONSISTENCY_RATIO)

    profit_col = _find_column(df, ["earnings", "net_income", "netIncome", "net_profit", "Net Income"])
    if profit_col is None or len(df) < 2:
        return {
            "value": 0.0,
            "consistency_ratio": 0.0,
            "avg_growth": 0.0,
            "trend": "N/A",
            "detail": [],
            "growth_years": [],
            "pass_fail": False,
            "threshold": cfg.get("label", "> 0% (Konsisten >=60%)"),
        }

    latest, growths, growth_years = _yoy_growth(df, profit_col)
    consistency, avg_growth, trend = _calculate_consistency(growths)

    passed = (latest > 0) and (consistency >= min_consistency if len(growths) >= 2 else True)

    return {
        "value": latest,
        "consistency_ratio": consistency,
        "avg_growth": avg_growth,
        "trend": trend,
        "detail": growths,
        "growth_years": growth_years,
        "pass_fail": passed,
        "threshold": cfg.get("label", "> 0% (Konsisten >=60%)"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 4 — CASH FLOW GROWTH YoY (FCF DIUTAMAKAN)
# ═══════════════════════════════════════════════════════

def calculate_cashflow_growth_yoy(df: pd.DataFrame, sector: str | None = None) -> dict[str, Any]:
    """
    Hitung pertumbuhan arus kas YoY (FCF diutamakan dibanding OCF).

    Rumus: CFO/FCF Growth YoY = (CF[t] - CF[t-1]) / |CF[t-1]|
    Threshold LULUS: YoY Terakhir > 0% DAN Konsistensi Pertumbuhan >= 60%
    """
    cfg = get_threshold("cashflow_growth", sector)
    min_consistency = cfg.get("min_consistency", MIN_CONSISTENCY_RATIO)

    fcf_col = _find_column(df, ["free_cash_flow", "freeCashFlow"])
    ocf_col = _find_column(df, ["operating_cash_flow", "operatingCashFlow", "cash_from_operations"])

    col = None
    metric_used = "FCF"

    if fcf_col:
        col = fcf_col
        metric_used = "FCF"
    elif ocf_col:
        capex_col = _find_column(df, ["realized_capital_goods_investment", "capex", "capital_expenditure"])
        if capex_col and len(df) >= 2:
            try:
                df = df.copy()
                df["calculated_fcf"] = _safe_series_float(df[ocf_col]) - _safe_series_float(df[capex_col]).abs()
                col = "calculated_fcf"
                metric_used = "Calculated FCF"
            except Exception:
                col = ocf_col
                metric_used = "OCF"
        else:
            col = ocf_col
            metric_used = "OCF"

    if col is None or len(df) < 2:
        return {
            "value": 0.0,
            "consistency_ratio": 0.0,
            "avg_growth": 0.0,
            "metric_used": metric_used,
            "trend": "N/A",
            "detail": [],
            "growth_years": [],
            "pass_fail": False,
            "threshold": cfg.get("label", "> 0% (Konsisten >=60%)"),
        }

    latest, growths, growth_years = _yoy_growth(df, col)
    consistency, avg_growth, trend = _calculate_consistency(growths)

    passed = (latest > 0) and (consistency >= min_consistency if len(growths) >= 2 else True)

    return {
        "value": latest,
        "consistency_ratio": consistency,
        "avg_growth": avg_growth,
        "metric_used": metric_used,
        "trend": trend,
        "detail": growths,
        "growth_years": growth_years,
        "pass_fail": passed,
        "threshold": cfg.get("label", "> 0% (Konsisten >=60%)"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 5 — RETURN ON EQUITY (ROE)
# ═══════════════════════════════════════════════════════

def calculate_roe(
    income_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    sector: str | None = None,
) -> dict[str, Any]:
    """
    Hitung Return on Equity multi-tahun dan deteksi leverage-driven ROE.

    Rumus: ROE = Net Income / Total Equity
    Analisis Leverage: Financial Leverage = Total Assets / Total Equity
    Threshold LULUS: ROE >= 15% (Standar Warren Buffett)
    """
    cfg = get_threshold("roe", sector)
    min_roe = cfg.get("min_roe", 0.15)
    max_leverage = cfg.get("max_leverage_ratio", 2.5)

    profit_col = _find_column(income_df, ["earnings", "net_income", "netIncome", "net_profit"])
    equity_col = _find_column(balance_df, [
        "total_equity", "totalEquity", "stockholders_equity",
        "total_shareholders_equity", "totalStockholdersEquity",
    ])
    asset_col = _find_column(balance_df, ["total_assets", "totalAssets"])

    if not profit_col or not equity_col or len(income_df) < 1 or len(balance_df) < 1:
        return {
            "value": 0.0,
            "avg_roe": 0.0,
            "leverage_multiplier": 1.0,
            "leverage_warning": False,
            "historical_roe": [],
            "pass_fail": False,
            "threshold": cfg.get("label", ">= 15%"),
        }

    profits = _safe_series_float(income_df[profit_col]).values
    equities = _safe_series_float(balance_df[equity_col]).values

    historical_roe = []
    min_len = min(len(profits), len(equities))
    for i in range(min_len):
        eq = equities[i]
        historical_roe.append(profits[i] / eq if eq > 0 else 0.0)

    latest_roe = historical_roe[-1] if historical_roe else 0.0
    avg_roe = float(np.mean(historical_roe)) if historical_roe else 0.0

    # Evaluasi Financial Leverage (Assets / Equity)
    latest_equity = equities[-1] if len(equities) > 0 else 0.0
    latest_assets = _safe_float(balance_df[asset_col].iloc[-1]) if asset_col else 0.0
    leverage_multiplier = latest_assets / latest_equity if latest_equity > 0 else 1.0

    # Khusus non-bank, leverage > 2.5 memicu warning bahwa ROE didongkrak hutang
    is_bank = "financial" in (sector or "").lower() or "bank" in (sector or "").lower()
    leverage_warning = (leverage_multiplier > max_leverage and not is_bank and latest_roe >= min_roe)

    # Validasi konsistensi: ROE terkini >= 15% dan rata-rata multi-tahun stabil
    passed = (latest_roe >= min_roe) and (avg_roe >= min_roe * 0.8 if len(historical_roe) >= 3 else True)

    return {
        "value": latest_roe,
        "avg_roe": avg_roe,
        "leverage_multiplier": leverage_multiplier,
        "leverage_warning": leverage_warning,
        "historical_roe": historical_roe,
        "pass_fail": passed,
        "threshold": cfg.get("label", ">= 15%"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 6 — RETURN ON INVESTED CAPITAL (ROIC)
# ═══════════════════════════════════════════════════════

def calculate_roic(
    income_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    sector: str | None = None,
) -> dict[str, Any]:
    """
    Hitung Return on Invested Capital dengan effective tax rate dan modal diinvestasikan.

    Rumus:
        NOPAT = Operating Income (EBIT) × (1 - Effective_Tax_Rate)
        Invested Capital = Total Equity + Total Debt - Cash & Equivalents
        ROIC = NOPAT / Invested Capital
    Threshold LULUS: ROIC > 10%
    """
    cfg = get_threshold("roic", sector)
    min_roic = cfg.get("min_roic", 0.10)

    op_col = _find_column(income_df, ["ebit", "operating_pnl", "operating_income", "operatingIncome", "EBIT"])
    profit_col = _find_column(income_df, ["earnings", "net_income", "netIncome", "net_profit"])
    equity_col = _find_column(balance_df, [
        "total_equity", "totalEquity", "stockholders_equity", "total_shareholders_equity",
    ])
    debt_col = _find_column(balance_df, ["total_debt", "totalDebt", "long_term_debt", "short_term_debt"])
    cash_col = _find_column(balance_df, [
        "cash_and_equivalents", "cashAndEquivalents", "cash_only",
        "cash", "total_cash_and_due_from_banks",
    ])

    if not equity_col or len(balance_df) < 1 or len(income_df) < 1:
        return {
            "value": 0.0,
            "avg_roic": 0.0,
            "nopat": 0.0,
            "invested_capital": 0.0,
            "tax_rate_used": DEFAULT_CORPORATE_TAX_RATE,
            "pass_fail": False,
            "threshold": cfg.get("label", "> 10%"),
        }

    effective_tax_rate = _calculate_effective_tax_rate(income_df)

    if op_col:
        ebit = _safe_float(income_df[op_col].iloc[-1])
        nopat = ebit * (1.0 - effective_tax_rate)
    elif profit_col:
        nopat = _safe_float(income_df[profit_col].iloc[-1])
    else:
        return {
            "value": 0.0,
            "avg_roic": 0.0,
            "nopat": 0.0,
            "invested_capital": 0.0,
            "tax_rate_used": effective_tax_rate,
            "pass_fail": False,
            "threshold": cfg.get("label", "> 10%"),
        }

    equity = _safe_float(balance_df[equity_col].iloc[-1])
    debt = _safe_float(balance_df[debt_col].iloc[-1]) if debt_col else 0.0
    cash = _safe_float(balance_df[cash_col].iloc[-1]) if cash_col else 0.0

    ic = equity + debt - cash

    # Standar Teori Valuasi (Aswath Damodaran / McKinsey):
    # Jika kas melimpah (Net Cash > Equity), modal kerja operasional tidak boleh terdistorsi mengecil
    # Invested Capital dibatasi batas bawah rasional (minimal 25% dari Equity)
    if ic <= 0 or (equity > 0 and ic < equity * 0.25):
        ic = max(equity * 0.5, equity + debt - cash) if equity > 0 else (debt if debt > 0 else 1.0)

    roic = nopat / ic if ic > 0 else 0.0

    # Multi-year ROIC
    historical_roic = []
    if op_col and len(income_df) >= 2 and len(balance_df) >= 2:
        min_len = min(len(income_df), len(balance_df))
        for i in range(min_len):
            _ebit = _safe_float(income_df[op_col].iloc[i])
            _nop = _ebit * (1.0 - effective_tax_rate)
            _eq = _safe_float(balance_df[equity_col].iloc[i])
            _dt = _safe_float(balance_df[debt_col].iloc[i]) if debt_col else 0.0
            _cs = _safe_float(balance_df[cash_col].iloc[i]) if cash_col else 0.0
            _inv = _eq + _dt - _cs
            if _inv <= 0 or (_eq > 0 and _inv < _eq * 0.25):
                _inv = max(_eq * 0.5, _eq + _dt - _cs) if _eq > 0 else 1.0
            if _inv > 0:
                historical_roic.append(_nop / _inv)
    avg_roic = float(np.mean(historical_roic)) if historical_roic else roic

    return {
        "value": roic,
        "avg_roic": avg_roic,
        "nopat": nopat,
        "invested_capital": ic,
        "tax_rate_used": effective_tax_rate,
        "pass_fail": roic > min_roic,
        "threshold": cfg.get("label", "> 10%"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 7 — DEBT HEALTH & INTEREST COVERAGE
# ═══════════════════════════════════════════════════════

def calculate_debt_health(
    balance_df: pd.DataFrame,
    income_df: pd.DataFrame | None = None,
    sector: str | None = None,
) -> dict[str, Any]:
    """
    Hitung kesehatan struktur hutang: D/E, D/A, dan Interest Coverage Ratio (ICR).

    Rumus:
        D/E = Total Debt (Beban Bunga) / Total Equity
        D/A = Total Debt / Total Assets
        ICR = Operating PnL (EBIT) / Interest Expense
    Penyesuaian Sektoral: Threshold disesuaikan untuk Bank / Finansial / Infrastruktur.
    """
    cfg = get_threshold("debt_health", sector)
    max_de = cfg.get("max_de", 1.0)
    max_da = cfg.get("max_da", 0.5)
    min_icr = cfg.get("min_icr", 3.0)
    is_bank = cfg.get("is_bank", False)

    # Pisahkan total_debt (interest-bearing) dari total_liabilities
    debt_col = _find_column(balance_df, ["total_debt", "totalDebt", "long_term_debt"])
    liabilities_col = _find_column(balance_df, ["total_liabilities", "totalLiabilities"])
    equity_col = _find_column(balance_df, [
        "total_equity", "totalEquity", "stockholders_equity", "total_shareholders_equity",
    ])
    asset_col = _find_column(balance_df, ["total_assets", "totalAssets"])

    if not equity_col or len(balance_df) < 1:
        return {
            "value": 0.0,
            "de_ratio": 0.0,
            "da_ratio": 0.0,
            "interest_coverage": 0.0,
            "pass_fail": False,
            "threshold": cfg.get("label", "< 1.0x"),
            "interpretasi": "Data tidak tersedia",
            "risk_label": "UNKNOWN RISK",
        }

    total_equity = _safe_float(balance_df[equity_col].iloc[-1])
    total_assets = _safe_float(balance_df[asset_col].iloc[-1]) if asset_col else 0.0
    total_liabilities = _safe_float(balance_df[liabilities_col].iloc[-1]) if liabilities_col else 0.0

    if debt_col:
        total_debt = _safe_float(balance_df[debt_col].iloc[-1])
    elif liabilities_col:
        total_debt = total_liabilities
    else:
        total_debt = 0.0

    if total_equity <= 0:
        return {
            "value": float("inf"),
            "de_ratio": float("inf"),
            "da_ratio": 0.0,
            "interest_coverage": 0.0,
            "pass_fail": False,
            "threshold": cfg.get("label", "< 1.0x"),
            "interpretasi": "Ekuitas negatif / nol (Distressed)",
            "risk_label": "HIGH RISK",
            "is_bank": is_bank,
        }

    de = total_debt / total_equity
    da = total_debt / total_assets if total_assets > 0 else 0.0

    # Hitung Interest Coverage Ratio (ICR)
    icr = 999.0
    if income_df is not None and not income_df.empty:
        ebit_col = _find_column(income_df, ["ebit", "operating_pnl", "operating_income"])
        int_exp_col = _find_column(income_df, ["interest_expense", "interestExpense", "interest_expense_non_operating"])
        if ebit_col and int_exp_col:
            ebit_val = _safe_float(income_df[ebit_col].iloc[-1])
            int_exp_val = abs(_safe_float(income_df[int_exp_col].iloc[-1]))
            if int_exp_val > 0:
                icr = ebit_val / int_exp_val

    # Evaluasi risiko sektoral
    if is_bank:
        # Untuk bank: liabilitas total merefleksikan DPK (Dana Pihak Ketiga: tabungan/deposito)
        # Financial Leverage = Total Liabilities / Equity (standar bank sehat: 4.0x - 8.0x)
        fin_leverage = total_liabilities / total_equity if total_equity > 0 else 0.0
        liab_asset = total_liabilities / total_assets if total_assets > 0 else 0.0

        # Cari metrik spesifik perbankan: LDR (Loan to Deposit) & CAR (Capital Adequacy)
        dep_col = _find_column(balance_df, ["total_deposit", "totalDeposit", "deposits"])
        loan_col = _find_column(balance_df, ["net_loan", "gross_loan", "loans"])
        cap_col = _find_column(balance_df, ["total_capital", "core_capital_tier1"])
        rwa_col = _find_column(balance_df, ["total_risk_weighted_asset", "credit_rwa"])

        ldr = None
        if dep_col and loan_col:
            dep_val = _safe_float(balance_df[dep_col].iloc[-1])
            loan_val = _safe_float(balance_df[loan_col].iloc[-1])
            if dep_val > 0:
                ldr = (loan_val / dep_val) * 100

        car = None
        if cap_col and rwa_col:
            cap_val = _safe_float(balance_df[cap_col].iloc[-1])
            rwa_val = _safe_float(balance_df[rwa_col].iloc[-1])
            if rwa_val > 0:
                car = (cap_val / rwa_val) * 100

        # Evaluasi solvabilitas bank
        car_ok = (car >= 12.0) if car is not None else True
        ldr_ok = (65.0 <= ldr <= 95.0) if ldr is not None else True

        if fin_leverage <= 6.0 and car_ok and ldr_ok:
            interp = "Permodalan bank sangat solid (CAR & LDR sehat)"
            risk = "LOW RISK"
            passed = True
        elif fin_leverage <= max_de and car_ok:
            interp = "Leverage bank wajar & aman"
            risk = "LOW RISK"
            passed = True
        elif fin_leverage <= max_de * 1.25:
            interp = "Leverage bank sedang (perlu dipantau)"
            risk = "MEDIUM RISK"
            passed = False
        else:
            interp = "Leverage bank tinggi di atas batas wajar"
            risk = "HIGH RISK"
            passed = False

        pure_de = (_safe_float(balance_df[debt_col].iloc[-1]) / total_equity) if debt_col else 0.0

        return {
            "value": fin_leverage,
            "de_ratio": pure_de,
            "da_ratio": liab_asset,
            "interest_coverage": icr,
            "financial_leverage": fin_leverage,
            "ldr": ldr,
            "car": car,
            "is_bank": True,
            "pass_fail": passed,
            "threshold": cfg.get("label", "< 8.0x (Sektor Finansial)"),
            "interpretasi": interp,
            "risk_label": risk,
        }
    else:
        icr_ok = (icr >= min_icr) if min_icr > 0 else True
        if de < 0.5 and da < 0.35 and icr_ok:
            interp, risk = "Neraca sangat kuat & aman", "LOW RISK"
            passed = True
        elif de <= max_de and da <= max_da and icr_ok:
            interp, risk = "Hutang dalam batas wajar", "LOW RISK"
            passed = True
        elif de <= max_de * 1.5:
            interp, risk = "Perlu perhatian (leverage sedang)", "MEDIUM RISK"
            passed = False
        else:
            interp, risk = "Beban hutang tinggi", "HIGH RISK"
            passed = False

    return {
        "value": de,
        "de_ratio": de,
        "da_ratio": da,
        "interest_coverage": icr,
        "financial_leverage": de,
        "ldr": None,
        "car": None,
        "is_bank": False,
        "pass_fail": passed,
        "threshold": cfg.get("label", "< 1.0x"),
        "interpretasi": interp,
        "risk_label": risk,
    }


# ═══════════════════════════════════════════════════════
# PILAR 8 — GROWTH CAGR (MULTI-METRIC & TAHUN KALENDER)
# ═══════════════════════════════════════════════════════

def calculate_cagr(
    df: pd.DataFrame,
    column_hint: str = "revenue",
    sector: str | None = None,
) -> dict[str, Any]:
    """
    Hitung Compound Annual Growth Rate (CAGR) multi-metrik & periode tahun kalender riil.

    Rumus: CAGR = (EndValue / BeginValue) ^ (1/n) - 1
    Menganalisis Revenue, Net Income, dan Cash Flow secara komprehensif.
    """
    cfg = get_threshold("growth_cagr", sector)
    min_cagr = cfg.get("min_cagr", 0.05)

    hint_map = {
        "revenue": ["revenue", "total_revenue", "totalRevenue", "Revenue"],
        "net_income": ["earnings", "net_income", "netIncome", "net_profit", "Net Income"],
        "cash_flow": ["free_cash_flow", "operating_cash_flow", "operatingCashFlow", "freeCashFlow"],
    }

    def _get_single_cagr(col_candidates: list[str]) -> float:
        col = _find_column(df, col_candidates)
        if col is None or len(df) < 2:
            return 0.0
        values = _safe_series_float(df[col]).values
        begin, end, n = values[0], values[-1], len(values) - 1
        if begin <= 0 or end <= 0 or n == 0:
            return 0.0
        try:
            return float((end / begin) ** (1 / n) - 1)
        except Exception:
            return 0.0

    cagr_revenue = _get_single_cagr(hint_map["revenue"])
    cagr_profit = _get_single_cagr(hint_map["net_income"])
    cagr_fcf = _get_single_cagr(hint_map["cash_flow"])

    target_candidates = hint_map.get(column_hint, [column_hint])
    main_cagr = _get_single_cagr(target_candidates)

    n_years = max(1, len(df) - 1)
    passed = main_cagr >= min_cagr

    # Deteksi tahun awal dan tahun akhir kalender
    year_col = _find_column(df, ["year", "Year", "fiscal_year"])
    start_year = None
    end_year = None
    if year_col and len(df[year_col]) >= 2:
        try:
            start_year = int(df[year_col].iloc[0])
            end_year = int(df[year_col].iloc[-1])
        except (ValueError, TypeError):
            pass

    if not start_year or not end_year:
        curr_y = datetime.now().year
        end_year = curr_y
        start_year = curr_y - n_years

    return {
        "value": main_cagr,
        "cagr_revenue": cagr_revenue,
        "cagr_profit": cagr_profit,
        "cagr_fcf": cagr_fcf,
        "start_year": start_year,
        "end_year": end_year,
        "years_count": n_years,
        "pass_fail": passed,
        "threshold": cfg.get("label", "> 5%"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 9 — INTRINSIC VALUE (DCF DUA TAHAP & EV-TO-EQUITY)
# ═══════════════════════════════════════════════════════

def calculate_dcf(
    free_cash_flows: list[float],
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    growth_rate: float = DEFAULT_GROWTH_RATE,
    terminal_growth: float = DEFAULT_TERMINAL_GROWTH,
    shares_outstanding: float | None = None,
    projection_years: int = DEFAULT_PROJECTION_YEARS,
    current_price: float = 0.0,
    total_debt: float = 0.0,
    cash_and_equivalents: float = 0.0,
    base_year: int | None = None,
    is_bank: bool = False,
) -> dict[str, Any]:
    """
    Hitung Intrinsic Value via Discounted Cash Flow (Two-Stage Model).
    
    Mengikuti Teori Valuasi Fundamental (Aswath Damodaran & McKinsey):
        1. Explicit Period Proyeksi FCF (dengan penomoran tahun kalender 2026, 2027, dst)
        2. Terminal Value via Gordon Growth Model
        3. Enterprise Value (EV) = Σ PV(FCF) + PV(Terminal Value)
        4. Jembatan EV ke Equity Value:
           Equity Value = Enterprise Value + Kas & Setara Kas - Total Hutang Berbunga
        5. Intrinsic Value per Share = Equity Value / Jumlah Saham Beredar
    """
    cfg = get_threshold("intrinsic_value")

    if not base_year:
        base_year = datetime.now().year

    if not free_cash_flows or discount_rate <= terminal_growth or projection_years <= 0:
        return {
            "intrinsic_value": 0.0,
            "enterprise_value": 0.0,
            "equity_value": 0.0,
            "projected_fcf": [],
            "projected_years": [],
            "present_values": [],
            "terminal_value": 0.0,
            "projection_years": projection_years,
            "base_year": base_year,
            "value": 0.0,
            "pass_fail": False,
            "threshold": cfg.get("label", "DCF > Harga Pasar"),
        }

    last_fcf = free_cash_flows[-1]
    if last_fcf <= 0:
        positive = [f for f in free_cash_flows if f > 0]
        last_fcf = float(np.mean(positive)) if positive else 0.0

    if last_fcf <= 0:
        return {
            "intrinsic_value": 0.0,
            "enterprise_value": 0.0,
            "equity_value": 0.0,
            "projected_fcf": [],
            "projected_years": [],
            "present_values": [],
            "terminal_value": 0.0,
            "projection_years": projection_years,
            "base_year": base_year,
            "value": 0.0,
            "pass_fail": False,
            "threshold": cfg.get("label", "DCF > Harga Pasar"),
        }

    # Proyeksi eksplisit dengan tahun kalender aktual (misal: 2026, 2027, 2028, dst)
    projected_fcf: list[float] = []
    present_values: list[float] = []
    projected_years: list[int] = []

    for t in range(1, projection_years + 1):
        proj = last_fcf * ((1.0 + growth_rate) ** t)
        pv = proj / ((1.0 + discount_rate) ** t)
        projected_fcf.append(proj)
        present_values.append(pv)
        projected_years.append(base_year + t)

    # Terminal Value
    terminal_fcf = projected_fcf[-1] * (1.0 + terminal_growth)
    tv = terminal_fcf / (discount_rate - terminal_growth)
    pv_tv = tv / ((1.0 + discount_rate) ** projection_years)

    ev = sum(present_values) + pv_tv

    # Jembatan EV ke Equity Value:
    # Untuk bank, FCF mencerminkan aliran ekuitas secara langsung
    # Untuk non-bank, sesuaikan dengan Net Debt (Kas - Total Hutang)
    if is_bank:
        equity_value = ev
    else:
        equity_value = ev + cash_and_equivalents - total_debt
        if equity_value < 0:
            equity_value = 0.0

    iv = equity_value / shares_outstanding if (shares_outstanding and shares_outstanding > 0) else equity_value
    passed = (iv > current_price) if current_price > 0 else (iv > 0)

    return {
        "intrinsic_value": iv,
        "enterprise_value": ev,
        "equity_value": equity_value,
        "projected_fcf": projected_fcf,
        "projected_years": projected_years,
        "present_values": present_values,
        "terminal_value": tv,
        "projection_years": projection_years,
        "base_year": base_year,
        "value": iv,
        "pass_fail": passed,
        "threshold": cfg.get("label", "DCF > Harga Pasar"),
    }


# ═══════════════════════════════════════════════════════
# PILAR 10 — MARGIN OF SAFETY (BENJAMIN GRAHAM)
# ═══════════════════════════════════════════════════════

def calculate_margin_of_safety(
    intrinsic_value: float,
    current_price: float,
    sector: str | None = None,
) -> dict[str, Any]:
    """
    Hitung Margin of Safety (MoS) sesuai prinsip Benjamin Graham.

    Rumus: MoS = (Intrinsic Value - Current Price) / Intrinsic Value
    Threshold LULUS: MoS >= 25% (Standar Margin of Safety Graham)
    """
    cfg = get_threshold("margin_of_safety", sector)
    min_mos = cfg.get("min_mos", 0.25)

    if intrinsic_value <= 0 or current_price <= 0:
        return {
            "value": 0.0,
            "pass_fail": False,
            "threshold": cfg.get("label", ">= 25%"),
            "intrinsic_value": intrinsic_value,
            "current_price": current_price,
            "status_label": "Tidak dapat dihitung",
        }

    mos = (intrinsic_value - current_price) / intrinsic_value
    passed = mos >= min_mos

    if mos >= 0.25:
        status_label = "Undervalued (Aman)"
    elif mos > 0:
        status_label = "Fair Value (MoS Tipis)"
    else:
        status_label = "Overvalued (Mahal)"

    return {
        "value": mos,
        "pass_fail": passed,
        "threshold": cfg.get("label", ">= 25%"),
        "intrinsic_value": intrinsic_value,
        "current_price": current_price,
        "status_label": status_label,
    }


# ═══════════════════════════════════════════════════════
# UTIL — PROYEKSI FUTURE VALUE REKURSIF
# ═══════════════════════════════════════════════════════

def project_future_value_recurrence(
    initial_value: float,
    growth_rate: float,
    periods: int,
    start_year: int | None = None,
) -> list[dict[str, Any]]:
    """
    Proyeksi nilai masa depan menggunakan relasi rekurensi dengan tahun kalender.
    FV[n] = FV[n-1] × (1 + growth_rate)
    """
    if not start_year:
        start_year = datetime.now().year

    projections = [{"period": 0, "year": str(start_year), "value": initial_value}]
    current = initial_value
    for n in range(1, periods + 1):
        current = current * (1.0 + growth_rate)
        projections.append({"period": n, "year": str(start_year + n), "value": current})
    return projections
