# test_api.py -- Verifies GEMINI_API_KEY is loaded from .env
# Uses the built-in llm_client loader so python-dotenv is not required.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# llm_client._try_load_dotenv() runs at import and handles .env parsing
# without requiring python-dotenv to be installed.
from llm_client import _load_env_file
_load_env_file()

api_key = os.getenv("GEMINI_API_KEY")

print("=========================================")
print("          API KEY CONNECTION TEST        ")
print("=========================================")

if api_key and not api_key.startswith("your_"):
    masked_key = f"{api_key[:6]}...{api_key[-4:]}"
    print(f"  SUCCESS: Key loaded: {masked_key}")
    print("  System ready to connect to Gemini LLM.")
else:
    print("  ERROR: GEMINI_API_KEY not found or placeholder value.")
    print("  Check your .env file at:  d:\\The Matrix\\.env")
    print("  Expected:  GEMINI_API_KEY=<your_real_key>")

print("=========================================")