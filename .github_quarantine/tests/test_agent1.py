# =============================================================================
# tests/test_agent1.py — Unit Test: DataAnalystAgent
# The Quant Council
# =============================================================================
# Verifies that Agent 1 correctly ingests a 100-row dummy DataFrame,
# executes all 3 tools, and produces a structured readable market report.
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.agents.agent1_data_analyst import DataAnalystAgent


def _make_dummy_df(n_rows: int = 100, regime: str = "NORMAL", seed: int = 42) -> pd.DataFrame:
    """
    Synthesizes a dummy tick DataFrame with controllable noise levels.

    regime options:
      "NORMAL"      — clean random walk, tight spreads
      "HEAVY_NOISE" — random spikes injected, wider spreads
      "FLASH_CRASH" — catastrophic price drop in the middle
    """
    np.random.seed(seed)
    start = datetime(2025, 1, 6, 9, 0, 0)

    # Timestamps: mostly 10ms ticks, 5% lag spikes (for CV test)
    deltas_ms = np.random.choice([0.01, 0.60], size=n_rows, p=[0.95, 0.05])
    times = [start + timedelta(seconds=sum(deltas_ms[:i])) for i in range(n_rows)]

    # Base price random walk
    bids = 2000.0 + np.random.randn(n_rows).cumsum() * 0.5

    if regime == "HEAVY_NOISE":
        spike_idx = np.random.choice(n_rows, size=8, replace=False)
        bids[spike_idx] += np.random.randn(8) * 5.0

    elif regime == "FLASH_CRASH":
        crash_start = n_rows // 2
        bids[crash_start:] -= np.linspace(0, 30, n_rows - crash_start)

    spreads = np.random.uniform(0.01, 0.05, n_rows)
    if regime in ("HEAVY_NOISE", "FLASH_CRASH"):
        toxic_idx = np.random.choice(n_rows, size=10, replace=False)
        spreads[toxic_idx] += np.random.uniform(0.5, 1.5, 10)

    asks = bids + spreads
    volumes = np.random.poisson(lam=5.0, size=n_rows).astype(float)

    return pd.DataFrame({
        'DateTime':    times,
        'Bid':         bids,
        'Ask':         asks,
        'Tick_Volume': volumes,
    })


# =============================================================================
# TEST 1: Basic smoke test — NORMAL regime
# =============================================================================
def test_agent1_normal_regime():
    print("\n" + "="*68)
    print("  TEST 1/3 — Agent 1 | NORMAL Regime (100-row DataFrame)")
    print("="*68)

    df     = _make_dummy_df(n_rows=100, regime="NORMAL")
    agent  = DataAnalystAgent(verbose=True)
    result = agent.run(df)

    # Assertions
    assert "report_text"  in result,            "FAIL: Missing 'report_text' key"
    assert "toxicity"     in result,            "FAIL: Missing 'toxicity' key"
    assert "volatility"   in result,            "FAIL: Missing 'volatility' key"
    assert "regime"       in result,            "FAIL: Missing 'regime' key"
    assert "metadata"     in result,            "FAIL: Missing 'metadata' key"

    report = result["report_text"]
    assert len(report) > 200,                   "FAIL: Report too short to be readable"
    assert "Q_SCORE"      in report,            "FAIL: Report missing Q_SCORE section"
    assert "VOLATILITY"   in report,            "FAIL: Report missing VOLATILITY section"
    assert "REGIME"       in report,            "FAIL: Report missing REGIME section"

    q = result["toxicity"]["Q_Score"]
    assert 0.0 <= q <= 1.0,                     f"FAIL: Q_Score {q} out of [0,1] range"

    regime = result["regime"]["regime"]
    assert regime in ("NORMAL", "ELEVATED"),    f"FAIL: Expected low-stress regime, got '{regime}'"

    print(f"\n  ✅ TEST 1 PASSED — Regime={regime}, Q_Score={q:.4f}")


# =============================================================================
# TEST 2: Heavy Noise regime detection
# =============================================================================
def test_agent1_heavy_noise():
    print("\n" + "="*68)
    print("  TEST 2/3 — Agent 1 | HEAVY_NOISE Regime")
    print("="*68)

    df     = _make_dummy_df(n_rows=300, regime="HEAVY_NOISE", seed=99)
    agent  = DataAnalystAgent(verbose=True)
    result = agent.run(df)

    q      = result["toxicity"]["Q_Score"]
    regime = result["regime"]["regime"]
    rec_f  = result["regime"]["recommended_filter"]

    # Heavy noise should produce a higher Q_Score than normal
    assert q > 0.05,           f"FAIL: Expected elevated Q_Score for HEAVY_NOISE, got {q:.4f}"
    assert rec_f is not None,  "FAIL: Missing recommended_filter in regime output"

    print(f"\n  ✅ TEST 2 PASSED — Regime={regime}, Q_Score={q:.4f}, Filter={rec_f}")


# =============================================================================
# TEST 3: Validation failure — too few rows
# =============================================================================
def test_agent1_validation_failure():
    print("\n" + "="*68)
    print("  TEST 3/3 — Agent 1 | Validation: Too Few Rows (should raise)")
    print("="*68)

    df_tiny = _make_dummy_df(n_rows=5)
    agent   = DataAnalystAgent(verbose=True)

    try:
        agent.run(df_tiny)
        print("  ❌ TEST 3 FAILED — Expected ValueError, got no exception")
        return False
    except ValueError as e:
        print(f"  ✅ TEST 3 PASSED — ValueError correctly raised: {e}")
        return True


# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("\n" + "█"*68)
    print("  THE QUANT COUNCIL — UNIT TESTS: AGENT 1 (DataAnalystAgent)")
    print("█"*68)

    passed = 0
    total  = 3

    try:
        test_agent1_normal_regime()
        passed += 1
    except AssertionError as e:
        print(f"  ❌ TEST 1 FAILED: {e}")

    try:
        test_agent1_heavy_noise()
        passed += 1
    except AssertionError as e:
        print(f"  ❌ TEST 2 FAILED: {e}")

    try:
        if test_agent1_validation_failure():
            passed += 1
    except Exception as e:
        print(f"  ❌ TEST 3 FAILED: {e}")

    print(f"\n{'='*68}")
    print(f"  AGENT 1 TESTS: {passed}/{total} PASSED")
    print(f"{'='*68}\n")
