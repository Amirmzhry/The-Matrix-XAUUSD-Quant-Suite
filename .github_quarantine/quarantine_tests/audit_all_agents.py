# =============================================================================
# audit_all_agents.py -- Project-Wide Gemini Agent Live API Audit
# The Quant Council
# =============================================================================
# Imports every agent, instantiates it, makes a live Gemini API call
# via the shared llm_client (which uses ClientOptions / AQ. key fix),
# and prints a clear PASS/FAIL scorecard.
#
# Usage: .venv\Scripts\python.exe audit_all_agents.py
# EXIT CODE: 0 if all agents pass, 1 if any fail
# =============================================================================
import os
import sys
import time

# STEP 1: Purge ADC / OAuth2 credentials BEFORE any google import
for _v in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
           "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    os.environ.pop(_v, None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# STEP 2: Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    _env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_env):
        with open(_env) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _, _v2 = _line.partition("=")
                    os.environ.setdefault(_k.strip(), _v2.strip().strip('"').strip("'"))

# STEP 3: Verify key before starting
api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key or (not api_key.startswith("AIza") and not api_key.startswith("AQ.")):
    print("[FATAL] GEMINI_API_KEY not found or invalid format.")
    print("        Set it in .env: GEMINI_API_KEY=AQ.<your_key>")
    sys.exit(1)

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# Shared call_gemini from llm_client (ClientOptions auth is baked in)
from src.core.llm_client import call_gemini

SEP = "=" * 65
results = []


def _make_minimal_df(n: int = 100) -> pd.DataFrame:
    """Tiny synthetic tick DataFrame for agent instantiation/test calls."""
    np.random.seed(0)
    base = datetime(2025, 1, 6, 10, 0, 0, tzinfo=timezone.utc)
    times = [base + timedelta(milliseconds=i * 100) for i in range(n)]
    bids  = 2350.0 + np.random.randn(n).cumsum() * 0.1
    asks  = bids + np.random.uniform(0.01, 0.05, n)
    return pd.DataFrame({
        "DateTime":    pd.to_datetime(times),
        "Bid":         bids,
        "Ask":         asks,
        "Tick_Volume": np.random.poisson(10, n).astype(float),
    })


def audit(agent_name: str, fn) -> bool:
    """Runs fn(), records result, prints PASS/FAIL."""
    t0 = time.time()
    try:
        result = fn()
        ms = (time.time() - t0) * 1000
        snippet = str(result)[:80].replace("\n", " ")
        print(f"  [PASS]  {agent_name:<30}  ({ms:.0f}ms)  -> {snippet}")
        results.append((True, agent_name))
        return True
    except Exception as e:
        ms = (time.time() - t0) * 1000
        print(f"  [FAIL]  {agent_name:<30}  ({ms:.0f}ms)")
        print(f"          ERROR: {e}")
        results.append((False, agent_name))
        return False


print(f"\n{SEP}")
print(f"  THE QUANT COUNCIL -- PROJECT-WIDE AGENT API AUDIT")
print(f"  API Key: {api_key[:6]}...{api_key[-4:]}  |  Model: gemini-2.5-flash")
print(f"{SEP}\n")


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 0: Baseline llm_client connectivity (fastest sanity check)
# ─────────────────────────────────────────────────────────────────────────────
print("  Phase 0: LLM Client baseline connectivity")
print(f"  {'-'*62}")

def _t0():
    resp = call_gemini(
        "System check. Reply with exactly: OK",
        temperature=0.0,
        max_retries=2,
    )
    assert "OK" in resp.upper(), f"Unexpected: '{resp}'"
    return resp.strip()

audit("llm_client.call_gemini", _t0)

print()

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 1: DataAnalystAgent
# ─────────────────────────────────────────────────────────────────────────────
print("  Phase 1: DataAnalystAgent (Agent 1)")
print(f"  {'-'*62}")

