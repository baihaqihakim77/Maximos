"""
sectors_api.py — Layanan koneksi ke Sectors REST API v2.

Semua konfigurasi API (base URL, key) diambil dari environment variable (.env).
Tidak ada kredensial atau endpoint yang di-hardcode di file ini.
"""

import os
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests


# Semua konfigurasi API dari .env
_BASE_URL = os.getenv("SECTORS_BASE_URL", "https://api.sectors.app/v2")
_TIMEOUT = 30


def _get_headers() -> dict[str, str]:
    """Bangun header Authorization dari environment variable."""
    api_key = os.getenv("SECTORS_API_KEY", "")
    if not api_key:
        raise ValueError(
            "SECTORS_API_KEY belum diatur. "
            "Silakan isi di file .env atau environment variable."
        )
    return {"Authorization": api_key}


def _handle_response(response: requests.Response, ticker: str = "") -> Any:
    """
    Proses response API dan tangani error umum.

    Raises:
        ConnectionError: Jika terjadi error koneksi atau rate limit.
        ValueError: Jika response bukan JSON valid atau ticker tidak ditemukan.
    """
    if response.status_code == 429:
        raise ConnectionError("Rate limit Sectors API tercapai. Tunggu beberapa saat.")
    if response.status_code == 401:
        raise ConnectionError("API key tidak valid. Periksa SECTORS_API_KEY di .env.")
    if response.status_code == 404:
        label = f"'{ticker}' " if ticker else ""
        raise ValueError(
            f"Ticker {label}tidak ditemukan di Sectors API. "
            "Pastikan kode saham benar dan terdaftar di Bursa Efek Indonesia."
        )
    if response.status_code != 200:
        raise ConnectionError(f"Error Sectors API: HTTP {response.status_code} — {response.text[:200]}")

    try:
        return response.json()
    except Exception as e:
        raise ValueError(f"Response bukan JSON valid: {e}")


def get_company_report(ticker: str) -> dict[str, Any]:
    """
    Ambil laporan fundamental perusahaan dari Sectors API v2.

    Args:
        ticker: Kode saham (misal "BBCA"). Mendukung format dengan atau tanpa ".jk".

    Returns:
        Dict berisi data laporan fundamental perusahaan.
    """
    # v2: ticker sebagai path parameter, bukan query param
    url = f"{_BASE_URL}/company/report/{ticker}/"
    params = {
        "sections": "overview,financials,valuation,future",
    }

    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=_TIMEOUT)
        return _handle_response(response, ticker)
    except requests.exceptions.Timeout:
        raise ConnectionError("Koneksi ke Sectors API timeout.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Gagal terhubung ke Sectors API.")


def get_financial_statements(ticker: str) -> dict[str, pd.DataFrame]:
    """
    Ambil data keuangan historis dan konversi ke DataFrame.

    Di v2, semua data keuangan ada di satu endpoint company/report dengan
    section 'financials' → field 'historical_financials' (flat list per tahun).

    Returns:
        Dict dengan key: "income_statement", "balance_sheet", "cash_flow"
        Semua merujuk ke DataFrame yang sama (historical_financials) karena
        v2 menggabungkan semua dalam satu tabel flat.
    """
    url = f"{_BASE_URL}/company/report/{ticker}/"
    params = {"sections": "financials"}

    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=_TIMEOUT)
        data = _handle_response(response, ticker)
    except requests.exceptions.Timeout:
        raise ConnectionError("Timeout saat mengambil laporan keuangan.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Gagal terhubung untuk laporan keuangan.")

    # v2 structure: data["financials"]["historical_financials"] → list of yearly dicts
    hist = data.get("financials", {}).get("historical_financials", [])
    df = pd.DataFrame(hist) if hist else pd.DataFrame()

    # Semua financial data ada dalam satu flat DataFrame di v2
    # Mapping field v2 ke key yang dipakai oleh engine/*
    result = {
        "income_statement": df,   # revenue, earnings, operating_pnl, ...
        "balance_sheet": df,      # total_assets, total_equity, total_liabilities, ...
        "cash_flow": df,          # free_cash_flow, operating_cash_flow, ...
    }

    return result


def get_historical_price(ticker: str) -> pd.DataFrame:
    """
    Ambil data harga historis saham untuk grafik.

    Catatan v2: max window 90 hari per request. Ambil 90 hari terakhir.

    Returns:
        DataFrame dengan kolom: date, close.
    """
    # v2 max 90 hari — ambil 90 hari terakhir
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=89)).strftime("%Y-%m-%d")

    url = f"{_BASE_URL}/daily/{ticker}/"
    params = {"start": start_date, "end": end_date}

    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=_TIMEOUT)
        data = _handle_response(response, ticker)
    except requests.exceptions.Timeout:
        raise ConnectionError("Timeout saat mengambil harga historis.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Gagal terhubung untuk harga historis.")

    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        if "date" not in df.columns and "Date" in df.columns:
            df = df.rename(columns={"Date": "date"})
        if "close" not in df.columns and "Close" in df.columns:
            df = df.rename(columns={"Close": "close"})
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
        return df
    else:
        return pd.DataFrame(columns=["date", "close"])
