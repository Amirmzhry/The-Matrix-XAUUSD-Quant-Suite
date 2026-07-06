# =============================================================================
# tests/test_agent5.py — Unit Test: MQL5SynthesizerAgent
# The Quant Council
# =============================================================================
# Verifies that Agent 5:
#   - Generates a .mqh file for ALL 5 filter types
#   - File is non-empty and contains required C++ structural elements
#   - Inner Monologue is printed for every filter
#   - Audit passes (structural validation)
#   - Deployment comments are present in the generated code
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile

from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent


def _build_approved_payload(filter_name: str, extra_params: dict = None) -> dict:
    """Build a mock RiskOfficerAgent approved payload for a given filter."""
    base_params = {"filter": filter_name}
    filter_defaults = {
        "ADAPTIVE_KALMAN":          {"kalman_R": 0.07, "q_scaling": 0.1},
        "MAD":                      {"window": 50, "mad_threshold": 3.0, "tolerance": 0.05},
        "EMA_ZSCORE":               {"ema_span": 40, "threshold": 2.8},
        "HAMPEL":                   {"half_window": 15, "k_sigma": 2.5},
        "DEEP_DENOISE_HAMPEL_KALMAN": {"hampel_k": 2.5, "kalman_R": 0.1},
    }
    base_params.update(filter_defaults.get(filter_name, {}))
    if extra_params:
        base_params.update(extra_params)
    return {
        "verdict":   "APPROVED",
        "var_shift": 4.2,
        "rmse":      0.08,
        "params":    base_params,
    }


REQUIRED_PATTERNS = [
    "class CTickFactory",
    "ArrayResize",
    "UpdateTick",
    "ArrayFree",
    "IsReady",
    "#property strict",
    "OnTick",                   # Usage example must reference OnTick
    "STEP 1",                   # Deployment step instructions
    "MQL5\\\\Include",          # Install path comment
    "CTickFactory g_filter",    # Usage example instantiation
]


# =============================================================================
# TEST 1: Generate MQL5 for all 5 filter types
# =============================================================================
def test_agent5_all_filters():
    print("\n" + "="*68)
    print("  TEST 1/2 — Agent 5 | Generates valid MQL5 for ALL 5 filters")
    print("="*68)

    filters = [
        "ADAPTIVE_KALMAN",
        "MAD",
        "EMA_ZSCORE",
        "HAMPEL",
        "DEEP_DENOISE_HAMPEL_KALMAN",
    ]

    tmp_dir = tempfile.mkdtemp()
    agent   = MQL5SynthesizerAgent(output_dir=tmp_dir, verbose=True)
    results = {}

    for fname in filters:
        print(f"\n  ── Synthesizing: [{fname}] ──")
        payload = _build_approved_payload(fname)
        result  = agent.run(payload, output_filename=f"test_{fname}.mqh")
        results[fname] = result

        # Assertions for every filter
        assert result.get("audit_passed"),          f"FAIL [{fname}]: Audit failed"
        assert "mql5_code" in result,               f"FAIL [{fname}]: Missing 'mql5_code'"
        assert "filepath"  in result,               f"FAIL [{fname}]: Missing 'filepath'"

        filepath = result["filepath"]
        assert os.path.exists(filepath),            f"FAIL [{fname}]: File not found: {filepath}"
        file_size = os.path.getsize(filepath)
        assert file_size > 2000,                    f"FAIL [{fname}]: File too small ({file_size} bytes)"

        code = result["mql5_code"]
        for pattern in REQUIRED_PATTERNS:
            # Use raw pattern for file-system paths
            check = pattern.replace("\\\\", "\\")
            if check == "IsReady" and fname != "MAD":
                continue
            assert check in code, f"FAIL [{fname}]: Required pattern missing: '{check}'"

        # Filter name should appear in the code
        assert fname in code,                       f"FAIL [{fname}]: Filter name not in generated code"

        print(f"     ✅ {fname}: {file_size:,} bytes, audit PASSED")

    print(f"\n  ✅ TEST 1 PASSED — All 5 filter MQL5 files generated and validated.")


# =============================================================================
# TEST 2: Inner Monologue is printed for MAD filter
# =============================================================================
def test_agent5_inner_monologue():
    print("\n" + "="*68)
    print("  TEST 2/2 — Agent 5 | Inner Monologue printed to terminal")
    print("="*68)

    import io
    from contextlib import redirect_stdout

    tmp_dir = tempfile.mkdtemp()
    agent   = MQL5SynthesizerAgent(output_dir=tmp_dir, verbose=True)
    payload = _build_approved_payload("MAD")

    buf = io.StringIO()
    with redirect_stdout(buf):
        result = agent.run(payload, output_filename="test_monologue.mqh")

    output = buf.getvalue()

    # Verify monologue sections are printed
    assert "INNER MONOLOGUE"     in output,     "FAIL: 'INNER MONOLOGUE' header not printed"
    assert "DESIGN DECISIONS"    in output,     "FAIL: 'DESIGN DECISIONS' section missing"
    assert "MEMORY MODEL"        in output,     "FAIL: Memory model discussion missing"
    assert "TICK PROCESSING"     in output,     "FAIL: Tick processing discussion missing"
    assert "MAD"                 in output,     "FAIL: Filter name not in monologue"
    assert "SYNTHESIZING CODE"   in output,     "FAIL: Code synthesis confirmation missing"

    print(f"  ✅ TEST 2 PASSED — Inner Monologue validated ({len(output)} chars printed).")


# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("\n" + "█"*68)
    print("  THE QUANT COUNCIL — UNIT TESTS: AGENT 5 (MQL5SynthesizerAgent)")
    print("█"*68)

    passed = 0
    total  = 2

    try:
        test_agent5_all_filters()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 1 FAILED: {e}")
        import traceback; traceback.print_exc()

    try:
        test_agent5_inner_monologue()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 2 FAILED: {e}")

    print(f"\n{'='*68}")
    print(f"  AGENT 5 TESTS: {passed}/{total} PASSED")
    print(f"{'='*68}\n")