def _t1_import():
    from src.agents.agent1_data_analyst import DataAnalystAgent
    agent = DataAnalystAgent(verbose=False)
    assert agent.AGENT_NAME == "DataAnalystAgent"
    return "Instantiated OK"

def _t1_api():
    from src.agents.agent1_data_analyst import DataAnalystAgent
    agent = DataAnalystAgent(verbose=False)
    df    = _make_minimal_df(200)
    out   = agent.run(df)
    assert "report_text" in out, "Missing report_text in output"
    assert "toxicity"    in out, "Missing toxicity in output"
    assert "regime"      in out, "Missing regime in output"
    regime = out["regime"].get("regime", "UNKNOWN")
    return f"report_text len={len(out['report_text'])} | regime={regime}"

audit("DataAnalystAgent  [import+instantiate]", _t1_import)
audit("DataAnalystAgent  [live API call]",      _t1_api)
print()

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 2: LeadQuantAgent
# ─────────────────────────────────────────────────────────────────────────────
print("  Phase 2: LeadQuantAgent (Agent 2)")
print(f"  {'-'*62}")

def _t2_import():
    from src.agents.agent2_lead_quant import LeadQuantAgent, VALID_FILTERS
    agent = LeadQuantAgent(verbose=False)
    assert len(VALID_FILTERS) == 5, f"Expected 5 filters, got {len(VALID_FILTERS)}"
    return f"Instantiated OK | {len(VALID_FILTERS)} filters"

def _t2_api():
    from src.agents.agent1_data_analyst import DataAnalystAgent
    from src.agents.agent2_lead_quant   import LeadQuantAgent
    df      = _make_minimal_df(200)
    analyst = DataAnalystAgent(verbose=False)
    a_out   = analyst.run(df)
    quant   = LeadQuantAgent(verbose=False)
    q_out   = quant.run(df, a_out, rejected_filters=[], iteration=1)
    assert "filter_name"     in q_out, "Missing filter_name"
    assert "inner_monologue" in q_out, "Missing inner_monologue"
    assert "params"          in q_out, "Missing params"
    return f"filter={q_out['filter_name']} | params={list(q_out['params'].keys())}"

audit("LeadQuantAgent    [import+instantiate]", _t2_import)
audit("LeadQuantAgent    [live API call]",      _t2_api)
print()

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 3: RiskOfficerAgent
# ─────────────────────────────────────────────────────────────────────────────
print("  Phase 3: RiskOfficerAgent (Agent 3)")
print(f"  {'-'*62}")

def _t3_import():
    from src.agents.agent3_risk_officer import RiskOfficerAgent, RiskVetoException
    agent = RiskOfficerAgent(verbose=False)
    # Verify hard floor constants exist
    assert hasattr(agent, "MAX_VARIANCE_SHIFT"), "Missing MAX_VARIANCE_SHIFT"
    assert hasattr(agent, "MAX_RMSE"),           "Missing MAX_RMSE"
    return f"Instantiated OK | MAX_VARIANCE_SHIFT={agent.MAX_VARIANCE_SHIFT}"

def _t3_api():
    from src.agents.agent1_data_analyst import DataAnalystAgent
    from src.agents.agent2_lead_quant   import LeadQuantAgent
    from src.agents.agent3_risk_officer import RiskOfficerAgent
    df       = _make_minimal_df(200)
    a_out    = DataAnalystAgent(verbose=False).run(df)
    q_out    = LeadQuantAgent(verbose=False).run(df, a_out, iteration=1)
    filt_df  = q_out["filtered_df"]
    params   = q_out["params"]
    risk     = RiskOfficerAgent(verbose=False)
    verdict  = risk.evaluate(df, filt_df, params)
    assert "verdict"    in verdict, "Missing verdict"
    assert "var_shift"  in verdict, "Missing var_shift"
    return f"verdict={verdict['verdict']} | var_shift={verdict['var_shift']:.3f}%"

