"""
Grounded website / document RAG for the policy chatbot.

Uses direct ``vector_store.similarity_search_with_score`` (no LCEL chains).
Embeddings and vector stores are cached with ``@st.cache_resource``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

import streamlit as st
from google import genai
from google.genai import types
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    DEFAULT_MODEL,
    EMBEDDING_CACHE_VERSION,
    get_gemini_api_key,
    get_gemini_embedding_model_candidates,
)
from services.agent import generate_content_with_fallback
from services.refund_policy_config import POLICIES
from services.terms_content import (
    FAQ_ITEMS,
    RAG_CHAT_TERMS_SECTIONS,
    RAG_CHAT_TERMS_INTRO,
    TERMS_INTRO,
    TERMS_SECTIONS,
)

# Tuned for HTML / markdown web pages: favor paragraph and sentence boundaries.
WEB_CHUNK_SIZE = 1100
WEB_CHUNK_OVERLAP = 180
WEB_SPLIT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]

TERMS_STORE_ID = "terms_policies_kb"
MIN_RELEVANCE_SCORE = 0.42  # cosine distance on FAISS scores (lower = closer)

GROUNDED_SYSTEM_INSTRUCTION = """You are a policy, support, and sales assistant for a travel app demo. 

Rules (Strictly Follow):

1. **Grounding & Scope:** Answer strictly using the "Retrieved context" below. Do not use outside knowledge. 
2. **General Package Overview:** If a user asks a general question about packages (e.g., "tell me about your packages" or "what packages do you have"), list the available package names along with a concise 2-line summary/detail, price, and what it is providing for each package based strictly on the context. Do not just output raw names.
3. **Detailed & Custom Inquiries:** If a user asks about a specific package, provide accurate details based on the context (per person rates, base nights, and base days).
4. **Package fare quotes (travelers, nights/days) — mandatory math:** When the user names a catalog package and gives **travelers** and/or a **longer stay** (extra nights, extra days, or a total trip length), you MUST produce a full **illustrative booking estimate** using only the demo formulas in the retrieved context (catalog base price per traveler, included catalog nights, night add-on rate, Standard vs Flex multipliers). Never stop at base-only pricing when the user asked for a longer trip or more travelers.
   - **Do NOT** tell the user to contact support, that extra-night rates are missing, or that you cannot total the trip if the context includes base prices and the night add-on / fare-type rules.
   - **Do NOT** hallucinate or invent prices. Use only numbers from context.
   - **Days vs nights:** Catalog bundles are priced by **nights** (same as *Book package*). If the user says **N days** but not nights, price using **N nights** and state that assumption in one short line. If they give nights, use that value directly.
   - **Demo formula (apply in order when present in context):**
     1. **Base subtotal** = package **base price per traveler** × **number of travelers**.
     2. **Included nights** = catalog included nights for that package (usually **1**).
     3. **Extra nights** = max(0, **requested nights** − **included nights**).
     4. **Night add-on** = **₹1,200** (or the rate in context) × **extra nights** × **travelers**.
     5. **Standard:** multiplier **1.0×** → **Standard total** = base subtotal + night add-on (fare adjustment **₹0**).
     6. **Flex:** multiplier **1.12×** → **Flex fare adjustment** = base subtotal × **0.12**; **Flex total** = base subtotal × **1.12** + night add-on.
     7. **Per traveler** = fare total ÷ travelers (for each fare type).
   - **Required output shape** for these quotes (use clear markdown, show every step):
     - Package name, travelers, requested nights (and day assumption if any), included nights, extra nights.
     - Line items: base subtotal; night add-on (show extra nights × rate × travelers); Flex premium line only for Flex.
     - **Standard total** and **Flex total** (both), with **per person** under each unless the user asked for only one fare type.
     - One line that totals are **illustrative demo** pricing, not a live contract.
   - Double-check multiplication and addition; totals must match the formula exactly.
