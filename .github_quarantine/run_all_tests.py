"""
run_all_tests.py — The Quant Council: Combined Test Runner
Runs all 5 agent unit tests + the end-to-end pipeline in one shot.
Usage: python run_all_tests.py
"""
import sys
import os
import traceback

# Add project root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

results = {}

# ═══════════════════════════════════════════════════════════
# AGENT 1 TESTS
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  RUNNING: AGENT 1 UNIT TESTS (DataAnalystAgent)")
print("█"*68)
try:
    from tests.test_agent1 import (
        test_agent1_normal_regime,
        test_agent1_heavy_noise,
        test_agent1_validation_failure,
    )
    p = 0
    for fn in [test_agent1_normal_regime, test_agent1_heavy_noise, test_agent1_validation_failure]:
        try:
            r = fn()
            p += 1 if r is not False else 0
        except AssertionError as e:
            print(f"  ❌ {fn.__name__}: {e}")
        except Exception as e:
            print(f"  ❌ {fn.__name__}: {e}")
    results["Agent1"] = f"{p}/3"
except Exception as e:
    print(f"  ❌ Agent 1 import failed: {e}")
    traceback.print_exc()
    results["Agent1"] = "IMPORT_ERROR"

# ═══════════════════════════════════════════════════════════
# AGENT 2 TESTS
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  RUNNING: AGENT 2 UNIT TESTS (LeadQuantAgent)")
print("█"*68)
try:
    from tests.test_agent2 import (
        test_agent2_basic_execution,
        test_agent2_inner_monologue_heavy_noise,
        test_agent2_rejection_escalation,
    )
    p = 0
    for fn in [test_agent2_basic_execution, test_agent2_inner_monologue_heavy_noise, test_agent2_rejection_escalation]:
        try:
            fn()
            p += 1
        except (AssertionError, Exception) as e:
            print(f"  ❌ {fn.__name__}: {e}")
    results["Agent2"] = f"{p}/3"
except Exception as e:
    print(f"  ❌ Agent 2 import failed: {e}")
    traceback.print_exc()
    results["Agent2"] = "IMPORT_ERROR"

# ═══════════════════════════════════════════════════════════
# AGENT 3 TESTS
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  RUNNING: AGENT 3 UNIT TESTS (RiskOfficerAgent)")
print("█"*68)
try:
    from tests.test_agent3 import (
        test_agent3_approves_good_filter,
        test_agent3_rejects_bad_filter,
        test_agent3_rejects_negative_spreads,
    )
    p = 0
    for fn in [test_agent3_approves_good_filter, test_agent3_rejects_bad_filter, test_agent3_rejects_negative_spreads]:
        try:
            r = fn()
            p += 1 if r is not False else 0
        except (AssertionError, Exception) as e:
            print(f"  ❌ {fn.__name__}: {e}")
    results["Agent3"] = f"{p}/3"
except Exception as e:
    print(f"  ❌ Agent 3 import failed: {e}")
    traceback.print_exc()
    results["Agent3"] = "IMPORT_ERROR"

# ═══════════════════════════════════════════════════════════
# AGENT 4 TESTS
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  RUNNING: AGENT 4 UNIT TESTS (VisualizerAgent)")
print("█"*68)
try:
    import plotly  # noqa
    from tests.test_agent4 import (
        test_agent4_generates_three_charts,
        test_agent4_default_timeline,
    )
    p = 0
    for fn in [test_agent4_generates_three_charts, test_agent4_default_timeline]:
        try:
            fn()
            p += 1
        except (AssertionError, Exception) as e:
            print(f"  ❌ {fn.__name__}: {e}")
            traceback.print_exc()
    results["Agent4"] = f"{p}/2"
except ImportError:
    print("  ⚠️  Plotly not installed — skipping Agent 4 tests")
    results["Agent4"] = "SKIPPED (no plotly)"

# ═══════════════════════════════════════════════════════════
# AGENT 5 TESTS
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  RUNNING: AGENT 5 UNIT TESTS (MQL5SynthesizerAgent)")
print("█"*68)
try:
    from tests.test_agent5 import (
        test_agent5_all_filters,
        test_agent5_inner_monologue,
    )
    p = 0
    for fn in [test_agent5_all_filters, test_agent5_inner_monologue]:
        try:
            fn()
            p += 1
        except (AssertionError, Exception) as e:
            print(f"  ❌ {fn.__name__}: {e}")
            traceback.print_exc()
    results["Agent5"] = f"{p}/2"
except Exception as e:
    print(f"  ❌ Agent 5 import failed: {e}")
    traceback.print_exc()
    results["Agent5"] = "IMPORT_ERROR"

# ═══════════════════════════════════════════════════════════
# END-TO-END PIPELINE TEST
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  RUNNING: END-TO-END PIPELINE (master_pipeline.py)")
print("  Regime: HEAVY_NOISE | Rows: 2000")
print("█"*68)
try:
    from src.core.master_pipeline import QuantCouncilPipeline, generate_synthetic_data

    df = generate_synthetic_data(n_rows=2000, regime="HEAVY_NOISE", seed=42)
    pipeline = QuantCouncilPipeline(output_dir="output", verbose=True)
    result = pipeline.run(df, mode="synthetic", regime="HEAVY_NOISE")

    assert result.get("verdict") in ("APPROVED", "RECOVERED"), \
        f"Pipeline returned unexpected verdict: {result.get('verdict')}"
    assert result.get("filtered_df") is not None, "No filtered_df in result"
    assert len(result.get("chart_paths", {})) >= 0, "chart_paths missing"

    results["Pipeline_E2E"] = f"✅ {result['verdict']} | Filter={result['filter_applied']}"
except Exception as e:
    print(f"  ❌ E2E Pipeline failed: {e}")
    traceback.print_exc()
    results["Pipeline_E2E"] = f"FAILED: {e}"

# ═══════════════════════════════════════════════════════════
# FINAL SCORECARD
# ═══════════════════════════════════════════════════════════
print("\n" + "█"*68)
print("  THE QUANT COUNCIL — FINAL TEST SCORECARD")
print("█"*68)
for agent, score in results.items():
    icon = "✅" if "FAILED" not in str(score) and "ERROR" not in str(score) else "❌"
    print(f"  {icon}  {agent:<20}  {score}")
print("█"*68 + "\n")
