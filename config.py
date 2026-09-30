"""
Central configuration for the Trip Planner capstone app.

What: Default URLs, scoring constants, paths, and .env-backed secrets.
Why: One place to change behavior; API keys stay out of the UI and git.
How: Loads `.env` at import; use get_gemini_api_key() and get_user_agent().
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Project root (folder containing app.py)
PROJECT_ROOT = Path(__file__).resolve().parent

def _strip_env_value(value: str) -> str:
    """Remove whitespace and optional quotes from .env values."""
    return value.strip().strip('"').strip("'")


def _load_env_file() -> None:
    """
    Load `.env` from the project root.

    Uses python-dotenv first, then a simple line parser so values with quotes
    still work if the file was edited by hand.
    """
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return
    load_dotenv(env_path, override=True, encoding="utf-8")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw_val = line.partition("=")
        key = key.strip()
        val = _strip_env_value(raw_val)
        if key and val:
            os.environ.setdefault(key, val)


_load_env_file()

# Persistence paths required by the capstone instructions
DATA_DIR = PROJECT_ROOT / "data"
APP_STATE_PATH = DATA_DIR / "app_state.json"
FEEDBACK_PATH = DATA_DIR / "feedback.jsonl"

# OpenStreetMap endpoints (free, no API key)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Wikimedia / Wikivoyage (optional RAG)
WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"

# Default Gemini model (see MODEL_FALLBACKS if your key rejects this id)
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MODEL_FALLBACKS = (
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
)

# Agent loop limits
DEFAULT_MAX_STEPS = 6
FAST_MODE_MAX_STEPS = 4
FAST_POI_LIMIT = 45

# Feedback boost weights from instructions
UPVOTE_BOOST = 0.25
DOWNVOTE_BOOST = -0.35

# HTTP timeouts and retries
REQUEST_TIMEOUT_SEC = 15
MAX_RETRIES = 2

# RAG chunk size range from instructions
RAG_CHUNK_MIN = 800
RAG_CHUNK_MAX = 1000
RAG_TOP_K = 5

# OSM User-Agent — contact email comes from OSM_CONTACT_EMAIL in .env
DEFAULT_USER_AGENT_TEMPLATE = "trip-planner-capstone/1.0 ({contact})"


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def get_gemini_api_key() -> Optional[str]:
    """Google Gemini / AI Studio key from .env (GEMINI_API_KEY)."""
    key = _strip_env_value(os.environ.get("GEMINI_API_KEY", ""))
    return key or None


get_openai_api_key = get_gemini_api_key


def get_osm_contact_email() -> str:
    """Email for Nominatim/Overpass User-Agent (OSM_CONTACT_EMAIL in .env)."""
    return _strip_env_value(os.environ.get("OSM_CONTACT_EMAIL", ""))


def get_user_agent() -> str:
    """Full User-Agent string required by OpenStreetMap APIs."""
    contact = get_osm_contact_email()
    if not contact:
        return ""
    return DEFAULT_USER_AGENT_TEMPLATE.format(contact=contact)


def is_wikivoyage_rag_enabled() -> bool:
    """Optional RAG toggle (ENABLE_WIKIVOYAGE_RAG in .env, default off for speed)."""
    return _env_bool("ENABLE_WIKIVOYAGE_RAG", default=False)


def is_destination_guide_ai_enabled() -> bool:
    """Extra Gemini call for season copy (DESTINATION_GUIDE_AI in .env, default off)."""
    return _env_bool("DESTINATION_GUIDE_AI", default=False)


# Cap Wikipedia photo lookups per itinerary render (speed)
MAX_ITINERARY_PHOTO_STOPS = 12
