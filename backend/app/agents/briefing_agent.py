from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class BriefingOutput(BaseModel):
    briefing: str = Field(description="KOBİ sahibine yazılmış aksiyon odaklı Türkçe brifing metni.")



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


def _build_groq_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        logger.warning("langchain_groq import edilemedi: %s", exc)
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(model=model, api_key=api_key, temperature=0.2)


def _build_gemini_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,
    )


async def _invoke_llm(llm, prompt: str) -> str:
    """Önce structured output dene; desteklemiyorsa düz metin parse et."""
    try:
        structured = llm.with_structured_output(BriefingOutput)
        response = await structured.ainvoke(prompt)
        return str(response.briefing).strip()
    except Exception as exc:
        logger.info("Structured output başarısız (%s), düz metin deneniyor.", exc)
        response = await llm.ainvoke(prompt)
        content = getattr(response, "content", response)
        return str(content).strip()


async def run(
    order_data: dict,
    stock_data: list[dict],
    supplier_drafts: list[dict],
    rag_context: list[str],
) -> str:
    payload = _compact_payload(order_data, stock_data, supplier_drafts, rag_context)
    prompt = _build_prompt(payload)

    # Sırayla dene: Groq (öncelikli) -> Gemini (yedek)
    providers = [
        ("groq", _build_groq_llm),
        ("gemini", _build_gemini_llm),
    ]

    errors: list[str] = []
    for name, builder in providers:
        llm = builder()
        if llm is None:
            errors.append(f"{name}: api key/SDK yok")
            continue
        try:
            text = await _invoke_llm(llm, prompt)
            if text:
                logger.info("Brifing %s sağlayıcısı ile üretildi.", name)
                return text
            errors.append(f"{name}: boş cevap")
        except Exception as exc:
            logger.warning("%s sağlayıcısı başarısız: %s", name, exc)
            errors.append(f"{name}: {type(exc).__name__}: {exc}")

    raise RuntimeError("Tüm LLM sağlayıcıları başarısız: " + " | ".join(errors))
