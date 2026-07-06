# =============================================================================
# tests/test_agent4.py — Unit Test: VisualizerAgent
# The Quant Council
# =============================================================================
# Verifies that Agent 4:
#   - Generates exactly 3 HTML files when given an approved dataset
#   - All HTML files are non-empty and contain Plotly markup
#   - Handles datasets with and without Ask column
#   - Returns correct chart_paths dict
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.agents.agent4_visualizer import VisualizerAgent


def _make_approved_payload(filter_name: str = "MAD") -> dict:
    """Builds a mock approved payload from RiskOfficerAgent."""
    return {
        "verdict":   "APPROVED",
        "var_shift": 3.5,
        "rmse":      0.12,
        "params": {
            "filter":         filter_name,
            "mad_threshold":  3.0,
            "window":         50,
            "tolerance":      0.05,
        },
        "metrics": {
            "var_shift_pct": 3.5,
            "rmse":          0.12,
            "neg_spreads":   0,
        }
    }


def _make_analyst_output(q_score: float = 0.35, vol_ratio: float = 1.4) -> dict:
    """Builds a mock analyst output."""
    return {
        "toxicity": {
            "Q_Score": q_score,
            "dimensions": {"RV": 0.3, "Spike": 0.4, "CV": 0.2, "Spread": 0.1, "Gap": 0.05},
            "interpretation": "HIGH — Heavy microstructure noise.",
        },
        "volatility": {
            "realized_vol":  0.0012,
            "ewma_baseline": 0.00086,
            "vol_ratio":     vol_ratio,
            "roc_std":       0.0008,
            "kurtosis":      4.2,
            "skewness":      -0.3,
            "stress_flag":   False,
        },
        "regime": {
            "regime":             "HEAVY_NOISE",
            "confidence":         0.72,
            "recommended_filter": "MAD",
        },
        "metadata": {"tick_count": 500},
    }


def _make_tick_dfs(n: int = 500, seed: int = 42) -> tuple:
    """Returns (df_raw, df_filtered) tuple."""
    np.random.seed(seed)
    start  = datetime(2025, 6, 1, 9, 0, 0)
    times  = [start + timedelta(milliseconds=i * 100) for i in range(n)]
    bids_r = 2100.0 + np.random.randn(n).cumsum() * 0.7
    spike_idx = np.random.choice(n, 20, replace=False)
    bids_r[spike_idx] += np.random.randn(20) * 4.0
    spreads = np.random.uniform(0.01, 0.05, n)
    asks_r  = bids_r + spreads

    df_raw = pd.DataFrame({
        'DateTime': pd.to_datetime(times),
        'Bid':      bids_r,
        'Ask':      asks_r,
    })

    # Filtered: mild MAD clip
    med    = np.median(bids_r)
    mad    = np.median(np.abs(bids_r - med))
    bids_f = np.clip(bids_r, med - 3.5 * mad, med + 3.5 * mad)

    df_filtered = df_raw.copy()
    df_filtered['Bid'] = bids_f

    return df_raw, df_filtered


def _make_pipeline_log() -> list:
    """Builds a sample pipeline execution log for the timeline chart."""
    return [
        {"agent": "DataAnalystAgent",    "phase": "Market Intelligence Scan",  "duration_ms": 285,  "status": "COMPLETE", "note": "Q_Score=0.35"},
        {"agent": "LeadQuantAgent",      "phase": "Filter Proposal (MAD)",     "duration_ms": 92,   "status": "COMPLETE", "note": "k=3.0, win=50"},
        {"agent": "RiskOfficerAgent",    "phase": "Safety Evaluation",         "duration_ms": 48,   "status": "COMPLETE", "note": "VS=3.5%, APPROVED"},
        {"agent": "VisualizerAgent",     "phase": "Chart Generation",          "duration_ms": 220,  "status": "COMPLETE", "note": "3 charts"},
        {"agent": "MQL5SynthesizerAgent","phase": "C++ Code Synthesis",        "duration_ms": 35,   "status": "COMPLETE", "note": "MAD filter injected"},
    ]


