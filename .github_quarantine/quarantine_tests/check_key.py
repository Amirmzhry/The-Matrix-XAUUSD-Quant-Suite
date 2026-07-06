# check_key.py -- Gemini API Key Connectivity Verification
# Run: .venv\Scripts\python.exe check_key.py
import os
import sys

# STEP 1: Purge ADC / OAuth2 credentials before any genai import
for _var in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
             "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    os.environ.pop(_var, None)

# STEP 2: Load .env (llm_client fallback parser, no python-dotenv required)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from llm_client import _load_env_file
    _load_env_file()
except Exception:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# STEP 3: Imports (after purge and env load)
from google import genai

api_key = os.getenv("GEMINI_API_KEY", "")

print("=" * 50)
print("  GEMINI API KEY CONNECTIVITY CHECK")
print("=" * 50)

if not api_key or api_key.startswith("your_"):
    print("  ERROR: GEMINI_API_KEY not found in .env")
    print("  Add:   GEMINI_API_KEY=<your_real_key>")
    sys.exit(1)

masked = f"{api_key[:6]}...{api_key[-4:]}"
print(f"  Key loaded: {masked}")
print(f"  Key format: {'AQ. (AI Studio)' if api_key.startswith('AQ.') else 'Standard (AIza)'}")
print()

# STEP 4: Test with new google-genai client
try:
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly one word: ONLINE",
    )
    print(f"  Gemini response: {resp.text.strip()}")
    print("  STATUS: CONNECTED OK")
except Exception as e:
    print(f"  STATUS: FAILED -- {e}")
    sys.exit(1)

print("=" * 50)