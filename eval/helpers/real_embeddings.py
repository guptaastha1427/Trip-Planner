"""Real embeddings for evaluation and tests (HuggingFace or Gemini — never dummy vectors)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Optional, Tuple

from langchain_community.vectorstores import FAISS

from services.rag.website_rag import _terms_source_documents, build_faiss_index

DEFAULT_HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_ACTIVE_EMBEDDING_MODE: Optional[str] = None


def _require_real_embeddings_message() -> str:
    return (
        "Real embeddings are required for tests/eval. "
        "Install sentence-transformers (HuggingFace) or set GEMINI_API_KEY for Gemini."
    )


@lru_cache(maxsize=4)
def get_huggingface_embeddings(
    model_name: str = DEFAULT_HF_EMBEDDING_MODEL,
) -> Any:
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model_name)


def _gemini_embeddings_for_eval() -> Any:
    from config import get_gemini_api_key
    from services.rag.website_rag import get_embeddings

    if not get_gemini_api_key():
        raise RuntimeError(_require_real_embeddings_message())
    embeddings = get_embeddings()
    if embeddings is None:
        raise RuntimeError(_require_real_embeddings_message())
    return embeddings


def _use_gemini_for_eval() -> bool:
    return os.environ.get("EVAL_EMBEDDINGS", "").strip().lower() in (
        "gemini",
        "production",
    )


def resolve_eval_embeddings(
    model_name: str = DEFAULT_HF_EMBEDDING_MODEL,
) -> Tuple[Any, str]:
    """
    Default: HuggingFace (bulk eval, no API quota).
    Set EVAL_EMBEDDINGS=gemini for production Gemini parity (needs GEMINI_API_KEY).
    """
    global _ACTIVE_EMBEDDING_MODE

    if _use_gemini_for_eval():
        emb = _gemini_embeddings_for_eval()
        _ACTIVE_EMBEDDING_MODE = "Gemini:production"
        return emb, _ACTIVE_EMBEDDING_MODE

    try:
        emb = get_huggingface_embeddings(model_name)
        label = f"HuggingFace:{model_name}"
    except ImportError:
        from config import get_gemini_api_key

        if get_gemini_api_key():
            emb = _gemini_embeddings_for_eval()
            _ACTIVE_EMBEDDING_MODE = "Gemini:production"
            return emb, _ACTIVE_EMBEDDING_MODE
        raise RuntimeError(_require_real_embeddings_message()) from None

    _ACTIVE_EMBEDDING_MODE = label
    return emb, label


@lru_cache(maxsize=4)
def build_terms_vector_store_with_huggingface(
    model_name: str = DEFAULT_HF_EMBEDDING_MODEL,
) -> FAISS:
    """Cached in-memory Terms KB index using real embeddings only."""
    embeddings, _ = resolve_eval_embeddings(model_name)
    return build_faiss_index(_terms_source_documents(), embeddings)


def embedding_mode_label(model_name: Optional[str] = None) -> str:
    if _ACTIVE_EMBEDDING_MODE:
        return _ACTIVE_EMBEDDING_MODE
    name = model_name or DEFAULT_HF_EMBEDDING_MODEL
    return f"HuggingFace:{name}"