audit("RiskOfficerAgent  [import+instantiate]", _t3_import)
audit("RiskOfficerAgent  [live API call]",      _t3_api)
print()

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 4: VisualizerAgent (no live LLM call — pure Plotly)
# ─────────────────────────────────────────────────────────────────────────────
print("  Phase 4: VisualizerAgent (Agent 4 -- Plotly, no LLM call)")
print(f"  {'-'*62}")

def _t4_import():
    from src.agents.agent4_visualizer import VisualizerAgent
    agent = VisualizerAgent(output_dir="output", verbose=False)
    return "Instantiated OK"

def _t4_charts():
    from src.agents.agent1_data_analyst import DataAnalystAgent
    from src.agents.agent2_lead_quant   import LeadQuantAgent
    from src.agents.agent3_risk_officer import RiskOfficerAgent
    from src.agents.agent4_visualizer   import VisualizerAgent
    os.makedirs("output", exist_ok=True)
    df      = _make_minimal_df(200)
    a_out   = DataAnalystAgent(verbose=False).run(df)
    q_out   = LeadQuantAgent(verbose=False).run(df, a_out, iteration=1)
    filt_df = q_out["filtered_df"]
    params  = q_out["params"]
    approved = RiskOfficerAgent(verbose=False).evaluate(df, filt_df, params)
    viz_out = VisualizerAgent(output_dir="output", verbose=False).run(
        df, filt_df, approved, a_out, pipeline_log=[]
    )
    chart_paths = viz_out.get("chart_paths", {})
    return f"{len(chart_paths)} charts generated: {list(chart_paths.keys())}"

audit("VisualizerAgent   [import+instantiate]", _t4_import)
audit("VisualizerAgent   [chart generation]",  _t4_charts)
print()

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT 5: MQL5SynthesizerAgent
# ─────────────────────────────────────────────────────────────────────────────
print("  Phase 5: MQL5SynthesizerAgent (Agent 5)")
print(f"  {'-'*62}")

def _t5_import():
    from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent
    agent = MQL5SynthesizerAgent(output_dir="output", verbose=False)
    return "Instantiated OK"

def _t5_api():
    from src.agents.agent1_data_analyst     import DataAnalystAgent
    from src.agents.agent2_lead_quant       import LeadQuantAgent
    from src.agents.agent3_risk_officer     import RiskOfficerAgent
    from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent
    os.makedirs("output", exist_ok=True)
    df      = _make_minimal_df(200)
    a_out   = DataAnalystAgent(verbose=False).run(df)
    q_out   = LeadQuantAgent(verbose=False).run(df, a_out, iteration=1)
    filt_df = q_out["filtered_df"]
    params  = q_out["params"]
    approved = RiskOfficerAgent(verbose=False).evaluate(df, filt_df, params)
    mql5_out = MQL5SynthesizerAgent(output_dir="output", verbose=False).run(
        approved, output_filename="HFT_Tick_Factory.mqh"
    )
    assert "filepath"     in mql5_out, "Missing filepath"
    assert "audit_passed" in mql5_out, "Missing audit_passed"
    return (f"gemini_used={mql5_out.get('gemini_used')} | "
            f"audit={'PASSED' if mql5_out['audit_passed'] else 'WARNED'} | "
            f"file={os.path.basename(mql5_out['filepath'])}")

audit("MQL5SynthesizerAgent [import+instantiate]", _t5_import)
audit("MQL5SynthesizerAgent [live API call]",      _t5_api)
print()

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SCORECARD
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)

print(SEP)
print(f"  AUDIT SCORECARD: {passed}/{len(results)} PASSED | {failed} FAILED")
print(SEP)

if failed == 0:
    print("""
  ALL AGENTS OPERATIONAL
  The Quant Council pipeline is fully authenticated and ready.
  Run: .venv\\Scripts\\python.exe master_pipeline.py --mode synthetic
""")
else:
    print("\n  FAILURES DETECTED:\n")
    for ok, name in results:
        if not ok:
            print(f"    [FAIL] {name}")
    print()

print(SEP + "\n")
sys.exit(0 if failed == 0 else 1)
