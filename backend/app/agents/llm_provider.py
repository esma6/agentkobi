from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _build_groq(temperature: float = 0.1):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        logger.warning("langchain_groq import edilemedi: %s", exc)
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(model=model, api_key=api_key, temperature=temperature)


def _build_gemini(temperature: float = 0.1):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        logger.warning("langchain_google_genai import edilemedi: %s", exc)
        return None
    model = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
    )


def get_llm(temperature: float = 0.1):
    """Önce Groq, başarısız olursa Gemini döner.

    Tüm agent'ların ortak LLM giriş noktasıdır; sağlayıcı önceliği:
    1) GROQ_API_KEY varsa Groq
    2) GOOGLE_API_KEY varsa Gemini
    """
    llm = _build_groq(temperature=temperature)
    if llm is not None:
        logger.info("LLM sağlayıcı: groq")
        return llm
    llm = _build_gemini(temperature=temperature)
    if llm is not None:
        logger.info("LLM sağlayıcı: gemini (fallback)")
        return llm
    raise RuntimeError(
        "Hiçbir LLM API key tanımlı değil (GROQ_API_KEY veya GOOGLE_API_KEY)."
    )
