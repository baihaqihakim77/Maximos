"""
llm_api.py — Layanan koneksi ke LLM API (Google Gemini) dan fallback narasi.

Jika LLM gagal/timeout, fallback_narrative() menghasilkan narasi template
statis berbasis kondisi skor tanpa ketergantungan API eksternal.
"""

import os
from typing import Any

from google import genai


_LLM_TIMEOUT = 45

_PILAR_NAMES = {
    "profitabilitas": "Profitabilitas (NPM)",
    "revenue_growth": "Pertumbuhan Pendapatan (YoY)",
    "profit_growth": "Pertumbuhan Laba Bersih (YoY)",
    "cashflow_growth": "Pertumbuhan Arus Kas (FCF/CFO)",
    "roic_roe": "Efisiensi Modal (ROIC & ROE)",
    "debt_health": "Kesehatan Hutang (D/E, D/A, ICR)",
    "growth_cagr": "Pertumbuhan Majemuk (CAGR)",
    "intrinsic_value": "Nilai Intrinsik (DCF Model)",
    "margin_of_safety": "Margin of Safety (MoS)",
}


def _build_prompt(pilar_scores: dict[str, dict[str, Any]]) -> str:
    """Bangun prompt untuk LLM berdasarkan skor 10 pilar."""
    total = len(pilar_scores)
    passed = sum(1 for v in pilar_scores.values() if v.get("pass_fail", False))

    detail_lines = []
    for key, data in pilar_scores.items():
        nama = _PILAR_NAMES.get(key, key)
        status = "✅ LULUS" if data.get("pass_fail", False) else "❌ GAGAL"
        value = data.get("value", "N/A")
        threshold = data.get("threshold", "N/A")
        detail_lines.append(f"- {nama}: {value} (threshold: {threshold}) → {status}")

    detail_text = "\n".join(detail_lines)

    return f"""Kamu adalah seorang analis keuangan profesional yang merangkum
hasil analisis fundamental saham untuk investor awam.

Skor keseluruhan: {passed}/{total} pilar LULUS

Detail per pilar:
{detail_text}

Tugasmu:
1. Ringkasan kondisi fundamental dalam 2-3 paragraf.
2. Bahasa Indonesia yang mudah dipahami investor pemula.
3. Sebutkan kekuatan dan kelemahan utama.
4. Kesimpulan apakah layak dipertimbangkan dari sisi value investing.
5. Ingatkan bahwa ini analisis kuantitatif, perlu riset kualitatif.

Gaya: profesional namun ramah, seperti analis menjelaskan ke klien retail."""


def generate_narrative(pilar_scores: dict[str, dict[str, Any]]) -> str:
    """
    Kirim skor 10 pilar ke Gemini API dan kembalikan narasi analis virtual.

    Raises:
        Exception: Jika Gemini API gagal/timeout/key tidak valid.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    if not api_key:
        raise ValueError("GEMINI_API_KEY belum dikonfigurasi.")

    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(pilar_scores)

    system_instruction = (
        "Kamu adalah analis keuangan profesional Indonesia yang "
        "ahli value investing. Jawab dalam Bahasa Indonesia."
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=1024,
        ),
    )

    return response.text or ""


def fallback_narrative(pilar_scores: dict[str, dict[str, Any]]) -> str:
    """
    Hasilkan narasi template statis berbasis kondisi skor (tanpa AI).

    Logika:
        - Skor ≥ 8/10 → sangat positif
        - Skor 5-7/10 → campuran
        - Skor < 5/10 → waspada
    """
    total = len(pilar_scores) if pilar_scores else 10
    passed = sum(1 for v in pilar_scores.values() if v.get("pass_fail", False))
    failed = total - passed

    pilar_lulus = []
    pilar_gagal = []
    for key, data in pilar_scores.items():
        nama = _PILAR_NAMES.get(key, key)
        if data.get("pass_fail", False):
            pilar_lulus.append(nama)
        else:
            pilar_gagal.append(nama)

    lulus_text = ", ".join(pilar_lulus) if pilar_lulus else "tidak ada"
    gagal_text = ", ".join(pilar_gagal) if pilar_gagal else "tidak ada"

    # Kalibrasi threshold untuk sistem 9 pilar
    if passed >= 7:
        ringkasan = (
            f"Mayoritas pilar menunjukkan kondisi fundamental yang **sangat sehat**. "
            f"Dari {total} pilar, **{passed} LULUS** dan {failed} belum memenuhi threshold.\n\n"
            f"**Kekuatan utama:** {lulus_text}.\n\n"
        )
        if pilar_gagal:
            ringkasan += f"**Perlu perhatian:** {gagal_text}.\n\n"
        ringkasan += (
            "Secara keseluruhan, profil value investing menarik dengan margin keamanan memadai. Namun perlu "
            "dilengkapi analisis kualitatif terhadap manajemen dan prospek industri."
        )
        action = "Buy"
    elif passed >= 5:
        ringkasan = (
            f"Perusahaan menunjukkan kinerja **campuran** yang moderat. "
            f"Dari {total} pilar, **{passed} LULUS** sementara {failed} belum memenuhi.\n\n"
            f"**Kekuatan:** {lulus_text}.\n\n"
            f"**Kelemahan:** {gagal_text}.\n\n"
            "Investor sebaiknya menganalisis lebih lanjut apakah hambatan "
            "bersifat sementara atau terdapat perubahan struktural."
        )
        action = "Hold"
    else:
        ringkasan = (
            f"⚠️ Mayoritas pilar menunjukkan **kelemahan fundamental** yang signifikan. "
            f"Dari {total} pilar, hanya **{passed} LULUS** sementara {failed} belum memenuhi standar.\n\n"
            f"**Kekuatan terbatas:** {lulus_text}.\n\n"
            f"**Kelemahan dominan:** {gagal_text}.\n\n"
            "Disarankan kehati-hatian ekstra atau mencari alternatif emiten dengan valuasi dan kesehatan neraca lebih baik."
        )
        action = "Avoid"

    return ringkasan, action
