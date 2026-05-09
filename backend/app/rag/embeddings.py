"""
Embedding wrapper.

Default: HuggingFace 'sentence-transformers/all-MiniLM-L6-v2'
(384-dim, lokal, ücretsiz, hızlı). Türkçe için ideal değil ama
demo için yeter. Production'da 'intfloat/multilingual-e5-base'
veya 'BAAI/bge-m3' tercih edilebilir.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embeddings(model_name: str = DEFAULT_MODEL) -> HuggingFaceEmbeddings:
    """Singleton embedding instance."""
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
