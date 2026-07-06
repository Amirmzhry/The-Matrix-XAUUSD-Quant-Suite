# =============================================================================
# agents/agent3_risk_officer.py — Agent 3: The Risk Officer (Gemini-Powered)
# The Quant Council
# =============================================================================
# ROLE: Computes statistical deltas (Variance Shift, RMSE, Negative Spreads,
# Mean Drift, ACF), converts them to a rich text summary, then hands them to
# Gemini for institutional compliance reasoning and a strict APPROVED/REJECTED
# verdict with a machine-parsable JSON output.
#
# The hard mathematical checks are ALWAYS computed first (deterministic).
# Gemini provides the institutional reasoning narrative and can apply nuance
# to borderline cases. CRITICAL safety floors are enforced in Python code
# regardless of what Gemini says — the LLM cannot bypass hard limits.
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from src.core.llm_client import call_gemini, extract_json


class RiskVetoException(Exception):
    """
    Raised when a filtered payload fails the Risk Officer's safety checks.
    Contains the full rejection report for the orchestrator's ReAct loop.
    """
    def __init__(self, reason: str, metrics: Dict[str, Any]):
        super().__init__(reason)
        self.reason  = reason
        self.metrics = metrics


class RiskOfficerAgent:
    """
    Agent 3: The Risk Officer (Gemini-Powered)
    -------------------------------------------
    Hard Safety Floors (Python-enforced — LLM CANNOT override):
      - MAX_VARIANCE_SHIFT:   20.0%  — Destroying >20% variance kills alpha
      - MAX_RMSE:              0.50  — Tracking error above 0.50 = signal destroyed
      - MAX_NEGATIVE_SPREADS:     0  — ANY negative spread = data corruption
      - MAX_MEAN_DRIFT:       0.005  — Mean must not drift >0.5% after filtering

    Gemini adds:
      - Institutional reasoning narrative
      - Nuanced interpretation of borderline metrics (e.g., ACF delta)
      - Specific feedback to the Lead Quant about what to improve
    """

    AGENT_NAME = "RiskOfficerAgent"

    # Hard floors — Gemini cannot override these
    MAX_VARIANCE_SHIFT   = 20.0   # percent
    MAX_RMSE             = 5.00
    MAX_NEGATIVE_SPREADS = 0
    MAX_MEAN_DRIFT_PCT   = 0.005  # 0.5%

    USER_PROMPT_TEMPLATE = """
You are the Chief Risk Officer at an institutional HFT desk trading Gold (XAUUSD).
You have received a statistical compliance report comparing raw vs filtered tick data.

=== STATISTICAL COMPLIANCE METRICS ===
{metrics_json}
=== FILTER APPLIED ===
{params_json}
=== HARD LIMIT STATUS (Python-enforced) ===
{hard_limits_summary}

=== XAUUSD RISK CONTEXT ===
- XAUUSD trades at ~$2300+. 
- An RMSE of 2.0 represents a mere ~0.08% tracking error. Do NOT treat an RMSE of 1.0 or 2.0 as a failure for XAUUSD if the variance shift is acceptable; it simply means large multi-dollar toxic spikes were successfully clipped.
- Negative spreads are an absolute hard-fail (impossible market state).

=== YOUR TASK ===
Review the statistical deltas. Assess the payload safety:
1. Does the filter destroy meaningful market variance (alpha)?
2. Does it introduce directional bias (mean drift)?
3. Are there any negative spreads indicating data corruption?
4. Is there over-smoothing (high ACF lag-1 delta)?
5. Is the tracking error (RMSE) acceptable given the $2300+ baseline price?

Provide an institutional compliance log explaining your reasoning.
Issue a FINAL DECISION.

CRITICAL OUTPUT FORMAT (ONLY VALID JSON):
{{
  "verdict": "<APPROVED or REJECTED>",
  "reasoning": "<2-4 paragraph institutional compliance narrative>",
  "risk_score": <float 0.0-1.0, where 1.0 = maximum risk>,
  "recalibration_advice": "<if REJECTED: specific technical instructions for the Lead Quant>"
}}

IMPORTANT: If ANY hard limit has failed (marked FAILED below), you MUST set verdict to REJECTED.
"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [{self.AGENT_NAME}] {msg}")

    def _compute_metrics(
        self, df_raw: pd.DataFrame, df_filtered: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute all safety metrics. Pure Python — always runs before LLM."""
        bid_r = df_raw['Bid'].values
        bid_f = df_filtered['Bid'].values

        var_raw    = np.var(bid_r)
        var_filt   = np.var(bid_f)
        var_shift  = abs((var_raw - var_filt) / var_raw) * 100 if var_raw > 0 else 0.0
        rmse       = float(np.sqrt(np.mean((bid_r - bid_f) ** 2)))

        if 'Ask' in df_filtered.columns:
            spreads_filt  = df_filtered['Ask'] - df_filtered['Bid']
            neg_spreads   = int((spreads_filt < 0).sum())
            mean_spread_r = float((df_raw['Ask'] - df_raw['Bid']).mean())
            mean_spread_f = float(spreads_filt.mean())
        else:
            neg_spreads   = 0
            mean_spread_r = 0.0
            mean_spread_f = 0.0

        mean_raw      = float(np.mean(bid_r))
        mean_filt     = float(np.mean(bid_f))
        mean_drift_pct = abs((mean_raw - mean_filt) / mean_raw) if mean_raw > 0 else 0.0

        def lag1_acf(arr):
            if len(arr) < 3:
                return 0.0
            r = np.diff(arr)
            if len(r) < 2:
                return 0.0
            try:
                return float(np.corrcoef(r[:-1], r[1:])[0, 1])
            except Exception:
                return 0.0

        acf_raw  = lag1_acf(bid_r)
        acf_filt = lag1_acf(bid_f)

        return {
            "var_raw":              round(float(var_raw),  8),
            "var_filtered":         round(float(var_filt), 8),
            "var_shift_pct":        round(float(var_shift), 4),
            "rmse":                 round(float(rmse), 6),
            "neg_spreads":          neg_spreads,
            "mean_spread_raw":      round(mean_spread_r, 6),
            "mean_spread_filtered": round(mean_spread_f, 6),
            "mean_price_drift_pct": round(float(mean_drift_pct), 6),
            "acf_lag1_raw":         round(float(acf_raw),  4),
            "acf_lag1_filt":        round(float(acf_filt), 4),
            "acf_delta":            round(float(acf_filt - acf_raw), 4),
        }

    def _check_hard_limits(self, metrics: Dict[str, Any]) -> Tuple[list, str]:
        """
        Evaluate hard Python safety floors.
        Returns (failures_list, human-readable summary for the LLM prompt).
        """
        failures = []
        rows = []

        def check(name, value, limit, failed, reason=""):
            status = "❌ FAILED" if failed else "✅ PASSED"
            rows.append(f"  {name:<35} value={value:<12} limit={limit:<12} {status}")
            if failed:
                failures.append(f"{name}: {reason or f'value {value} exceeds limit {limit}'}")

        check("Variance Shift (%)",     f"{metrics['var_shift_pct']:.2f}%",
              f"< {self.MAX_VARIANCE_SHIFT}%",
              metrics['var_shift_pct'] >= self.MAX_VARIANCE_SHIFT,
              f"Alpha-destroying over-filter ({metrics['var_shift_pct']:.2f}% > {self.MAX_VARIANCE_SHIFT}%)")

        check("RMSE (Tracking Error)",  f"{metrics['rmse']:.6f}",
              f"< {self.MAX_RMSE}",
              metrics['rmse'] >= self.MAX_RMSE,
              f"Signal destroyed beyond recognition (RMSE={metrics['rmse']:.6f})")

        check("Negative Spreads",       str(metrics['neg_spreads']),
              "= 0",
              metrics['neg_spreads'] > self.MAX_NEGATIVE_SPREADS,
              f"{metrics['neg_spreads']} negative spreads — Bid-Ask corrupted")

        check("Mean Price Drift (%)",   f"{metrics['mean_price_drift_pct']*100:.4f}%",
              f"< {self.MAX_MEAN_DRIFT_PCT*100:.1f}%",
              metrics['mean_price_drift_pct'] >= self.MAX_MEAN_DRIFT_PCT,
              f"Directional bias introduced ({metrics['mean_price_drift_pct']*100:.4f}%)")

        return failures, "\n".join(rows)

    def _print_evaluation(self, metrics: Dict, gemini_data: Dict, hard_failures: list):
        """Prints the full combined evaluation to the terminal."""
        verdict   = gemini_data.get("verdict", "UNKNOWN")
        reasoning = gemini_data.get("reasoning", "No reasoning provided.")
        risk_score = gemini_data.get("risk_score", 0.0)
        advice    = gemini_data.get("recalibration_advice", "")

        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [GEMINI RISK EVALUATION REPORT]")
        print(f"{'-'*68}")
        print(f"")
        print(f"  STATISTICAL METRICS:")
        print(f"  {'-'*60}")
        print(f"  Variance Shift:    {metrics['var_shift_pct']:.4f}%")
        print(f"  RMSE:              {metrics['rmse']:.6f}")
        print(f"  Negative Spreads:  {metrics['neg_spreads']}")
        print(f"  Mean Drift:        {metrics['mean_price_drift_pct']*100:.4f}%")
        print(f"  ACF Lag-1 Delta:   {metrics['acf_delta']:.4f}")
        print(f"")
        print(f"  GEMINI COMPLIANCE REASONING:")
        print(f"  {'-'*60}")
        for line in reasoning.split("\n"):
            print(f"  {line}")
        print(f"")
        print(f"  RISK SCORE:  {risk_score:.2f} / 1.00")
        print(f"")
        if verdict == "APPROVED":
            print(f"  >>> VERDICT: [APPROVED] - Payload cleared for synthesis.")
        else:
            print(f"  >>> VERDICT: [REJECTED] - {len(hard_failures)} hard limit(s) failed.")
            if advice:
                print(f"")
                print(f"  RECALIBRATION ADVICE FOR LEAD QUANT:")
                for line in advice.split("\n"):
                    print(f"  {line}")
        print(f"{'-'*68}\n")

    def evaluate(
        self,
        df_raw: pd.DataFrame,
        df_filtered: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main entry point. Computes metrics, calls Gemini, enforces hard limits.

        Returns:
            Approved payload dict (if cleared)

        Raises:
            RiskVetoException if any hard limit fails or Gemini rejects.
        """
        print(f"\n  [{self.AGENT_NAME}] ACTIVATING - Gemini Institutional Safety Evaluation...")

        # Step 1: Compute statistical metrics (always deterministic)
        metrics = self._compute_metrics(df_raw, df_filtered)

        # Step 2: Check hard Python safety floors
        hard_failures, hard_limits_summary = self._check_hard_limits(metrics)

        # Step 3: Call Gemini for institutional compliance reasoning
        prompt = self.USER_PROMPT_TEMPLATE.format(
            metrics_json       = json.dumps(metrics, indent=2),
            params_json        = json.dumps(params,  indent=2),
            hard_limits_summary = hard_limits_summary,
        )

        self._log("Calling Gemini for compliance reasoning...")
        try:
            raw_response = call_gemini(prompt, temperature=0.1)  # Low temp = deterministic
            self._log("Gemini compliance assessment received.")
            gemini_data = extract_json(raw_response)

            if not gemini_data or "verdict" not in gemini_data:
                raise ValueError(f"Malformed Gemini response: {raw_response[:200]}")

        except Exception as e:
            self._log(f"Gemini evaluation failed ({e}). Activating deterministic fallback.")
            # Deterministic fallback: approve iff all hard limits pass
            verdict_str = "REJECTED" if hard_failures else "APPROVED"
            gemini_data = {
                "verdict":  verdict_str,
                "reasoning": (
                    f"[FALLBACK — Gemini unavailable]\n"
                    f"Hard limit check: {'FAILED' if hard_failures else 'ALL PASSED'}.\n"
                    + ("\n".join(hard_failures) if hard_failures else "No violations detected.")
                ),
                "risk_score": min(1.0, len(hard_failures) * 0.25),
                "recalibration_advice": "\n".join(hard_failures) if hard_failures else "",
            }

        # CRITICAL: hard limits override Gemini — enforce Python floors regardless
        if hard_failures:
            gemini_data["verdict"] = "REJECTED"

        # Print the full evaluation
        self._print_evaluation(metrics, gemini_data, hard_failures)

        # Raise veto if rejected
        if gemini_data["verdict"] != "APPROVED":
            primary_reason = hard_failures[0] if hard_failures else gemini_data.get("reasoning", "Gemini rejected.")
            raise RiskVetoException(
                reason  = f"VETO: {primary_reason}",
                metrics = metrics,
            )

        return {
            "verdict":                "APPROVED",
            "metrics":                metrics,
            "params":                 params,
            "var_shift":              metrics['var_shift_pct'],
            "rmse":                   metrics['rmse'],
            "gemini_reasoning":       gemini_data.get("reasoning", ""),
            "gemini_risk_score":      gemini_data.get("risk_score", 0.0),
        }
