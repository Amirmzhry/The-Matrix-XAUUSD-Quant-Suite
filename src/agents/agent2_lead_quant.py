# =============================================================================
# agents/agent2_lead_quant.py — Agent 2: The Lead Quant (Gemini-Powered)
# The Quant Council
# =============================================================================
# ROLE: The strategic mastermind. Reads the Data Analyst's Gemini report,
# sends it to Gemini with a strict JSON-output prompt to:
#   • Print a comprehensive Inner Monologue (reasoning chain)
#   • Select the optimal filter from the available toolkit
#   • Calculate data-driven hyperparameters from scratch
#   • Adapt aggressively if previous attempts were rejected
#
# ALL hardcoded REGIME_PRIORITY tables and procedural _derive_parameters()
# logic have been REMOVED. The LLM reasons from first principles each time.
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

from src.core.tick_factory_engine import verify_tick_by_tick
from src.core.llm_client import call_gemini, extract_json


# ---------------------------------------------------------------------------
# VALID FILTER TOOLKIT — Gemini must choose exactly one of these
# ---------------------------------------------------------------------------
VALID_FILTERS = {
    "ADAPTIVE_KALMAN": {
        "description": "Self-tuning Kalman filter. Best for low-moderate noise regimes. O(1) per tick.",
        "required_params": ["kalman_R", "q_scaling"],
        "example": {"filter": "ADAPTIVE_KALMAN", "kalman_R": 0.05, "q_scaling": 0.1},
    },
    "MAD": {
        "description": "Trailing Median Absolute Deviation clipper. Robust to fat tails.",
        "required_params": ["window", "mad_threshold", "tolerance"],
        "example": {"filter": "MAD", "window": 50, "mad_threshold": 3.0, "tolerance": 0.05},
    },
    "EMA_ZSCORE": {
        "description": "Exponentially weighted Z-Score outlier removal. Fast adaptation.",
        "required_params": ["ema_span", "threshold"],
        "example": {"filter": "EMA_ZSCORE", "ema_span": 50, "threshold": 3.0},
    },
    "HAMPEL": {
        "description": "Hampel identifier — replaces outliers with trailing median. Gold standard.",
        "required_params": ["half_window", "k_sigma"],
        "example": {"filter": "HAMPEL", "half_window": 15, "k_sigma": 3.0},
    },
    "DEEP_DENOISE_HAMPEL_KALMAN": {
        "description": "Sequential Hampel→Kalman chain. Nuclear option for FLASH_CRASH regimes.",
        "required_params": ["hampel_k", "kalman_R"],
        "example": {"filter": "DEEP_DENOISE_HAMPEL_KALMAN", "hampel_k": 2.5, "kalman_R": 0.1},
    },
}

# ---------------------------------------------------------------------------
# Fallback parameter table (used ONLY if Gemini is unavailable)
# ---------------------------------------------------------------------------
_FALLBACK_PARAMS: Dict[str, Dict] = {
    "ADAPTIVE_KALMAN":           {"filter": "ADAPTIVE_KALMAN",           "kalman_R": 0.05, "q_scaling": 0.1},
    "MAD":                       {"filter": "MAD",                       "window": 50, "mad_threshold": 3.0, "tolerance": 0.05},
    "EMA_ZSCORE":                {"filter": "EMA_ZSCORE",                "ema_span": 50, "threshold": 3.0},
    "HAMPEL":                    {"filter": "HAMPEL",                    "half_window": 15, "k_sigma": 3.0},
    "DEEP_DENOISE_HAMPEL_KALMAN":{"filter": "DEEP_DENOISE_HAMPEL_KALMAN","hampel_k": 2.5, "kalman_R": 0.1},
}

_FALLBACK_PRIORITY = {
    "FLASH_CRASH":   ["DEEP_DENOISE_HAMPEL_KALMAN", "HAMPEL", "MAD"],
    "EXTREME_SPIKE": ["HAMPEL", "MAD", "EMA_ZSCORE", "ADAPTIVE_KALMAN"],
    "HEAVY_NOISE":   ["MAD", "HAMPEL", "EMA_ZSCORE", "ADAPTIVE_KALMAN"],
    "ELEVATED":      ["EMA_ZSCORE", "MAD", "HAMPEL", "ADAPTIVE_KALMAN"],
    "NORMAL":        ["ADAPTIVE_KALMAN", "EMA_ZSCORE", "MAD", "HAMPEL"],
}