5. **Other customizations:** For changes not covered above (e.g., combining packages), still compute step-by-step from context rates; do not defer if the numbers are in the text.
6. **Day & Night Significance:** Keep **days** (itinerary length) and **nights** (priced stay) distinct in wording; tie priced nights to the add-on formula.
7. **Tone & Quality:** Highly relevant, coherent, complete, context-precise. Short, clear markdown.
"""

_USER_PROMPT_TEMPLATE = """User question:
{question}

Retrieved context:
{context}

Answer the user question following the system rules."""


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    text: str
    score: float  # similarity: higher = more relevant (1 - distance when using FAISS distance)
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _strip_markdown_noise(text: str) -> str:
    t = re.sub(r"[#>*_`]", " ", text)
    return _normalize_whitespace(t)


def web_text_splitter() -> RecursiveCharacterTextSplitter:
    """Chunk web-like text without splitting mid-sentence when possible."""
    return RecursiveCharacterTextSplitter(
        chunk_size=WEB_CHUNK_SIZE,
        chunk_overlap=WEB_CHUNK_OVERLAP,
        length_function=len,
        separators=WEB_SPLIT_SEPARATORS,
    )


def validate_http_url(url: str) -> Tuple[bool, str]:
    raw = (url or "").strip()
    if not raw:
        return False, "Please enter a URL."
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        return False, "URL must start with http:// or https://."
    if not parsed.netloc:
        return False, "That URL does not look valid (missing host name)."
    return True, raw


def _terms_source_documents() -> List[Document]:
    """Build LangChain documents from in-app Terms & Policies knowledge."""
    docs: List[Document] = []
    docs.append(
        Document(
            page_content=_strip_markdown_noise(TERMS_INTRO),
            metadata={"source": "Terms — Introduction"},
        )
    )
    docs.append(
        Document(
            page_content=_strip_markdown_noise(RAG_CHAT_TERMS_INTRO),
            metadata={"source": "Document Assistant — Introduction"},
        )
    )
    for title, body in RAG_CHAT_TERMS_SECTIONS:
        docs.append(
            Document(
                page_content=_strip_markdown_noise(body),
                metadata={"source": f"Document Assistant — {title}"},
            )
        )
    for title, body in TERMS_SECTIONS:
        docs.append(
            Document(
                page_content=_strip_markdown_noise(body),
                metadata={"source": f"Terms — {title}"},
            )
        )
    for item in FAQ_ITEMS:
        docs.append(
            Document(
                page_content=_strip_markdown_noise(
                    f"Question: {item['q']} Answer: {item['a']}"
                ),
                metadata={"source": f"FAQ — {item['q']}"},
            )
        )
    for pol in POLICIES.values():
        docs.append(
            Document(
                page_content=_strip_markdown_noise(
                    f"{pol.description} "
                    f"Travel mode: {pol.travel_mode}. Ticket type: {pol.ticket_type}. "
                    f"Refundability: {pol.refundability}. "
                    f"Minimum hours before departure: {pol.min_hours_before_departure}. "
                    f"Cancellation fee (demo fraction of fare): {pol.cancellation_fee_rate:.0%}. "
                    f"Max refundable fraction after fee: {pol.max_refund_fraction:.0%}. "
                    f"Processing (demo): {pol.processing_days_min}–{pol.processing_days_max} business days."
                ),
                metadata={"source": f"Policy — {pol.label}"},
            )
        )
    return docs


def load_documents_from_url(url: str) -> Tuple[List[Document], Optional[str]]:
    """
    Scrape a public page into documents.
    Returns (documents, error_message). error_message is set on failure.
    """
    ok, normalized = validate_http_url(url)
    if not ok:
        return [], normalized

    try:
        loader = WebBaseLoader(
            normalized,
            requests_kwargs={"timeout": 20},
        )
        raw_docs = loader.load()
    except Exception as exc:  # noqa: BLE001
        return [], f"Could not load URL: {exc}"

    if not raw_docs:
        return [], "No content was returned from that URL."

    cleaned: List[Document] = []
    for doc in raw_docs:
        text = _normalize_whitespace(doc.page_content)
        if len(text) < 40:
            continue
        source = str(doc.metadata.get("source") or normalized)
        cleaned.append(Document(page_content=text, metadata={"source": source}))

    if not cleaned:
        return [], "The page loaded but contained no usable text."

    splitter = web_text_splitter()
    chunks = splitter.split_documents(cleaned)
    if not chunks:
        return [], "Could not split page text into chunks."

    return chunks, None


def _remember_embedding_error(message: str) -> None:
    st.session_state["_embedding_init_error"] = message


def _clear_embedding_error() -> None:
    st.session_state.pop("_embedding_init_error", None)


@st.cache_resource(show_spinner=False)
def get_embeddings(_cache_version: int = EMBEDDING_CACHE_VERSION) -> Optional[GoogleGenerativeAIEmbeddings]:
    """Pick the first Gemini embedding model that responds to a probe embed."""
    api_key = get_gemini_api_key()
    if not api_key:
        _remember_embedding_error("GEMINI_API_KEY is not set.")
        return None

    last_error: Optional[str] = None
    for model in get_gemini_embedding_model_candidates():
        try:
            client = GoogleGenerativeAIEmbeddings(
                model=model,
                google_api_key=api_key,
            )
            client.embed_query("healthcheck")
            _clear_embedding_error()
            return client
        except Exception as exc:  # noqa: BLE001 — surface model fallback chain
            last_error = f"{model}: {exc}"
            continue

    _remember_embedding_error(
        last_error
        or "No embedding model succeeded. Set GEMINI_EMBEDDING_MODEL=gemini-embedding-001 in .env."
    )
    return None


def build_faiss_index(
    documents: Sequence[Document],
    embeddings: Any,
) -> FAISS:
    """Build a FAISS index (used by caches and unit tests)."""
    return _build_faiss_from_documents(documents, embeddings)


def _build_faiss_from_documents(
    documents: Sequence[Document],
    embeddings: Any,
) -> FAISS:
    splitter = web_text_splitter()
    # Split long sections; short FAQ/policy docs may pass through as one chunk.
    chunks = splitter.split_documents(list(documents))
    if not chunks:
        raise ValueError("No text chunks to index.")
    return FAISS.from_documents(chunks, embeddings)


@st.cache_resource(show_spinner=False)
def get_terms_vector_store(_cache_version: int = EMBEDDING_CACHE_VERSION) -> Optional[FAISS]:
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        return build_faiss_index(_terms_source_documents(), embeddings)
    except Exception as exc:  # noqa: BLE001
        _remember_embedding_error(str(exc))
        return None


@st.cache_resource(show_spinner=False)
def get_url_vector_store(
    url: str,
    _cache_version: int = EMBEDDING_CACHE_VERSION,
) -> Optional[FAISS]:
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    docs, err = load_documents_from_url(url)
    if err:
        return None
    try:
        return _build_faiss_from_documents(docs, embeddings)
    except Exception as exc:  # noqa: BLE001
        _remember_embedding_error(str(exc))
        return None


def _distance_to_similarity(distance: float) -> float:
    """Map FAISS L2 distance to a simple 0–1 relevance score for display."""
    return float(1.0 / (1.0 + max(distance, 0.0)))


def similarity_search(
    query: str,
    *,
    vector_store: FAISS,
    top_k: int = 4,
) -> List[RetrievedChunk]:
    q = (query or "").strip()
    if not q:
        return []

    pairs = vector_store.similarity_search_with_score(q, k=top_k)
    out: List[RetrievedChunk] = []
    for doc, dist in pairs:
        sim = _distance_to_similarity(float(dist))
        if sim < MIN_RELEVANCE_SCORE:
            continue
        meta = dict(doc.metadata or {})
        source = str(meta.get("source") or "Document")
        out.append(
            RetrievedChunk(
                source=source,
                text=doc.page_content.strip(),
                score=sim,
                metadata=MappingProxyType(meta),
            )
        )
    return out


def retrieve_from_terms_kb(
    query: str,
    *,
    top_k: int = 4,
) -> Tuple[List[RetrievedChunk], Optional[str]]:
    """Retrieve chunks from the built-in Terms & Policies index."""
    store = get_terms_vector_store()
    if store is None:
        detail = st.session_state.get("_embedding_init_error") or ""
        if not get_gemini_api_key():
            return [], "GEMINI_API_KEY is missing. Add it to `.env` to enable semantic search."
        if detail:
            return (
                [],
                "Semantic search is unavailable (embedding API error). "
                f"Details: {detail} "
                "Try `GEMINI_EMBEDDING_MODEL=gemini-embedding-001` in `.env`, then restart the app.",
            )
        return [], "Could not build the policy search index. Restart the app after updating `.env`."
    return similarity_search(query, vector_store=store, top_k=top_k), None


def retrieve_from_url(
    query: str,
    url: str,
    *,
    top_k: int = 4,
) -> Tuple[List[RetrievedChunk], Optional[str]]:
    ok, msg = validate_http_url(url)
    if not ok:
        return [], msg

    store = get_url_vector_store(url.strip())
    if store is None:
        docs, err = load_documents_from_url(url.strip())
        if err:
            return [], err
        if not docs:
            return [], "No content to search from that URL."
        return [], "Could not build the search index (check GEMINI_API_KEY)."

    return similarity_search(query, vector_store=store, top_k=top_k), None


def chunks_to_context(chunks: Sequence[RetrievedChunk]) -> str:
    parts: List[str] = []
    for i, ch in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {ch.source}\n{ch.text}")
    return "\n\n".join(parts)


def chunks_to_source_dicts(chunks: Sequence[RetrievedChunk]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for c in chunks:
        meta = dict(c.metadata) if c.metadata else {}
        row: Dict[str, Any] = {
            "source": c.source,
            "text": c.text,
            "score": round(c.score, 3),
            "metadata": meta,
        }
        for key in ("url", "source_url", "link", "href", "page_url", "title", "details", "extra"):
            if key in meta and meta[key] is not None:
                row[key] = meta[key]
        rows.append(row)
    return rows


def format_chunks_as_markdown(chunks: Sequence[RetrievedChunk]) -> str:
    """Fallback answer when the LLM is unavailable — still grounded in retrieval."""
    from services.rag_citations import embed_sources_in_reply

    lines = [
        "From the **Terms & Conditions & Policies** document (demo):",
        "",
    ]
    for ch in chunks:
        snippet = ch.text if len(ch.text) <= 480 else ch.text[:479] + "…"
        cite = embed_sources_in_reply(snippet, [chunks_to_source_dicts([ch])[0]], append_sentence=False)
        lines.append(cite)
        lines.append("")
    lines.append(
        "_Illustrative demo text, not a real operator contract._"
    )
    return "\n".join(lines)


def generate_grounded_answer(
    query: str,
    chunks: Sequence[RetrievedChunk],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Call Gemini with strict grounding. Returns (answer_text, error_message).
    """
    if not chunks:
        return None, None

    api_key = get_gemini_api_key()
    if not api_key:
        return format_chunks_as_markdown(chunks), None

    context = chunks_to_context(chunks)
    prompt = _USER_PROMPT_TEMPLATE.format(question=query.strip(), context=context)
    client = genai.Client(api_key=api_key)
    try:
        _, response = generate_content_with_fallback(
            client,
            DEFAULT_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=GROUNDED_SYSTEM_INSTRUCTION,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return format_chunks_as_markdown(chunks), None
        return text, None
    except Exception as exc:  # noqa: BLE001
        return format_chunks_as_markdown(chunks), f"LLM error: {exc}"
