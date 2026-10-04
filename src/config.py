"""
config.py — Konfigurasi sentral parameter & threshold 9 Pilar Value Investing.

Semua konstanta finansial, asumsi diskonto, pajak, dan threshold sektoral
dikelola di sini agar tidak ada 'magic numbers' di engine atau UI.
"""

from typing import Any

# ═══════════════════════════════════════════════════════
# KONSTANTA MAKRO & ASUMSI VALUASI
# ═══════════════════════════════════════════════════════

# Tarif PPh Badan Indonesia (UU HPP No. 7/2021)
DEFAULT_CORPORATE_TAX_RATE: float = 0.22

# Parameter DCF Default
DEFAULT_DISCOUNT_RATE: float = 0.10       # 10% Required Rate of Return
DEFAULT_GROWTH_RATE: float = 0.08         # 8% Proyeksi pertumbuhan konservatif
DEFAULT_TERMINAL_GROWTH: float = 0.03     # 3% Pertumbuhan jangka panjang (~GDP Indonesia konservatif)
DEFAULT_PROJECTION_YEARS: int = 5         # Periode proyeksi eksplisit (tahun)

# Konsistensi Historis
MIN_CONSISTENCY_RATIO: float = 0.60       # Minimal 60% tahun mencatat pertumbuhan positif

# ═══════════════════════════════════════════════════════
# THRESHOLD STANDARD 9 PILAR (GENERAL / NON-FINANCIAL)
# ═══════════════════════════════════════════════════════

STANDARD_THRESHOLDS: dict[str, dict[str, Any]] = {
    "profitabilitas": {
        "min_npm": 0.05,                  # Net Profit Margin > 5%
        "label": "> 5%",
    },
    "revenue_growth": {
        "min_yoy": 0.0,                   # YoY > 0%
        "min_consistency": 0.60,          # >= 60% periode bertumbuh
        "label": "> 0% (Konsisten >=60%)",
    },
    "profit_growth": {
        "min_yoy": 0.0,
        "min_consistency": 0.60,
        "label": "> 0% (Konsisten >=60%)",
    },
    "cashflow_growth": {
        "min_yoy": 0.0,
        "min_consistency": 0.60,
        "label": "> 0% (Konsisten >=60%)",
    },
    "roe": {
        "min_roe": 0.15,                  # Standar Warren Buffett (>= 15%)
        "max_leverage_ratio": 2.5,        # Aset/Ekuitas > 2.5 memicu warning leverage-driven ROE
        "label": ">= 15%",
    },
    "roic": {
        "min_roic": 0.10,                 # ROIC > 10% (di atas perkiraan WACC)
        "label": "> 10%",
    },
    "debt_health": {
        "max_de": 1.0,                    # Debt to Equity < 1.0x
        "max_da": 0.5,                    # Debt to Assets < 0.5x
        "min_icr": 3.0,                   # Interest Coverage Ratio > 3.0x
        "label": "D/E < 1.0x",
    },
    "growth_cagr": {
        "min_cagr": 0.05,                 # CAGR > 5%
        "label": "> 5%",
    },
    "intrinsic_value": {
        "label": "DCF > Harga Pasar",
    },
    "margin_of_safety": {
        "min_mos": 0.25,                  # Standar Benjamin Graham (>= 25%)
        "label": ">= 25%",
    },
}

# ═══════════════════════════════════════════════════════
# SECTOR OVERRIDES (PENYESUAIAN KARAKTERISTIK INDUSTRI)
# ═══════════════════════════════════════════════════════

SECTOR_OVERRIDES: dict[str, dict[str, Any]] = {
    "Financials": {
        # Bank & institusi keuangan beroperasi dengan leverage tinggi (dana pihak ketiga = liabilitas)
        "debt_health": {
            "max_de": 8.0,
            "max_da": 0.90,
            "min_icr": 0.0,
            "label": "D/E < 8.0x (Sektor Finansial)",
            "is_bank": True,
        },
        "roic": {
            "min_roic": 0.08,
            "label": "> 8% (Finansial)",
            "is_bank": True,
        },
    },
    "Infrastructures": {
        # Proyek infrastruktur / utilitas padat modal & modal hutang jangka panjang
        "debt_health": {
            "max_de": 2.0,
            "max_da": 0.65,
            "min_icr": 2.0,
            "label": "D/E < 2.0x (Infrastruktur)",
        },
    },
    "Real Estate": {
        "debt_health": {
            "max_de": 1.5,
            "max_da": 0.60,
            "min_icr": 2.0,
            "label": "D/E < 1.5x (Properti)",
        },
    },
}


def normalize_sector(sector: str | None) -> str:
    """Normalisasi string sektor dari API ke grup sektor standar."""
    if not sector:
        return "General"
    s = sector.strip().lower()
    if any(k in s for k in ["financial", "bank", "keuangan"]):
        return "Financials"
    if any(k in s for k in ["infra", "utility", "telecommunication", "toll"]):
        return "Infrastructures"
    if any(k in s for k in ["real estate", "property", "properti"]):
        return "Real Estate"
    return "General"


def get_threshold(pilar: str, sector: str | None = None) -> dict[str, Any]:
    """
    Ambil threshold untuk pilar tertentu, disesuaikan dengan sektor industri jika relevan.
    """
    base = STANDARD_THRESHOLDS.get(pilar, {}).copy()
    norm_sector = normalize_sector(sector)

    if norm_sector in SECTOR_OVERRIDES and pilar in SECTOR_OVERRIDES[norm_sector]:
        base.update(SECTOR_OVERRIDES[norm_sector][pilar])

    return base
