# =============================================================================
# tests/test_agent3.py — Unit Test: RiskOfficerAgent
# The Quant Council
# =============================================================================
# Verifies that Agent 3:
#   - APPROVES a properly filtered dataset
#   - REJECTS a badly over-filtered dataset (raises RiskVetoException)
#   - REJECTS data with negative spreads
#   - Reports correct variance shift values
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.agents.agent3_risk_officer import RiskOfficerAgent, RiskVetoException


def _make_raw_df(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Raw tick DataFrame with realistic XAUUSD noise."""
    np.random.seed(seed)
    start = datetime(2025, 1, 6, 10, 0, 0)
    times = [start + timedelta(milliseconds=i * 100) for i in range(n)]
    bids  = 2000.0 + np.random.randn(n).cumsum() * 0.6
    # Inject 10 hard spikes
    spike_idx = np.random.choice(n, size=10, replace=False)
    bids[spike_idx] += np.random.randn(10) * 4.0
    spreads = np.random.uniform(0.01, 0.05, n)
    asks    = bids + spreads
    return pd.DataFrame({'DateTime': times, 'Bid': bids, 'Ask': asks})


def _apply_good_filter(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Applies a light MAD clip — should pass risk checks."""
    df = df_raw.copy()
    prices = df['Bid'].values
    med    = np.median(prices)
    mad    = np.median(np.abs(prices - med))
    safe   = max(mad, 0.05)
    # Gentle 4.0x MAD clip — minimal variance destruction
    df['Bid'] = np.clip(prices, med - 4.0 * safe, med + 4.0 * safe)
    return df


def _apply_bad_filter(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Applies an extreme flattening — replaces all Bid with constant mean.
    This DESTROYS variance (100% shift) and should be rejected.
    """
    df = df_raw.copy()
    df['Bid'] = df['Bid'].mean()   # Constant price = zero variance
    return df


def _apply_negative_spread_filter(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a filtered df where Bid > Ask (negative spread) — corrupt data.
    """
    df = df_raw.copy()
    df['Bid'] = df['Ask'] + 0.10   # Bid intentionally above Ask
    return df


# =============================================================================
# TEST 1: Good filter → should be APPROVED
# =============================================================================
def test_agent3_approves_good_filter():
    print("\n" + "="*68)
    print("  TEST 1/3 — Agent 3 | APPROVE a properly filtered dataset")
    print("="*68)

    df_raw      = _make_raw_df(n=500)
    df_filtered = _apply_good_filter(df_raw)
    params      = {"filter": "MAD", "mad_threshold": 4.0, "tolerance": 0.05}

    agent  = RiskOfficerAgent(verbose=True)
    result = agent.evaluate(df_raw, df_filtered, params)

    assert result["verdict"] == "APPROVED",          "FAIL: Expected APPROVED verdict"
    assert "metrics"         in result,              "FAIL: Missing 'metrics' in result"
    assert "var_shift"       in result,              "FAIL: Missing 'var_shift' in result"
    assert result["var_shift"] < 20.0,               f"FAIL: var_shift {result['var_shift']:.2f}% should be < 20%"

    print(f"\n  ✅ TEST 1 PASSED — Verdict: APPROVED, Var Shift: {result['var_shift']:.4f}%")


# =============================================================================
# TEST 2: Bad filter (variance destroyed) → should REJECT
# =============================================================================
def test_agent3_rejects_bad_filter():
    print("\n" + "="*68)
    print("  TEST 2/3 — Agent 3 | REJECT over-filtered (constant) dataset")
    print("="*68)

    df_raw      = _make_raw_df(n=500)
    df_bad      = _apply_bad_filter(df_raw)
    params      = {"filter": "MAD", "mad_threshold": 0.001}

    agent = RiskOfficerAgent(verbose=True)

    try:
        agent.evaluate(df_raw, df_bad, params)
        print("  ❌ TEST 2 FAILED — Expected RiskVetoException but got no exception")
        return False
    except RiskVetoException as e:
        assert "VETO" in str(e),                     f"FAIL: Exception message should contain 'VETO', got: {e}"
        assert e.metrics is not None,                "FAIL: Exception should carry metrics dict"
        var_shift = e.metrics.get("var_shift_pct", 0)
        assert var_shift >= 20.0,                    f"FAIL: var_shift should be >= 20%, got {var_shift}"
        print(f"  ✅ TEST 2 PASSED — RiskVetoException raised correctly.")
        print(f"     Reason: {e.reason}")
        print(f"     Var Shift in metrics: {var_shift:.2f}%")
        return True


# =============================================================================
# TEST 3: Negative spreads → should REJECT
# =============================================================================
def test_agent3_rejects_negative_spreads():
    print("\n" + "="*68)
    print("  TEST 3/3 — Agent 3 | REJECT dataset with negative spreads")
    print("="*68)

    df_raw    = _make_raw_df(n=300)
    df_corrupt = _apply_negative_spread_filter(df_raw)
    params    = {"filter": "HAMPEL", "half_window": 15, "k_sigma": 3.0}

    agent = RiskOfficerAgent(verbose=True)

    try:
        agent.evaluate(df_raw, df_corrupt, params)
        print("  ❌ TEST 3 FAILED — Expected RiskVetoException but got no exception")
        return False
    except RiskVetoException as e:
        assert "VETO" in str(e),          f"FAIL: Exception should say VETO, got: {e}"
        neg = e.metrics.get("neg_spreads", 0)
        print(f"  ✅ TEST 3 PASSED — Negative spread veto fired correctly.")
        print(f"     Negative spreads detected: {neg}")
        return True


# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("\n" + "█"*68)
    print("  THE QUANT COUNCIL — UNIT TESTS: AGENT 3 (RiskOfficerAgent)")
    print("█"*68)

    passed = 0
    total  = 3

    try:
        test_agent3_approves_good_filter()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 1 FAILED: {e}")

    try:
        if test_agent3_rejects_bad_filter():
            passed += 1
    except Exception as e:
        print(f"  ❌ TEST 2 FAILED: {e}")

    try:
        if test_agent3_rejects_negative_spreads():
            passed += 1
    except Exception as e:
        print(f"  ❌ TEST 3 FAILED: {e}")

    print(f"\n{'='*68}")
    print(f"  AGENT 3 TESTS: {passed}/{total} PASSED")
    print(f"{'='*68}\n")