class LeadQuantAgent:
    """
    Agent 2: The Lead Quant (Gemini-Powered)
    -----------------------------------------
    Gemini receives the full Data Analyst report and must return a strict JSON:
      {
        "filter_name":     <one of VALID_FILTERS>,
        "inner_monologue": <string — full reasoning chain>,
        "parameters":      {<filter-specific hyperparameters>}
      }

    The inner_monologue is printed verbatim to the terminal.
    The parameters dict is passed directly to the TickEngine.
    """

    AGENT_NAME = "LeadQuantAgent"

    USER_PROMPT_TEMPLATE = """
You are the Mastermind Lead Quant at a multi-billion dollar hedge fund specialising in Gold (XAUUSD) HFT.

You have received this Market Intelligence Report:
===BEGIN REPORT===
{analyst_report}
===END REPORT===

REJECTION LEDGER (filters already vetoed by the Risk Officer — DO NOT re-propose these):
{rejection_ledger}

ITERATION: {iteration} of {max_iterations}
ESCALATION NOTE: {escalation_note}

AVAILABLE FILTER TOOLKIT (you must choose EXACTLY one):
{filter_toolkit_json}

YOUR TASK:
1. INNER MONOLOGUE: Reason through the market state in depth. Reference specific metrics (Q_Score, kurtosis, spike density). Explain WHY you are choosing this filter. If previous filters were rejected, explain your pivot strategy.
2. MATHEMATICAL CALIBRATION: Calculate exact hyperparameters from the metrics. 
   - XAUUSD Context: A $1.00 spike is noise, a $10.00 spike is a structural shift. 
   - Window sizing: Remember 50 ticks might just be 100 milliseconds during US session open.
   - Do NOT use example values blindly. Derive them mathematically based on the Q_Score and Escalation factor.

CRITICAL OUTPUT FORMAT:
You MUST respond with ONLY a valid JSON object — no markdown, no text outside the JSON.
{{
  "filter_name": "<EXACT filter name from the toolkit>",
  "inner_monologue": "<your full reasoning chain as a multi-paragraph string>",
  "parameters": {{ <filter-specific key-value pairs matching the toolkit's required_params> }}
}}

The "parameters" dict MUST include the key "filter" set to the same value as "filter_name".
"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def _log(self, msg: str, indent: int = 2):
        if self.verbose:
            prefix = " " * indent
            print(f"{prefix}[{self.AGENT_NAME}] {msg}")

    def _build_filter_toolkit_json(self) -> str:
        return json.dumps(VALID_FILTERS, indent=2)

    def _escalation_note(self, iteration: int, rejected: List[str]) -> str:
        if iteration == 1:
            return "This is the first attempt. Use your best judgment."
        factor = 1.0 + (iteration - 1) * 0.3
        return (
            f"This is attempt {iteration}. You must be MORE aggressive than the previous attempt. "
            f"Escalation factor: {factor:.2f}x — tighten thresholds and reduce window sizes "
            f"by approximately {int((factor-1)*100)}% vs your first-attempt values."
        )

    def _fallback_decide(
        self, analyst_output: Dict, rejected_filters: List[str], iteration: int
    ) -> Dict[str, Any]:
        """Pure-Python fallback if Gemini is unavailable."""
        regime = analyst_output.get("regime", {}).get("regime", "NORMAL")
        priority = _FALLBACK_PRIORITY.get(regime, _FALLBACK_PRIORITY["NORMAL"])
        chosen = None
        for f in priority:
            if f not in rejected_filters:
                chosen = f
                break
        if chosen is None:
            chosen = "DEEP_DENOISE_HAMPEL_KALMAN"

        params = dict(_FALLBACK_PARAMS[chosen])
        factor = 1.0 + (iteration - 1) * 0.3
        if "mad_threshold" in params:
            params["mad_threshold"] = round(params["mad_threshold"] / factor, 2)
        if "k_sigma" in params:
            params["k_sigma"] = round(params["k_sigma"] / factor, 2)
        if "threshold" in params:
            params["threshold"] = round(params["threshold"] / factor, 2)

        monologue = (
            f"[FALLBACK MODE — Gemini unavailable]\n"
            f"Regime detected: {regime}. Selecting {chosen} from priority list.\n"
            f"Iteration {iteration}: escalation factor {factor:.2f}x applied to thresholds."
        )
        return {"filter_name": chosen, "inner_monologue": monologue, "parameters": params}

    def run(
        self,
        df: pd.DataFrame,
        analyst_output: Dict[str, Any],
        rejected_filters: Optional[List[str]] = None,
        iteration: int = 1,
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Main entry point. Calls Gemini to reason about the filter strategy.

        Args:
            df:               Raw tick DataFrame
            analyst_output:   Full output from DataAnalystAgent.run()
            rejected_filters: Filter names already vetoed by Risk Officer
            iteration:        Current ReAct loop iteration (1-indexed)
            max_iterations:   Total allowed iterations

        Returns:
            Dict with filtered_df, params, filter_name, inner_monologue
        """
        if rejected_filters is None:
            rejected_filters = []

        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [ACTIVATING - Gemini Strategy Engine (Iter {iteration})]")
        print(f"{'-'*68}")

        report_text   = analyst_output.get("report_text", "No report available.")
        rejection_str = json.dumps(rejected_filters) if rejected_filters else "[] (none rejected yet)"

        prompt = self.USER_PROMPT_TEMPLATE.format(
            analyst_report    = report_text,
            rejection_ledger  = rejection_str,
            iteration         = iteration,
            max_iterations    = max_iterations,
            escalation_note   = self._escalation_note(iteration, rejected_filters),
            filter_toolkit_json = self._build_filter_toolkit_json(),
        )

        # --- Call Gemini ---
        try:
            self._log("Calling Gemini for filter strategy reasoning...")
            raw_response = call_gemini(prompt, temperature=0.4)
            self._log("  [SUCCESS] Gemini responded.")

            gemini_data = extract_json(raw_response)

            # Validate the response structure
            if not gemini_data or "filter_name" not in gemini_data or "parameters" not in gemini_data:
                raise ValueError(f"Gemini returned malformed JSON: {raw_response[:300]}")

            chosen_filter  = gemini_data["filter_name"]
            inner_monologue = gemini_data.get("inner_monologue", "No monologue provided.")
            params         = gemini_data["parameters"]

            # Ensure filter key is set inside params
            params["filter"] = chosen_filter

            # Validate filter name is in our toolkit
            if chosen_filter not in VALID_FILTERS:
                raise ValueError(
                    f"Gemini chose unknown filter '{chosen_filter}'. "
                    f"Valid options: {list(VALID_FILTERS.keys())}"
                )

            # Refuse rejected filters
            if chosen_filter in rejected_filters:
                raise ValueError(
                    f"Gemini re-proposed a rejected filter '{chosen_filter}'. "
                    "Falling back to deterministic override."
                )

        except Exception as e:
            self._log(f"  [WARNING] Gemini strategy failed ({e}). Activating deterministic fallback.")
            fallback = self._fallback_decide(analyst_output, rejected_filters, iteration)
            chosen_filter   = fallback["filter_name"]
            inner_monologue = fallback["inner_monologue"]
            params          = fallback["parameters"]

        # --- Print Inner Monologue ---
        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [INNER MONOLOGUE (Gemini Reasoning Chain)]")
        print(f"{'-'*68}")
        print(f"")
        print(f"  SITUATION ASSESSMENT:")
        print(f"  {'-'*21}")
        for line in inner_monologue.split("\n")[:8]:    # first 8 lines of Gemini monologue
            print(f"  {line}")
        print(f"")
        print(f"  FILTER SELECTION:")
        print(f"  {'-'*17}")
        print(f"  SELECTED: [{chosen_filter}]")
        print(f"")
        print(f"  RATIONALE:")
        for line in inner_monologue.split("\n")[8:]:    # remainder of Gemini monologue
            print(f"  {line}")
        print(f"")
        print(f"  FINAL PARAMETERS ISSUED TO TICK ENGINE:")
        for k, v in params.items():
            print(f"      {k:28s} = {v}")
        print(f"{'-'*68}\n")

        # --- Apply filter via strictly causal TickEngine ---
        self._log("Dispatching to strictly causal TickEngine...")
        try:
            cleaned_array = verify_tick_by_tick(df, chosen_filter, params)
            filtered_df = df.copy()
            filtered_df['Bid'] = cleaned_array
            if 'Ask' in df.columns:
                # Preserve raw spread — mathematically prevents negative spreads
                filtered_df['Ask'] = filtered_df['Bid'] + (df['Ask'] - df['Bid'])
            self._log(f"Filter applied. Rows processed: {len(filtered_df):,}")
        except Exception as e:
            raise RuntimeError(
                f"[{self.AGENT_NAME}] TickEngine crashed on filter '{chosen_filter}': {e}"
            )

        return {
            "filtered_df":    filtered_df,
            "params":         params,
            "filter_name":    chosen_filter,
            "inner_monologue": inner_monologue,
        }
