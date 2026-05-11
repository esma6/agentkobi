from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")


def _compact_payload(
    order_data: dict[str, Any],
    stock_data: list[dict[str, Any]],
    supplier_drafts: list[dict[str, Any]],
    rag_context: list[str],
) -> dict[str, Any]:
    return {
        "order_data": order_data,
        "stock_data": stock_data[:5],
        "supplier_drafts": supplier_drafts[:3],
        "rag_context": rag_context[:3],
    }


def _build_prompt(payload: dict[str, Any]) -> str:
    return f"""
Sen AgentKobi'nin sabah brifingi yazan AI ajanısın.

Görev:
- KOBİ sahibine kısa, net, aksiyon odaklı Türkçe sabah brifingi yaz.
- Metin "Günaydın!" ile başlasın.
- En fazla 5 cümle yaz.
- Markdown, başlık, madde işareti ve emoji kullanma.
- Sadece aşağıdaki JSON verisindeki sayıları kullan.
- Tahmin, yeni sayı, maliyet, teslim tarihi veya takip numarası uydurma.
- Stok için ürün adı, mevcut miktar ve birim söyleyebilirsin.
- Tedarikçi taslakları varsa sadece onay beklediğini ve mümkünse ürün/sipariş miktarını söyle.
- Veri yoksa sakin gün brifingi yaz.

JSON veri:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


async def run(
    order_data: dict,
    stock_data: list[dict],
    supplier_drafts: list[dict],
    rag_context: list[str],
) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY tanımlı değil")

    model = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,
    )
    payload = _compact_payload(order_data, stock_data, supplier_drafts, rag_context)
    response = await llm.ainvoke(_build_prompt(payload))
    content = getattr(response, "content", response)
    if isinstance(content, list):
        content = " ".join(str(part) for part in content)
    return str(content).strip()
