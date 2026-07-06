# smoke_test.py -- Import & unit checks for The Quant Council (Gemini refactor)
# Run with:  .venv\Scripts\python.exe smoke_test.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "OK"
FAIL = "FAIL"
results = []

def check(label, fn):
    try:
        fn()
        results.append((PASS, label))
        print(f"  [PASS] {label}")
    except Exception as e:
        results.append((FAIL, f"{label}"))
        print(f"  [FAIL] {label}")
        print(f"         {e}")

print("\n" + "="*60)
print("  THE QUANT COUNCIL -- SMOKE TEST")
print("="*60 + "\n")

def _t1():
    from llm_client import call_gemini, extract_json, get_client
check("llm_client imports (call_gemini, extract_json, get_client)", _t1)

def _t2():
    from llm_client import extract_json
    r = extract_json('{"verdict": "APPROVED"}')
    assert r.get("verdict") == "APPROVED", r
check("extract_json: bare JSON object", _t2)

def _t3():
    from llm_client import extract_json
    r = extract_json("```json\n{\"filter_name\": \"MAD\"}\n```")
    assert r.get("filter_name") == "MAD", r
check("extract_json: markdown fenced JSON", _t3)

def _t4():
    from llm_client import extract_json
    r = extract_json('Here: {"key": 42} end.')
    assert r.get("key") == 42, r
check("extract_json: JSON embedded in prose", _t4)

def _t5():
    from llm_client import extract_json
    r = extract_json("no json here at all")
    assert r == {}, r
check("extract_json: graceful empty return on no JSON", _t5)

def _t6():
    from src.agents.agent1_data_analyst import DataAnalystAgent
    a = DataAnalystAgent(verbose=False)
    assert hasattr(a, "run")
    assert hasattr(a, "SYSTEM_PROMPT")
    assert hasattr(a, "USER_PROMPT_TEMPLATE")
check("Agent1 DataAnalystAgent instantiation + attributes", _t6)

def _t7():
    from src.agents.agent2_lead_quant import LeadQuantAgent, VALID_FILTERS
    a = LeadQuantAgent(verbose=False)
    assert "ADAPTIVE_KALMAN" in VALID_FILTERS
    assert "MAD" in VALID_FILTERS
    assert "HAMPEL" in VALID_FILTERS
    assert "EMA_ZSCORE" in VALID_FILTERS
    assert "DEEP_DENOISE_HAMPEL_KALMAN" in VALID_FILTERS
    assert hasattr(a, "run")
check("Agent2 LeadQuantAgent + VALID_FILTERS (5 entries)", _t7)

def _t8():
    from src.agents.agent2_lead_quant import LeadQuantAgent
    a = LeadQuantAgent(verbose=False)
    fake_analyst = {
        "report_text": "Some report.",
        "regime":     {"regime": "HEAVY_NOISE", "confidence": 0.9},
        "toxicity":   {"Q_Score": 0.6, "dimensions": {"Spike": 0.7, "CV": 0.3}},
        "volatility": {"vol_ratio": 2.0, "kurtosis": 5.0},
    }
    result = a._fallback_decide(fake_analyst, [], iteration=1)
    assert result["filter_name"] in ("MAD", "HAMPEL", "EMA_ZSCORE", "ADAPTIVE_KALMAN", "DEEP_DENOISE_HAMPEL_KALMAN")
    assert "filter" in result["parameters"]
check("Agent2 _fallback_decide returns valid filter+params", _t8)

def _t9():
    from src.agents.agent3_risk_officer import RiskOfficerAgent
    a = RiskOfficerAgent(verbose=False)
    assert a.MAX_VARIANCE_SHIFT == 20.0
    assert a.MAX_RMSE == 5.0
    assert a.MAX_NEGATIVE_SPREADS == 0
    assert a.MAX_MEAN_DRIFT_PCT == 0.005
check("Agent3 RiskOfficerAgent hard floor constants", _t9)

