# =============================================================================
# agents/agent1_data_analyst.py - Agent 1: The Data Analyst (Gemini-Powered)
# The Quant Council
# =============================================================================
# ROLE: Runs the 3 quantitative arsenal tools, then passes the raw numeric
# outputs into Gemini-2.5-Flash for executive-level synthesis.
#
# The LLM produces a rich, narrative intelligence report that every downstream
# agent reads. The tool outputs are ALWAYS computed first (deterministic math),
# then Gemini interprets and narrates them (adaptive language).
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any

from src.core.tools import toxicity_scorer_tool, volatility_matrix_tool, market_regime_detector
from src.core.llm_client import call_gemini, extract_json


class DataAnalystAgent:
    """
    Agent 1: The Data Analyst (Gemini-Powered)
    -------------------------------------------
    Responsibilities:
      1. Validate incoming raw tick DataFrame
      2. Execute toxicity_scorer_tool  -> Q_Score, 5-dim toxicity
      3. Execute volatility_matrix_tool -> RV, EWMA, vol_ratio, kurtosis
      4. Execute market_regime_detector -> regime tag
      5. Synthesise an executive Market Intelligence Report via Gemini
      6. Return all raw tool outputs + the LLM report for downstream agents

    Output dict keys:
      report_text  - Gemini-written narrative intelligence report
      toxicity     - Raw toxicity_scorer_tool output
      volatility   - Raw volatility_matrix_tool output
      regime       - Raw market_regime_detector output
      metadata     - DataFrame statistics
    """

    AGENT_NAME = "DataAnalystAgent"

    SYSTEM_PROMPT = """
You are an institutional HFT Data Analyst embedded at a top-tier hedge fund specialising in Gold (XAUUSD) microstructure. 

XAUUSD MICROSTRUCTURE CONTEXT:
- Baseline Price: ~$2300 - $2500 per ounce.
- Tick Size: $0.01.
- Normal Spread: $0.10 - $0.30 (10 to 30 ticks).
- Volatility: Highly sensitive to US macro data (NFP, CPI) causing extreme liquidity voids and multi-dollar gaps within milliseconds.

You receive raw quantitative metrics computed from a live tick stream. Your job is to synthesise a comprehensive, executive-level Market Intelligence Scan report. Write in a precise, institutional tone. Structure your report with clear sections: Data Overview, Toxicity Assessment, Volatility Profile, Regime Classification, and a brief Analyst's Verdict.
"""

    USER_PROMPT_TEMPLATE = """
You are an institutional HFT Data Analyst. Analyze these raw market metrics for XAUUSD.
Synthesize a comprehensive, executive-level Market Intelligence Scan report.
You MUST highlight: data pollution level, skewness shifts, and fat-tail stress flags based on XAUUSD normal baseline behavior.

=== RAW TOOL OUTPUTS ===
DATASET METADATA: {metadata_json}
TOXICITY PROFILER: {toxicity_json}
VOLATILITY MATRIX: {volatility_json}
REGIME DETECTOR: {regime_json}

=== INSTRUCTIONS ===
Write a structured intelligence report with these EXACT sections:
1. DATA OVERVIEW - tick count, time span, price range.
2. TOXICITY ASSESSMENT - interpret Q_Score and each dimension (RV, Spike, CV, Spread, Gap). Note if spreads exceed normal 30 cents.
3. VOLATILITY PROFILE - analyze vol_ratio, kurtosis (note: kurtosis > 3 indicates heavy tails), stress_flag, and fat-tail risk.
4. REGIME CLASSIFICATION - confirm the detected regime and explain why it makes sense.
5. ANALYST VERDICT - one clear paragraph recommending the urgency and style of filtering required (e.g., standard vs. nuclear outlier removal).

Be specific with numbers. Reference the actual metric values in your analysis.
"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [{self.AGENT_NAME}] {msg}")

    def _validate(self, df: pd.DataFrame) -> None:
        if df is None or df.empty:
            raise ValueError("Input DataFrame is None or empty.")
        required = {"DateTime", "Bid", "Ask"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        if len(df) < 20:
            raise ValueError(f"Too few rows ({len(df)}) - minimum 20 required.")

    def _compute_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        try:
            dt = pd.to_datetime(df['DateTime'])
            time_span_sec = (dt.max() - dt.min()).total_seconds()
        except Exception:
            time_span_sec = 0.0
        mid = (df['Bid'] + df['Ask']) / 2.0
        return {
            "tick_count":     len(df),
            "time_span_sec":  round(time_span_sec, 2),
            "mid_price_mean": round(float(mid.mean()), 5),
            "mid_price_std":  round(float(mid.std()), 5),
            "bid_min":        round(float(df['Bid'].min()), 5),
            "bid_max":        round(float(df['Bid'].max()), 5),
            "has_volume":     "Tick_Volume" in df.columns,
            "generated_utc":  datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def _build_fallback_report(
        self,
        metadata: Dict, toxicity: Dict, volatility: Dict, regime: Dict
    ) -> str:
        """
        Deterministic fallback report used when Gemini is unavailable.
        Section headers are in ALL-CAPS to satisfy test assertions.
        """
        dims = toxicity.get("dimensions", {})
        q    = toxicity.get("Q_Score", 0)
        vr   = volatility.get("vol_ratio", 0)
        kurt = volatility.get("kurtosis", 0)
        sf   = volatility.get("stress_flag", False)
        rname = regime.get("regime", "UNKNOWN")
        conf  = regime.get("confidence", 0)
        rec_f = regime.get("recommended_filter", "N/A")
        lines = [
            "=" * 68,
            "  QUANT COUNCIL - DATA ANALYST INTELLIGENCE REPORT (FALLBACK)",
            "=" * 68,
            f"  Generated:   {metadata['generated_utc']}",
            f"  Tick Count:  {metadata['tick_count']:,}",
            f"  Mid Price:   {metadata['mid_price_mean']:.5f} (sigma={metadata['mid_price_std']:.5f})",
            "",
            # -- Section 1: Q_SCORE (required by tests) --
            "  Q_SCORE ASSESSMENT",
            "  " + "-" * 40,
            f"  Q_SCORE: {q:.6f}  -> {toxicity.get('interpretation', 'N/A')}",
            f"  Dimensions: RV={dims.get('RV',0):.3f}  Spike={dims.get('Spike',0):.3f}  "
            f"CV={dims.get('CV',0):.3f}  Spread={dims.get('Spread',0):.3f}  Gap={dims.get('Gap',0):.3f}",
            "",
            # -- Section 2: VOLATILITY (required by tests) --
            "  VOLATILITY PROFILE",
            "  " + "-" * 40,
            f"  Vol Ratio (RV/EWMA): {vr:.4f}  |  Return Kurtosis: {kurt:.4f}",
            f"  Stress Flag: {'ACTIVE - ELEVATED RISK' if sf else 'INACTIVE - NORMAL'}",
            f"  EWMA Baseline: {volatility.get('ewma_baseline', 0):.8f}",
            "",
            # -- Section 3: REGIME (required by tests) --
            "  REGIME CLASSIFICATION",
            "  " + "-" * 40,
            f"  REGIME: {rname}  (confidence={conf:.4f})",
            f"  Recommended Filter: {rec_f}",
            f"  Recommended K:      {regime.get('recommended_k', 'self-tuning')}",
            "",
            f"  Reasoning: {regime.get('reasoning', 'N/A')}",
            "=" * 68,
        ]
        return "\n".join(lines)

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Main entry point. Runs quantitative tools then calls Gemini to narrate.

        Args:
            df: Raw tick DataFrame {DateTime, Bid, Ask, [Tick_Volume]}

        Returns:
            Dict with report_text, toxicity, volatility, regime, metadata
        """
        print(f"\n{'='*68}")
        print(f"  [{self.AGENT_NAME}] ACTIVATING - Gemini-Powered Market Intelligence Scan")
        print(f"{'='*68}")

        # Step 1: Validate
        self._log("Step 1/5 - Validating DataFrame integrity...")
        self._validate(df)
        self._log(f"  OK - {len(df):,} ticks received. Columns: {list(df.columns)}")

        # Step 2: Run Toxicity Scorer (deterministic math)
        self._log("Step 2/5 - Executing toxicity_scorer_tool...")
        toxicity = toxicity_scorer_tool(df)
        self._log(f"  Q_Score = {toxicity['Q_Score']:.6f} | {toxicity['interpretation']}")

        # Step 3: Run Volatility Matrix (deterministic math)
        self._log("Step 3/5 - Executing volatility_matrix_tool...")
        volatility = volatility_matrix_tool(df)
        self._log(f"  vol_ratio = {volatility['vol_ratio']:.4f} | stress_flag = {volatility['stress_flag']}")

        # Step 4: Detect Regime (deterministic math)
        self._log("Step 4/5 - Executing market_regime_detector...")
        regime = market_regime_detector(toxicity, volatility)
        self._log(f"  REGIME LOCKED: [{regime['regime']}] (confidence={regime['confidence']:.4f})")

        # Step 5: Compile metadata
        metadata = self._compute_metadata(df)

        # Step 6: Call Gemini for LLM-synthesised executive report
        self._log("Step 5/5 - Calling Gemini for executive report synthesis...")
        prompt = self.USER_PROMPT_TEMPLATE.format(
            metadata_json  = json.dumps(metadata,   indent=2),
            toxicity_json  = json.dumps(toxicity,   indent=2),
            volatility_json= json.dumps(volatility, indent=2),
            regime_json    = json.dumps(regime,     indent=2),
        )

        try:
            report_text = call_gemini(prompt, temperature=0.2)
            self._log("  [SUCCESS] Gemini synthesis complete.")
        except Exception as e:
            self._log(f"  [WARNING] Gemini unavailable ({e}). Using deterministic fallback report.")
            report_text = self._build_fallback_report(metadata, toxicity, volatility, regime)

        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [GEMINI MARKET INTELLIGENCE REPORT]")
        print(f"{'-'*68}")
        print(f"\n{report_text}\n")
        print(f"\n  [{self.AGENT_NAME}] COMPLETE - Report ready for LeadQuantAgent.\n")

        return {
            "report_text": report_text,
            "toxicity":    toxicity,
            "volatility":  volatility,
            "regime":      regime,
            "metadata":    metadata,
        }
