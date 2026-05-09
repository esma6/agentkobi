@'
"""LLM çıktısındaki sayıları regex ile çıkarır."""
from __future__ import annotations

import re

# Türkçe metinde geçecek olası sayı formatları:
#   "12 yeni sipariş", "30 kg", "5 paket"
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")


def extract_numbers(text: str) -> set[float]:
    """Metindeki tüm sayıları float seti olarak döner."""
    out: set[float] = set()
    for m in NUMBER_PATTERN.findall(text):
        try:
            out.add(float(m.replace(",", ".")))
        except ValueError:
            continue
    return out
'@ | Set-Content -Path backend/app/validators/number_extractor.py -Encoding UTF8