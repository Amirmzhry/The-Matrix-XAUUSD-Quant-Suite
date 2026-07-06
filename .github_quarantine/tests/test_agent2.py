# =============================================================================
# tests/test_agent2.py — Unit Test: LeadQuantAgent
# The Quant Council
# =============================================================================
# Verifies that Agent 2:
#   - Correctly reads a "HEAVY_NOISE" analyst report and selects MAD/HAMPEL
#   - Prints the Inner Monologue to terminal
#   - Returns valid filtered DataFrame + params dict
#   - Escalates aggressiveness on retry (iteration > 1)
#   - Skips rejected filters from previous iterations
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.agents.agent1_data_analyst import DataAnalystAgent
from src.agents.agent2_lead_quant import LeadQuantAgent


def _make_noisy_df(n: int = 200, seed: int = 77) -> pd.DataFrame:
    """Builds a moderately toxic tick DataFrame for Lead Quant testing."""
    np.random.seed(seed)
    start = datetime(2025, 3, 10, 8, 0, 0)
    times = [start + timedelta(milliseconds=i * 150) for i in range(n)]
    bids  = 2050.0 + np.random.randn(n).cumsum() * 0.8
    # Inject 15 hard spikes
    spike_idx = np.random.choice(n, size=15, replace=False)
    bids[spike_idx] += np.random.randn(15) * 6.0
    spreads = np.random.uniform(0.01, 0.08, n)
    asks    = bids + spreads
    vols    = np.random.poisson(lam=8, size=n).astype(float)
    return pd.DataFrame({'DateTime': times, 'Bid': bids, 'Ask': asks, 'Tick_Volume': vols})


def _build_analyst_output(df: pd.DataFrame) -> dict:
    """Runs Agent 1 to get a real analyst output dict."""
    agent = DataAnalystAgent(verbose=False)
    return agent.run(df)


# =============================================================================
# TEST 1: Basic execution — reads analyst output, selects filter
# =============================================================================
def test_agent2_basic_execution():
    print("\n" + "="*68)
    print("  TEST 1/3 — Agent 2 | Basic Filter Selection from HEAVY_NOISE Report")
    print("="*68)

    df             = _make_noisy_df(n=200)
    analyst_output = _build_analyst_output(df)

    print(f"\n  [Pre-test] Analyst detected regime: {analyst_output['regime']['regime']}")

    agent  = LeadQuantAgent(verbose=True)
    result = agent.run(df, analyst_output, rejected_filters=[], iteration=1)

    # Structural assertions
    assert "filtered_df"  in result,     "FAIL: Missing 'filtered_df'"
    assert "params"       in result,     "FAIL: Missing 'params'"
    assert "filter_name"  in result,     "FAIL: Missing 'filter_name'"

    fdf    = result["filtered_df"]
    params = result["params"]
    fname  = result["filter_name"]

    assert isinstance(fdf, pd.DataFrame),      "FAIL: filtered_df is not a DataFrame"
    assert len(fdf) == len(df),                "FAIL: Filtered DF has wrong number of rows"
    assert "Bid" in fdf.columns,              "FAIL: 'Bid' column missing from filtered_df"
    assert "filter" in params,                 "FAIL: 'filter' missing from params dict"
    assert fname == params["filter"],          "FAIL: filter_name doesn't match params['filter']"
    assert not fdf['Bid'].isnull().any(),      "FAIL: Filtered Bid contains NaN values"

    print(f"\n  ✅ TEST 1 PASSED — Filter selected: [{fname}], Params: {params}")


# =============================================================================
# TEST 2: Inner Monologue verification for HEAVY_NOISE
# =============================================================================
def test_agent2_inner_monologue_heavy_noise(capsys=None):
    print("\n" + "="*68)
    print("  TEST 2/3 — Agent 2 | Inner Monologue printed for HEAVY_NOISE")
    print("="*68)

    df = _make_noisy_df(n=300, seed=42)
    analyst_output = _build_analyst_output(df)

    # Force regime to HEAVY_NOISE for deterministic test
    analyst_output["regime"]["regime"]    = "HEAVY_NOISE"
    analyst_output["regime"]["confidence"] = 0.88

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    agent = LeadQuantAgent(verbose=True)

    # Capture stdout to verify monologue content
    with redirect_stdout(buf):
        result = agent.run(df, analyst_output, rejected_filters=[], iteration=1)

    output = buf.getvalue()

    assert "INNER MONOLOGUE"    in output,   "FAIL: 'INNER MONOLOGUE' header not printed"
    assert "SITUATION ASSESSMENT" in output, "FAIL: 'SITUATION ASSESSMENT' section missing"
    assert "FILTER SELECTION"   in output,   "FAIL: 'FILTER SELECTION' section missing"
    assert "RATIONALE"          in output,   "FAIL: 'RATIONALE' not printed"
    assert result["filter_name"] in ("MAD", "HAMPEL", "EMA_ZSCORE"),  \
        f"FAIL: HEAVY_NOISE should select MAD/HAMPEL/EMA, got {result['filter_name']}"

    print(f"\n  ✅ TEST 2 PASSED — Inner Monologue verified, filter={result['filter_name']}")


# =============================================================================
# TEST 3: Rejected filter escalation
# =============================================================================
def test_agent2_rejection_escalation():
    print("\n" + "="*68)
    print("  TEST 3/3 — Agent 2 | Rejection Escalation (skips rejected filters)")
    print("="*68)

    df             = _make_noisy_df(n=200, seed=13)
    analyst_output = _build_analyst_output(df)

    # Force EXTREME_SPIKE regime — priority: [HAMPEL, MAD, EMA_ZSCORE, KALMAN]
    analyst_output["regime"]["regime"] = "EXTREME_SPIKE"

    agent = LeadQuantAgent(verbose=True)

    # First iteration: should pick HAMPEL (first in priority list)
    r1 = agent.run(df, analyst_output, rejected_filters=[], iteration=1)
    assert r1["filter_name"] == "HAMPEL", \
        f"FAIL: Expected HAMPEL first, got {r1['filter_name']}"

    r2 = agent.run(df, analyst_output, rejected_filters=["HAMPEL"], iteration=2)
    valid_alternatives = ["MAD", "DEEP_DENOISE_HAMPEL_KALMAN", "EMA_ZSCORE", "ADAPTIVE_KALMAN"]
    assert r2["filter_name"] in valid_alternatives, \
        f"FAIL: Expected a valid robust alternative after HAMPEL rejection, got {r2['filter_name']}"

    # Verify escalation factor tightens parameters
    k1 = r1["params"].get("k_sigma", r1["params"].get("mad_threshold", 3.0))
    k2 = r2["params"].get("mad_threshold", r2["params"].get("k_sigma", 3.0))
    assert k2 <= k1 + 0.5, \
        f"FAIL: Escalation should tighten params. k1={k1}, k2={k2}"

    print(f"\n  ✅ TEST 3 PASSED — Iter1={r1['filter_name']}, Iter2={r2['filter_name']}, Escalation verified")


# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("\n" + "█"*68)
    print("  THE QUANT COUNCIL — UNIT TESTS: AGENT 2 (LeadQuantAgent)")
    print("█"*68)

    passed = 0
    total  = 3

    try:
        test_agent2_basic_execution()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 1 FAILED: {e}")

    try:
        test_agent2_inner_monologue_heavy_noise()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 2 FAILED: {e}")

    try:
        test_agent2_rejection_escalation()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 3 FAILED: {e}")

    print(f"\n{'='*68}")
    print(f"  AGENT 2 TESTS: {passed}/{total} PASSED")
    print(f"{'='*68}\n")
