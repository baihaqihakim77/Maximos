# 📊 Value Investing Dashboard

**Dashboard analisis fundamental saham interaktif** berbasis Python & Streamlit
yang mengotomatisasi evaluasi 10 pilar utama value investing secara instan.

Aplikasi menarik data laporan keuangan dari **Sectors REST API**, memproses data
melalui mesin kalkulasi finansial (Pandas & NumPy), lalu menampilkan scorecard
visual dan grafik proyeksi interaktif (Plotly). Hasil analisis dirangkum oleh
**LLM** sebagai "analis virtual" menjadi narasi yang mudah dicerna investor awam.

---

## 🚀 Instalasi

```bash
cd value_investing_dashboard
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## ▶️ Menjalankan

```bash
# Edit .env → isi SECTORS_API_KEY (wajib) dan LLM_API_KEY (opsional)
streamlit run app.py
```

---

## 📐 10 Pilar Analisis

| # | Pilar | Deskripsi Singkat |
|---|-------|-------------------|
| 1 | **Profitabilitas** | Net Profit Margin & Gross Margin |
| 2 | **Revenue Growth** | Pertumbuhan pendapatan YoY |
| 3 | **Profit Growth** | Pertumbuhan laba bersih YoY |
| 4 | **Cash Flow Growth** | Pertumbuhan arus kas operasi YoY |
| 5 | **ROIC / ROE** | Return on Invested Capital & Equity |
| 6 | **Debt Health** | Rasio Debt-to-Equity |
| 7 | **Growth CAGR** | Compound Annual Growth Rate multi-tahun |
| 8 | **Efisiensi Manajemen** | Proxy via Asset Turnover & margin trend |
| 9 | **Intrinsic Value (DCF)** | Valuasi intrinsik via Discounted Cash Flow |
| 10 | **Margin of Safety** | Selisih harga pasar vs nilai intrinsik |

---

## 🛡️ Arsitektur Fallback LLM

1. Skor 10 pilar dikirim ke LLM API untuk narasi.
2. Jika LLM **gagal/timeout**, `fallback_narrative()` menghasilkan narasi template
   statis berbasis kondisi skor.
3. **Seluruh hasil kalkulasi, scorecard, dan grafik tetap ditampilkan sempurna.**

---

## 📁 Struktur Proyek

```
value_investing_dashboard/
├── .env                    # API keys
├── .gitignore
├── requirements.txt
├── README.md
├── app.py                  # Entry point Streamlit
└── src/
    ├── services/
    │   ├── sectors_api.py  # Koneksi Sectors REST API
    │   └── llm_api.py      # Koneksi LLM + fallback
    ├── engine/
    │   ├── growth.py       # Kalkulasi pertumbuhan & CAGR
    │   ├── health.py       # ROE/ROIC, D/E, efisiensi
    │   └── valuation.py    # DCF, proyeksi rekurensi, MoS
    ├── ui/
    │   ├── sidebar.py      # Input ticker (autocomplete)
    │   ├── scorecard.py    # Grid visual 10 pilar
    │   └── charts.py       # Grafik Plotly & SVG sparklines
    └── utils/
        └── formatter.py    # Format Rupiah & persen
```
