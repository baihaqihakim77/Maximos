"""
sidebar.py — Komponen input ticker saham dan parameter valuasi.

Menampilkan selectbox dengan autocomplete di bagian atas halaman,
serta accordion pengaturan parameter valuasi DCF (tanpa angka hardcode).
"""

import streamlit as st

from src.config import (
    DEFAULT_DISCOUNT_RATE,
    DEFAULT_GROWTH_RATE,
    DEFAULT_PROJECTION_YEARS,
    DEFAULT_TERMINAL_GROWTH,
)


# Daftar saham Indonesia populer untuk autocomplete
INDONESIAN_STOCKS: dict[str, str] = {
    "BBCA": "Bank Central Asia",
    "BBRI": "Bank Rakyat Indonesia",
    "BMRI": "Bank Mandiri",
    "BBNI": "Bank Negara Indonesia",
    "BRIS": "Bank Syariah Indonesia",
    "ARTO": "Bank Jago",
    "TLKM": "Telkom Indonesia",
    "ASII": "Astra International",
    "UNVR": "Unilever Indonesia",
    "HMSP": "HM Sampoerna",
    "GGRM": "Gudang Garam",
    "ICBP": "Indofood CBP Sukses Makmur",
    "INDF": "Indofood Sukses Makmur",
    "KLBF": "Kalbe Farma",
    "PGAS": "Perusahaan Gas Negara",
    "SMGR": "Semen Indonesia",
    "JSMR": "Jasa Marga",
    "ADRO": "Adaro Energy Indonesia",
    "PTBA": "Bukit Asam",
    "ANTM": "Aneka Tambang",
    "INCO": "Vale Indonesia",
    "UNTR": "United Tractors",
    "CPIN": "Charoen Pokphand Indonesia",
    "JPFA": "Japfa Comfeed Indonesia",
    "MNCN": "MNC Media",
    "EXCL": "XL Axiata",
    "ISAT": "Indosat Ooredoo Hutchison",
    "TOWR": "Sarana Menara Nusantara",
    "TBIG": "Tower Bersama Infrastructure",
    "ACES": "Ace Hardware Indonesia",
    "MAPI": "Mitra Adiperkasa",
    "BSDE": "Bumi Serpong Damai",
    "CTRA": "Ciputra Development",
    "SMRA": "Summarecon Agung",
    "PWON": "Pakuwon Jati",
    "ERAA": "Erajaya Swasembada",
    "SCMA": "Surya Citra Media",
    "SIDO": "Industri Jamu Sido Muncul",
    "MDKA": "Merdeka Copper Gold",
    "EMTK": "Elang Mahkota Teknologi",
    "GOTO": "GoTo Gojek Tokopedia",
    "BUKA": "Bukalapak.com",
    "ESSA": "Surya Esa Perkasa",
    "AMMN": "Amman Mineral Internasional",
    "BRPT": "Barito Pacific",
    "INKP": "Indah Kiat Pulp & Paper",
    "TKIM": "Pabrik Kertas Tjiwi Kimia",
}


def render_ticker_input() -> dict:
    """
    Render input ticker di bagian atas halaman beserta pengaturan parameter DCF.

    User bisa mengetik untuk mencari saham, sistem menampilkan rekomendasi.
    Klik saham untuk memilih, lalu klik tombol ANALYZE.

    Returns:
        Dict: {
            "ticker": str,
            "company_name": str,
            "discount_rate": float,
            "growth_rate": float,
            "terminal_growth": float,
            "projection_years": int,
            "analyze": bool,
        }
    """
    # Layout: selectbox + tombol di baris yang sama
    col_select, col_btn = st.columns([3, 1])

    with col_select:
        ticker = st.selectbox(
            "Pilih Saham",
            options=list(INDONESIAN_STOCKS.keys()),
            format_func=lambda x: f"{x}  —  {INDONESIAN_STOCKS.get(x, '')}",
            index=0,
            label_visibility="collapsed",
            placeholder="Ketik kode saham (misal: BBCA, TLKM)...",
        )

    with col_btn:
        analyze = st.button("ANALYZE", use_container_width=True, type="primary")

    company_name = INDONESIAN_STOCKS.get(ticker, ticker) if ticker else ""

    # Accordion Pengaturan Parameter Valuasi DCF
    with st.expander("⚙️ Parameter Valuasi DCF (Opsional)", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            discount_pct = st.slider(
                "Discount Rate (WACC)",
                min_value=6.0,
                max_value=20.0,
                value=float(DEFAULT_DISCOUNT_RATE * 100),
                step=0.5,
                format="%.1f%%",
                help="Tingkat pengembalian minimal yang diharapkan investor (Hurdle Rate).",
            )
        with c2:
            growth_pct = st.slider(
                "Growth Rate (FCF)",
                min_value=0.0,
                max_value=25.0,
                value=float(DEFAULT_GROWTH_RATE * 100),
                step=0.5,
                format="%.1f%%",
                help="Estimasi pertumbuhan tahunan arus kas bebas selama fase eksplisit.",
            )
        with c3:
            terminal_pct = st.slider(
                "Terminal Growth Rate",
                min_value=1.0,
                max_value=5.0,
                value=float(DEFAULT_TERMINAL_GROWTH * 100),
                step=0.25,
                format="%.2f%%",
                help="Tingkat pertumbuhan jangka panjang abadi (~pertumbuhan ekonomi nasional).",
            )
        with c4:
            proj_years = st.slider(
                "Projection Years",
                min_value=3,
                max_value=10,
                value=int(DEFAULT_PROJECTION_YEARS),
                step=1,
                help="Jumlah tahun periode proyeksi eksplisit sebelum nilai terminal.",
            )

    return {
        "ticker": ticker.strip().upper() if ticker else "",
        "company_name": company_name,
        "discount_rate": discount_pct / 100.0,
        "growth_rate": growth_pct / 100.0,
        "terminal_growth": terminal_pct / 100.0,
        "projection_years": int(proj_years),
        "analyze": analyze,
    }
