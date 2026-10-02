"""
sidebar.py — Komponen input ticker saham (tanpa sidebar).

Menampilkan selectbox dengan autocomplete di bagian atas halaman.
User mengetik kode saham, sistem menampilkan rekomendasi, lalu user klik.
"""

import streamlit as st


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
    Render input ticker di bagian atas halaman (BUKAN sidebar).

    User bisa mengetik untuk mencari saham, sistem menampilkan rekomendasi.
    Klik saham untuk memilih, lalu klik tombol ANALYSIS.

    Returns:
        Dict: {"ticker": str, "company_name": str, "discount_rate": float,
               "growth_rate": float, "projection_years": int, "analyze": bool}
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
        analyze = st.button("📊  ANALYSIS", use_container_width=True, type="primary")

    company_name = INDONESIAN_STOCKS.get(ticker, ticker) if ticker else ""

    # Default parameter
    discount_rate = 0.10
    growth_rate = 0.08
    projection_years = 10

    return {
        "ticker": ticker.strip().upper() if ticker else "",
        "company_name": company_name,
        "discount_rate": discount_rate,
        "growth_rate": growth_rate,
        "projection_years": int(projection_years),
        "analyze": analyze,
    }
