"""
valuation.py — Mesin kalkulasi valuasi intrinsik perusahaan.

Menghitung:
1. Intrinsic Value via Discounted Cash Flow (DCF)
2. Proyeksi Future Value via relasi rekurensi
3. Margin of Safety
"""

import numpy as np


def calculate_dcf(
    free_cash_flows: list[float],
    discount_rate: float,
    growth_rate: float,
    terminal_growth: float = 0.03,
    shares_outstanding: float | None = None,
) -> dict:
    """
    Hitung Intrinsic Value via Discounted Cash Flow (Two-Stage Model).

    Rumus:
        Tahap 1 — Explicit Period (5 tahun):
            Projected_FCF[t] = FCF_terakhir × (1 + growth_rate)^t
            PV[t] = Projected_FCF[t] / (1 + discount_rate)^t

        Tahap 2 — Terminal Value (Gordon Growth Model):
            Terminal_FCF = Projected_FCF[5] × (1 + terminal_growth)
            Terminal_Value = Terminal_FCF / (discount_rate - terminal_growth)
            PV_Terminal = Terminal_Value / (1 + discount_rate)^5

        Enterprise Value = Σ PV[t] + PV_Terminal
        Intrinsic Value per Share = EV / shares_outstanding
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


def project_future_value_recurrence(
    initial_value: float, growth_rate: float, periods: int,
) -> list[dict]:
    """
    Proyeksi nilai masa depan menggunakan relasi rekurensi.

    Relasi Rekurensi:
        FV[0] = initial_value
        FV[n] = FV[n-1] × (1 + growth_rate),  untuk n = 1..periods

    Solusi tertutup: FV[n] = initial_value × (1 + growth_rate)^n
    Implementasi menggunakan bentuk iteratif untuk transparansi langkah.
    """
    projections = [{"period": 0, "value": initial_value}]
    current = initial_value
    for n in range(1, periods + 1):
        current = current * (1 + growth_rate)
        projections.append({"period": n, "value": current})
    return projections


def calculate_margin_of_safety(intrinsic_value: float, current_price: float) -> dict:
    """
    Hitung Margin of Safety (MoS).

    Rumus: MoS = (Intrinsic Value - Current Price) / Intrinsic Value

    Interpretasi:
        MoS > 0  → Undervalued
        MoS ≤ 0  → Overvalued

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
