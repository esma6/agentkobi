"""
Conditional routing fonksiyonları.

LangGraph'te koşullu kenarlar (conditional edges) düz Python
fonksiyonlarıdır: state'i okurlar, hangi node'a gidileceğinin
adını string olarak döndürürler.
"""
from __future__ import annotations

from app.graph.state import AgentState


def route_after_aggregator(state: AgentState) -> str:
    """
    Sakin günse RAG ve LLM atlanabilir; doğrudan validator'a git.
    Aksi halde RAG -> LLM -> validator yoluna devam.
    """
    if state.get("is_quiet_day"):
        return "briefing_llm"  # quiet day template'i orada üretilir
    return "rag"


def route_after_validator(state: AgentState) -> str:
    """
    Validator geçtiyse: END.
    Geçmediyse zaten template'e düşmüş, yine END (retry yok — demo için sade).
    İleride: requires_human_review True olursa human-in-the-loop'a yönlendir.
    """
    if state.get("requires_human_review"):
        return "human_review"
    return "END"
