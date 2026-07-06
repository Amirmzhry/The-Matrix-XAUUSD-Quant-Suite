# =============================================================================
# llm_client.py — Shared Gemini LLM Client
# The Quant Council
# =============================================================================
# Centralised LLM connection so every agent uses the same model config.
#
# KEY DESIGN: python-dotenv is OPTIONAL. If it is not installed, we parse
# the .env file ourselves using a built-in parser. This means the module
# imports cleanly regardless of whether python-dotenv is in the venv.
# =============================================================================

import os
import re
import time
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

# ─── CRITICAL: Purge ADC / OAuth2 credentials before ANY google import ──────
# This must run before ANY google import or configure() call.
# ---------------------------------------------------------------------------
for _gac_var in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
                 "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    os.environ.pop(_gac_var, None)


# ---------------------------------------------------------------------------
# Zero-dependency .env loader
# ---------------------------------------------------------------------------

def _load_env_file(env_path: Optional[str] = None) -> None:
    """
    Parse a .env file and inject its key=value pairs into os.environ.
    Works without python-dotenv. Skips lines that are comments or blank.
    Already-set env vars are NOT overwritten (shell takes priority).
    """
    if env_path is None:
        # Walk up from this file's directory to find .env
        here = Path(__file__).parent
        candidates = [here / ".env", here.parent / ".env"]
        env_path = next((str(p) for p in candidates if p.exists()), None)

    if not env_path or not os.path.exists(env_path):
        return  # No .env file — silently continue

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")   # strip optional quotes
            if key and key not in os.environ:         # don't overwrite shell vars
                os.environ[key] = val


def _try_load_dotenv() -> None:
    """Try python-dotenv first; silently fall back to our built-in parser."""
    try:
        from dotenv import load_dotenv          # preferred if installed
        load_dotenv(override=False)
    except ImportError:
        _load_env_file()                        # built-in fallback


# Run at import time (same behaviour as `load_dotenv()` at module level)
_try_load_dotenv()


# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_client_cache: dict = {}


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def get_client() -> Any:
    """
    Returns a configured google-genai Client instance.
    Caches the client so we only initialise once per process.
    """
    try:
        from google import genai
    except ImportError:
        raise ImportError(
            "google-genai is not installed.\n"
            "Install it with:  .\\.venv\\Scripts\\pip install google-genai"
        )

    if "default" in _client_cache:
        return _client_cache["default"]

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            "Add it to your .env file:  GEMINI_API_KEY=<your_real_key>"
        )

    client = genai.Client(api_key=api_key)
    _client_cache["default"] = client
    return client


# ---------------------------------------------------------------------------
# LLM call with retry
# ---------------------------------------------------------------------------

def call_gemini(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_retries: int = 3,
) -> str:
    """
    Sends a prompt to Gemini and returns the raw text response.
    Retries up to `max_retries` times on transient errors.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai is not installed.")

    client = get_client()
    target_model = model or DEFAULT_MODEL

    generation_config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=8192,
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=generation_config,
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"  [LLM] Attempt {attempt}/{max_retries} failed: {e}")

            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 2s, 4s, 8s backoff

    raise RuntimeError(f"Gemini API failed after {max_retries} attempts. Last error: {last_error}")


# ---------------------------------------------------------------------------
# JSON extractor
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """
    Robustly extracts the first JSON object from a Gemini response string.
    Handles:
      - Bare JSON:           {"key": "value"}
      - Markdown fenced:     ```json\\n{...}\\n```
      - JSON in prose:       "Here is my answer: {...} done."
    Never raises — returns {} on total failure.
    """
    if not text or not text.strip():
        return {}

    # Step 1: Strip markdown code fences
    cleaned = re.sub(r"```(?:json|mql5|cpp)?\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)

    # Step 2: Find the first complete {...} block (greedy from outer braces)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return {}

    # Step 3: Try to parse
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        pass

    # Step 4: Last resort — parse the entire stripped string
    try:
        return json.loads(cleaned.strip())
    except Exception:
        return {}
