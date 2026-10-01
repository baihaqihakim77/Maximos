"""
formatter.py — Utilitas format angka untuk tampilan dashboard.

Semua angka finansial mentah (bukan persen) yang ditampilkan ke user
WAJIB melewati modul ini agar konsisten.
"""


def format_rupiah(value: float) -> str:
    """
    Format angka menjadi format Rupiah Indonesia.

    Contoh:
        format_rupiah(1500000)   → "Rp 1.500.000"
        format_rupiah(-300000.5) → "-Rp 300.001"

    Args:
        value: Nilai numerik yang akan diformat.

    Returns:
        String dalam format "Rp X.XXX.XXX".
    """
    if value is None:
        return "Rp 0"

    is_negative = value < 0
    abs_value = abs(value)
    rounded = int(round(abs_value))
    formatted = f"{rounded:,}".replace(",", ".")
    prefix = "-Rp " if is_negative else "Rp "
    return f"{prefix}{formatted}"


def format_rupiah_short(value: float) -> str:
    """
    Format angka besar menjadi format Rupiah ringkas (Miliar/Triliun).

    Contoh:
        format_rupiah_short(1_500_000_000_000) → "Rp 1,50 T"
        format_rupiah_short(750_000_000)       → "Rp 750,00 M"
    """
    if value is None:
        return "Rp 0"

    is_negative = value < 0
    abs_value = abs(value)
    prefix = "-Rp " if is_negative else "Rp "

    if abs_value >= 1_000_000_000_000:
        num = abs_value / 1_000_000_000_000
        return f"{prefix}{num:,.2f} T".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs_value >= 1_000_000_000:
        num = abs_value / 1_000_000_000
        return f"{prefix}{num:,.2f} M".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs_value >= 1_000_000:
        num = abs_value / 1_000_000
        return f"{prefix}{num:,.2f} Jt".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return format_rupiah(value)


def format_percent(value: float) -> str:
    """
    Format angka desimal menjadi format persen Indonesia.

    Contoh:
        format_percent(0.1523)  → "15,23%"
        format_percent(-0.05)   → "-5,00%"
    """
    if value is None:
        return "0,00%"

    persen = value * 100
    formatted = f"{persen:.2f}".replace(".", ",")
    return f"{formatted}%"