def _t10():
    import pandas as pd
    from src.agents.agent3_risk_officer import RiskOfficerAgent
    a = RiskOfficerAgent(verbose=False)
    raw  = pd.DataFrame({"Bid": [100.0, 100.1, 99.9, 100.2], "Ask": [100.1, 100.2, 100.0, 100.3]})
    filt = pd.DataFrame({"Bid": [100.0, 100.1, 99.9, 100.2], "Ask": [100.1, 100.2, 100.0, 100.3]})
    m = a._compute_metrics(raw, filt)
    assert m["neg_spreads"] == 0
    assert m["rmse"] < 1e-9
check("Agent3 _compute_metrics: identical raw/filt -> RMSE~0, neg_spreads=0", _t10)

def _t11():
    from src.agents.agent3_risk_officer import RiskOfficerAgent
    a = RiskOfficerAgent(verbose=False)
    good = {"var_shift_pct": 1.0, "rmse": 0.01, "neg_spreads": 0, "mean_price_drift_pct": 0.0001}
    failures, _ = a._check_hard_limits(good)
    assert failures == [], failures
check("Agent3 _check_hard_limits: no failures on clean metrics", _t11)

def _t12():
    from src.agents.agent3_risk_officer import RiskOfficerAgent
    a = RiskOfficerAgent(verbose=False)
    bad = {"var_shift_pct": 99.0, "rmse": 9.9, "neg_spreads": 5, "mean_price_drift_pct": 0.1}
    failures, _ = a._check_hard_limits(bad)
    assert len(failures) == 4, failures
check("Agent3 _check_hard_limits: catches all 4 violations", _t12)

def _t13():
    from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent
    a = MQL5SynthesizerAgent(output_dir="output", verbose=False)
    assert hasattr(a, "run")
    assert hasattr(a, "_mql5_linter_process")
    assert hasattr(a, "_validate_code")
check("Agent5 MQL5SynthesizerAgent instantiation + attributes", _t13)

def _t14():
    from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent
    a = MQL5SynthesizerAgent(output_dir="output", verbose=False)
    code = a._generate_fallback_code(
        "MAD", {"filter": "MAD", "window": 50, "mad_threshold": 3.0, "tolerance": 0.05}, "test.mqh"
    )
    assert "CTickFactory" in code
    assert "ArrayResize" in code
    assert "ArrayFree" in code
    assert "UpdateTick" in code
    assert "#property strict" in code
check("Agent5 fallback code generator: MAD -> valid MQL5 structure", _t14)

def _t15():
    from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent
    a = MQL5SynthesizerAgent(verbose=False)
    code = (
        "#property strict\n"
        "class CTickFactory {\nprivate:\n   double m_buffer[];\npublic:\n   void Reset() {}\n};\n"
        "void CTickFactory::Reset() {\n   double temp[];\n   ArrayResize(temp, 10);\n   m_buffer = temp;\n}\n"
    )
    _, logs = a._mql5_linter_process(code)
    assert any("Rule 2" in l for l in logs), f"Linter missed array assignment. Logs: {logs}"
check("Agent5 linter: catches illegal array assignment (Rule 2)", _t15)

def _t16():
    from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent
    a = MQL5SynthesizerAgent(verbose=False)
    good = "#property strict\nclass CTickFactory {\npublic:\n   double UpdateTick(double b);\n   bool IsReady() const;\n};\nvoid ArrayResize(){} void ArrayFree(){}"
    ok, issues = a._validate_code(good)
    assert ok, issues
check("Agent5 structural validator: accepts valid MQL5 skeleton", _t16)

def _t17():
    from src.core.master_pipeline import QuantCouncilPipeline
    p = QuantCouncilPipeline(output_dir="output", verbose=False)
    assert hasattr(p, "analyst")
    assert hasattr(p, "quant")
    assert hasattr(p, "risk")
    assert hasattr(p, "visualizer")
    assert hasattr(p, "synthesizer")
    assert p.MAX_ITERATIONS == 3
check("QuantCouncilPipeline instantiation (all 5 agents)", _t17)

print("\n" + "="*60)
passed = sum(1 for s, _ in results if s == PASS)
failed = sum(1 for s, _ in results if s == FAIL)
print(f"  RESULTS: {passed}/{len(results)} passed | {failed} failed")
print("="*60 + "\n")
if failed:
    sys.exit(1)