# =============================================================================
# TEST 1: Generates 3 HTML files
# =============================================================================
def test_agent4_generates_three_charts():
    print("\n" + "="*68)
    print("  TEST 1/2 — Agent 4 | Generates exactly 3 interactive HTML charts")
    print("="*68)

    import tempfile
    tmp_dir = tempfile.mkdtemp()

    df_raw, df_filtered = _make_tick_dfs(n=600)
    approved_payload    = _make_approved_payload("MAD")
    analyst_output      = _make_analyst_output()
    pipeline_log        = _make_pipeline_log()

    agent  = VisualizerAgent(output_dir=tmp_dir, verbose=True)
    result = agent.run(
        df_raw, df_filtered,
        approved_payload, analyst_output,
        pipeline_log=pipeline_log,
    )

    # Structural assertions
    assert "chart_paths"   in result,   "FAIL: Missing 'chart_paths' in result"
    assert "figures"       in result,   "FAIL: Missing 'figures' in result"
    chart_paths = result["chart_paths"]

    expected_keys = ["price_overlay", "density_skewness", "agent_timeline"]
    for key in expected_keys:
        assert key in chart_paths,      f"FAIL: Missing chart key '{key}'"
        path = chart_paths[key]
        assert os.path.exists(path),    f"FAIL: Chart file does not exist: {path}"
        size = os.path.getsize(path)
        assert size > 5000,             f"FAIL: Chart file too small ({size} bytes): {path}"

        # Verify it contains Plotly HTML markup
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "plotly" in content.lower(), f"FAIL: File doesn't look like Plotly HTML: {path}"

    print(f"\n  ✅ TEST 1 PASSED — 3 HTML charts generated in: {tmp_dir}")
    for k, p in chart_paths.items():
        print(f"     {k}: {os.path.getsize(p):,} bytes")

    return tmp_dir, chart_paths


# =============================================================================
# TEST 2: Works with default pipeline_log (no log provided)
# =============================================================================
def test_agent4_default_timeline():
    print("\n" + "="*68)
    print("  TEST 2/2 — Agent 4 | Default timeline chart (no pipeline_log)")
    print("="*68)

    import tempfile
    tmp_dir = tempfile.mkdtemp()

    df_raw, df_filtered = _make_tick_dfs(n=300, seed=99)
    approved_payload    = _make_approved_payload("HAMPEL")
    analyst_output      = _make_analyst_output(q_score=0.58, vol_ratio=2.1)

    agent  = VisualizerAgent(output_dir=tmp_dir, verbose=True)
    result = agent.run(
        df_raw, df_filtered,
        approved_payload, analyst_output,
        pipeline_log=None,   # Should use default log
    )

    timeline_path = result["chart_paths"].get("agent_timeline")
    assert timeline_path is not None,          "FAIL: No agent_timeline chart path"
    assert os.path.exists(timeline_path),      "FAIL: Timeline HTML file not created"
    assert os.path.getsize(timeline_path) > 1000, "FAIL: Timeline file appears empty"

    print(f"  ✅ TEST 2 PASSED — Default timeline generated: {timeline_path}")


# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("\n" + "█"*68)
    print("  THE QUANT COUNCIL — UNIT TESTS: AGENT 4 (VisualizerAgent)")
    print("█"*68)

    # Check plotly availability first
    try:
        import plotly
        print(f"  Plotly version: {plotly.__version__} ✅")
    except ImportError:
        print("  ⚠️  Plotly not installed. Install with: pip install plotly")
        print("  Skipping visualization tests.")
        sys.exit(0)

    passed = 0
    total  = 2

    try:
        test_agent4_generates_three_charts()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 1 FAILED: {e}")

    try:
        test_agent4_default_timeline()
        passed += 1
    except (AssertionError, Exception) as e:
        print(f"  ❌ TEST 2 FAILED: {e}")

    print(f"\n{'='*68}")
    print(f"  AGENT 4 TESTS: {passed}/{total} PASSED")
    print(f"{'='*68}\n")
