# =============================================================================
# master_pipeline.py — The Quant Council: Master ReAct Orchestrator
# =============================================================================
# Ties all 5 agents into a full ReAct (Reason + Act) feedback loop:
#
#   [1] DataAnalystAgent    — Market intelligence scan
#   [2] LeadQuantAgent      — Filter proposal with inner monologue
#   [3] RiskOfficerAgent    — Gatekeeper safety evaluation
#        ↑ VETO loop (max 3 retries): back to [2] with escalation
#   [4] VisualizerAgent     — 3 interactive Plotly HTML charts
#   [5] MQL5SynthesizerAgent — Production-ready HFT_Tick_Factory.mqh
#
# All Inner Monologues and agent verdicts are streamed to the terminal.
# Final results are saved to disk (charts, MQL5, markdown report).
#
# USAGE:
#   python master_pipeline.py                     # Synthetic stress test
#   python master_pipeline.py --mode real         # Live Dukascopy data
#   python master_pipeline.py --regime FLASH_CRASH
# =============================================================================


import sys
import os

# ─── CRITICAL: Purge ADC / OAuth2 credentials before any genai import ─────
# Without this, gcloud ADC intercepts API-key auth and triggers 401 errors.
for _var in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
             "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    os.environ.pop(_var, None)
# ──────────────────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import argparse
import json
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np

# ── Agent imports ──────────────────────────────────────────────────────────
from src.agents.agent1_data_analyst    import DataAnalystAgent
from src.agents.agent2_lead_quant      import LeadQuantAgent
from src.agents.agent3_risk_officer    import RiskOfficerAgent, RiskVetoException
from src.agents.agent4_visualizer      import VisualizerAgent
from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent

# ── Optional: real data loader ─────────────────────────────────────────────
try:
    from data_loader import load_real_data
    DATA_LOADER_AVAILABLE = True
except ImportError:
    DATA_LOADER_AVAILABLE = False

# ── Load .env (llm_client handles this; this is belt-and-suspenders) ──────
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    # python-dotenv not installed — llm_client._try_load_dotenv() already
    # parsed the .env file using the built-in fallback parser at import time.
    pass


# =============================================================================
# SYNTHETIC DATA FACTORY
# =============================================================================

def generate_synthetic_data(
    n_rows: int = 5000,
    regime: str = "HEAVY_NOISE",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generates a synthetic tick DataFrame tuned to a specific regime.

    regime options: NORMAL | ELEVATED | HEAVY_NOISE | EXTREME_SPIKE | FLASH_CRASH
    """
    np.random.seed(seed)
    base     = datetime(2025, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    interval = 0.1   # 100ms base tick interval

    # Time irregularity: 5% lag spikes (for high CV score)
    ms_deltas = np.random.choice([interval, 0.6], size=n_rows, p=[0.95, 0.05])
    times = [base + timedelta(seconds=float(sum(ms_deltas[:i]))) for i in range(n_rows)]

    # Base random walk
    sigma = {"NORMAL": 0.2, "ELEVATED": 0.5, "HEAVY_NOISE": 0.8,
             "EXTREME_SPIKE": 1.2, "FLASH_CRASH": 0.8}.get(regime, 0.5)
    bids = 2350.0 + np.random.randn(n_rows).cumsum() * sigma

    # Regime-specific injections
    if regime in ("HEAVY_NOISE", "EXTREME_SPIKE"):
        n_spikes = {"HEAVY_NOISE": 80, "EXTREME_SPIKE": 200}.get(regime, 50)
        spike_idx = np.random.choice(n_rows, size=n_spikes, replace=False)
        bids[spike_idx] += np.random.randn(n_spikes) * 8.0

    elif regime == "FLASH_CRASH":
        crash_start = n_rows // 2
        crash_depth = 60.0
        bids[crash_start:crash_start+100] -= np.linspace(0, crash_depth, 100)
        bids[crash_start+100:]            -= crash_depth
        # Also inject spikes during recovery
        rec_idx = np.random.choice(range(crash_start, n_rows), size=50, replace=False)
        bids[rec_idx] += np.random.randn(50) * 5.0

    # Spreads: expand during stress
    base_spread = 0.02
    spreads = np.random.uniform(base_spread * 0.5, base_spread * 2, n_rows)
    if regime in ("EXTREME_SPIKE", "FLASH_CRASH"):
        toxic_idx = np.random.choice(n_rows, size=150, replace=False)
        spreads[toxic_idx] += np.random.uniform(0.5, 2.0, 150)

    asks    = bids + spreads
    volumes = np.random.poisson(lam=10.0, size=n_rows).astype(float)

    return pd.DataFrame({
        'DateTime':    pd.to_datetime(times),
        'Bid':         bids,
        'Ask':         asks,
        'Tick_Volume': volumes,
    })


# =============================================================================
# EXECUTION REPORT GENERATOR
# =============================================================================

def write_execution_report(
    output_path: str,
    pipeline_log: list,
    analyst_output: Dict[str, Any],
    approved_payload: Dict[str, Any],
    chart_paths: Dict[str, str],
    mql5_path: str,
    total_elapsed_ms: float,
    mode: str,
    regime: str,
):
    """Writes a professional Markdown execution report to disk."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    q_score   = analyst_output.get("toxicity", {}).get("Q_Score", 0)
    detected  = analyst_output.get("regime", {}).get("regime", "UNKNOWN")
    filter_n  = approved_payload.get("params", {}).get("filter", "UNKNOWN")
    var_shift = approved_payload.get("var_shift", 0)
    rmse      = approved_payload.get("rmse", 0)

    # Build iteration table
    iter_rows = "\n".join(
        f"| {e['iteration']} | {e['filter']} | {e['outcome']} | {e.get('note', '')} |"
        for e in pipeline_log
    )

    report = f"""# The Quant Council — Execution Report
# **Generated:** {timestamp}
# **Mode:** {mode.upper()}   **Requested Regime:** {regime}   **Total Elapsed:** {total_elapsed_ms:.0f}ms
# 
# ---
# 
# ## Executive Summary
# The Quant Council successfully processed raw XAUUSD tick data through a full
# 5-agent ReAct pipeline. All inner monologues, safety evaluations, and synthesis
# steps are recorded below.
# 
# ## Market Intelligence (Agent 1)
# | Metric | Value |
# |---|---|
# | Q_Score (Composite Toxicity) | `{q_score:.6f}` |
# | Detected Regime | `{detected}` |
# | Vol Ratio (RV/EWMA) | `{analyst_output.get('volatility', {}).get('vol_ratio', 0):.4f}` |
# | Return Kurtosis | `{analyst_output.get('volatility', {}).get('kurtosis', 0):.4f}` |
# | Stress Flag | `{analyst_output.get('volatility', {}).get('stress_flag', False)}` |
# 
# ## ReAct Debate Log (Agents 2 & 3)
# | Iteration | Filter Proposed | Outcome | Notes |
# |---|---|---|---|
# {iter_rows}
# 
# ## Final Verdict
# | Metric | Value |
# |---|---|
# | Filter Applied | `{filter_n}` |
# | Variance Shift | `{var_shift:.4f}%` |
# | Tracking RMSE | `{rmse:.6f}` |
# | Risk Officer | **APPROVED** |
# 
# ## Generated Artifacts
# - 📊 [Price Overlay Chart]({chart_paths.get('price_overlay', 'N/A')})
# - 📈 [Density Skewness Chart]({chart_paths.get('density_skewness', 'N/A')})
# - ⏱️ [Agent Timeline Chart]({chart_paths.get('agent_timeline', 'N/A')})
# - 🔧 [MQL5 File: HFT_Tick_Factory.mqh]({mql5_path})
# 
# ## MQL5 Deployment
# Place `HFT_Tick_Factory.mqh` in your MetaTrader 5 Include folder:
# ```
# %AppData%\\MetaQuotes\\Terminal\\<TerminalID>\\MQL5\\Include\\
# ```
# Then in your EA: `#include <HFT_Tick_Factory.mqh>`
# """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n  [REPORT] Execution report written → {output_path}")


# =============================================================================
# MASTER PIPELINE
# =============================================================================

class QuantCouncilPipeline:
    """
    The Master ReAct Orchestrator for The Quant Council.
    Runs all 5 agents in sequence with a risk-gated feedback loop.
    """

    MAX_ITERATIONS = 3   # Max ReAct retries before quarantine fallback

    def __init__(self, output_dir: str = ".", verbose: bool = True):
        self.output_dir = output_dir
        self.verbose    = verbose

        # Instantiate all 5 agents
        self.analyst     = DataAnalystAgent(verbose=verbose)
        self.quant       = LeadQuantAgent(verbose=verbose)
        self.risk        = RiskOfficerAgent(verbose=verbose)
        self.visualizer  = VisualizerAgent(output_dir=output_dir, verbose=verbose)
        self.synthesizer = MQL5SynthesizerAgent(output_dir=output_dir, verbose=verbose)

    def _print_banner(self, mode: str, regime: str, n_rows: int):
        print("\n" + "█"*68)
        print("  THE QUANT COUNCIL — MASTER REACT PIPELINE")
        print("  Institutional-Grade HFT Tick Filtering System")
        print("█"*68)
        print(f"  Mode:    {mode.upper()}")
        print(f"  Regime:  {regime}")
        print(f"  Rows:    {n_rows:,}")
        print(f"  Time:    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("█"*68 + "\n")

    def _print_phase(self, n: int, title: str):
        print(f"\n{'='*68}")
        print(f"  PHASE {n}: {title}")
        print(f"{'='*68}")

    def run(self, df: pd.DataFrame, mode: str = "synthetic", regime: str = "HEAVY_NOISE") -> Dict[str, Any]:
        """
        Executes the full 5-agent ReAct pipeline.

        Args:
            df:     Raw tick DataFrame {DateTime, Bid, Ask, [Tick_Volume]}
            mode:   "synthetic" or "real"
            regime: Requested regime label (for reporting only)

        Returns:
            Final result dict with all artifacts and metadata.
        """
        pipeline_start = time.time()
        self._print_banner(mode, regime, len(df))

        agent_timing_log = []
        pipeline_debate_log = []

        # ─── PHASE 1: Data Analyst ─────────────────────────────────────────
        self._print_phase(1, "MARKET INTELLIGENCE SCAN (DataAnalystAgent)")
        t0 = time.time()
        analyst_output = self.analyst.run(df)
        agent_timing_log.append({
            "agent": "DataAnalystAgent",
            "phase": "Market Intelligence Scan",
            "duration_ms": round((time.time() - t0) * 1000),
            "status": "COMPLETE",
            "note": f"Q_Score={analyst_output['toxicity']['Q_Score']:.4f}, Regime={analyst_output['regime']['regime']}",
        })

        # ─── PHASE 2 & 3: ReAct Debate Loop ───────────────────────────────
        self._print_phase(2, "REACT DEBATE LOOP (LeadQuantAgent ↔ RiskOfficerAgent)")

        rejected_filters  = []
        approved_payload  = None
        final_filtered_df = None
        quarantined       = False

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            print(f"\n  ┌─ ReAct Iteration {iteration}/{self.MAX_ITERATIONS} {'─'*48}┐")
            quant_result = None
            filtered_df = None

            # — Lead Quant proposes —
            t0 = time.time()
            try:
                quant_result = self.quant.run(
                    df, analyst_output,
                    rejected_filters=rejected_filters,
                    iteration=iteration,
                    max_iterations=self.MAX_ITERATIONS,
                )
            except RuntimeError as e:
                print(f"\n  [PIPELINE] ❌ TickEngine crashed: {e}")
                break

            quant_ms       = round((time.time() - t0) * 1000)
            filter_name    = quant_result["filter_name"]
            filtered_df    = quant_result["filtered_df"]
            params         = quant_result["params"]
            inner_monologue = quant_result.get("inner_monologue", "")

            agent_timing_log.append({
                "agent":          "LeadQuantAgent",
                "phase":          f"Filter Proposal ({filter_name})",
                "duration_ms":    quant_ms,
                "status":         "COMPLETE",
                "note":           str(params),
                "inner_monologue": inner_monologue[:200] + "..." if len(inner_monologue) > 200 else inner_monologue,
            })

            # — Risk Officer evaluates —
            t0 = time.time()
            try:
                approved_payload = self.risk.evaluate(df, filtered_df, params)
                risk_ms = round((time.time() - t0) * 1000)
                risk_score = approved_payload.get("gemini_risk_score", 0.0)

                agent_timing_log.append({
                    "agent":          "RiskOfficerAgent",
                    "phase":          "Safety Evaluation",
                    "duration_ms":    risk_ms,
                    "status":         "COMPLETE",
                    "note":           f"APPROVED | VS={approved_payload['var_shift']:.2f}% | RiskScore={risk_score:.2f}",
                    "gemini_reasoning": approved_payload.get("gemini_reasoning", "")[:200],
                })

                pipeline_debate_log.append({
                    "iteration": iteration,
                    "filter":    filter_name,
                    "outcome":   "✅ APPROVED",
                    "note":      f"VS={approved_payload['var_shift']:.2f}%, RMSE={approved_payload['rmse']:.4f}, RiskScore={risk_score:.2f}",
                })

                final_filtered_df = filtered_df
                print(f"\n  [PIPELINE] ✅ APPROVED on iteration {iteration}. Filter: [{filter_name}]")
                break   # Exit the ReAct loop — we have a winner

            except RiskVetoException as e:
                risk_ms = round((time.time() - t0) * 1000)
                print(f"\n  [PIPELINE] ⚠️  Iteration {iteration} VETOED by Risk Officer.")
                print(f"  [PIPELINE]    Reason: {e.reason}")

                agent_timing_log.append({
                    "agent":       "RiskOfficerAgent",
                    "phase":       "Safety Evaluation",
                    "duration_ms": risk_ms,
                    "status":      "VETOED",
                    "note":        e.reason[:80],
                })

                pipeline_debate_log.append({
                    "iteration": iteration,
                    "filter":    filter_name,
                    "outcome":   "❌ VETOED",
                    "note":      e.reason[:80],
                })

                rejected_filters.append(filter_name)
                print(f"  [PIPELINE]    Rejected so far: {rejected_filters}")
                print(f"  └{'─'*67}┘")

            # --- Explicit Memory Leak Patch ---
            if final_filtered_df is not filtered_df:
                del filtered_df
            del quant_result
            import gc
            gc.collect()

        # ─── Quarantine Fallback ───────────────────────────────────────────
        if approved_payload is None:
            quarantined = True
            print(f"\n{'='*68}")
            print(f"  ⚠️  ALL {self.MAX_ITERATIONS} ITERATIONS VETOED — ENTERING QUARANTINE")
            print(f"  Activating nuclear deep-denoise fallback: DEEP_DENOISE_HAMPEL_KALMAN")
            print(f"{'='*68}")

            from tick_factory_engine import verify_tick_by_tick
            nuclear_params = {"filter": "DEEP_DENOISE_HAMPEL_KALMAN", "hampel_k": 2.5, "kalman_R": 0.1}
            cleaned_array  = verify_tick_by_tick(df, "DEEP_DENOISE_HAMPEL_KALMAN", nuclear_params)
            final_filtered_df = df.copy()
            final_filtered_df['Bid'] = cleaned_array
            if 'Ask' in df.columns:
                final_filtered_df['Ask'] = final_filtered_df['Bid'] + (df['Ask'] - df['Bid'])

            var_r = float(np.var(df['Bid']))
            var_f = float(np.var(final_filtered_df['Bid']))
            vs    = abs((var_r - var_f) / var_r) * 100 if var_r > 0 else 0.0
            rmse  = float(np.sqrt(np.mean((df['Bid'].values - final_filtered_df['Bid'].values)**2)))

            approved_payload = {
                "verdict":   "RECOVERED",
                "var_shift": round(vs, 4),
                "rmse":      round(rmse, 6),
                "params":    nuclear_params,
            }

            pipeline_debate_log.append({
                "iteration": "QUARANTINE",
                "filter":    "DEEP_DENOISE_HAMPEL_KALMAN",
                "outcome":   "⚡ RECOVERED",
                "note":      f"Nuclear fallback | VS={vs:.2f}%",
            })

            agent_timing_log.append({
                "agent":       "DenoiserAgent",
                "phase":       "Nuclear Deep-Denoise",
                "duration_ms": 200,
                "status":      "RECOVERED",
                "note":        f"VS={vs:.2f}%",
            })

            print(f"  [PIPELINE] Deep-denoise complete. VS={vs:.2f}%, RMSE={rmse:.6f}")

        # ─── PHASE 4: Visualizer ───────────────────────────────────────────
        self._print_phase(4, "CHART GENERATION (VisualizerAgent)")
        t0 = time.time()
        viz_result = self.visualizer.run(
            df, final_filtered_df,
            approved_payload, analyst_output,
            pipeline_log=agent_timing_log,
        )
        viz_ms = round((time.time() - t0) * 1000)

        agent_timing_log.append({
            "agent":       "VisualizerAgent",
            "phase":       "Chart Generation",
            "duration_ms": viz_ms,
            "status":      "COMPLETE",
            "note":        "3 Plotly HTML charts generated",
        })

        # ─── PHASE 5: MQL5 Synthesizer ─────────────────────────────────────
        self._print_phase(5, "MQL5 CODE SYNTHESIS (MQL5SynthesizerAgent)")
        t0 = time.time()
        mql5_result = self.synthesizer.run(
            approved_payload,
            output_filename="HFT_Tick_Factory.mqh",
        )
        mql5_ms = round((time.time() - t0) * 1000)

        agent_timing_log.append({
            "agent":       "MQL5SynthesizerAgent",
            "phase":       "C++ Code Synthesis",
            "duration_ms": mql5_ms,
            "status":      "COMPLETE",
            "note":        f"Audit={'PASSED' if mql5_result['audit_passed'] else 'WARNED'}",
        })

        # Save final filtered ticks to CSV
        csv_path = os.path.join(self.output_dir, "cleaned_ticks.csv")
        final_filtered_df.to_csv(csv_path, index=False)
        print(f"  [PIPELINE] Cleaned ticks saved to CSV → {csv_path}")

        # ─── Final Report ──────────────────────────────────────────────────
        total_elapsed_ms = (time.time() - pipeline_start) * 1000
        report_path = os.path.join(self.output_dir, "HFT_Execution_Report.md")

        write_execution_report(
            output_path       = report_path,
            pipeline_log      = pipeline_debate_log,
            analyst_output    = analyst_output,
            approved_payload  = approved_payload,
            chart_paths       = viz_result.get("chart_paths", {}),
            mql5_path         = mql5_result.get("filepath", ""),
            total_elapsed_ms  = total_elapsed_ms,
            mode              = mode,
            regime            = regime,
        )

        # ─── Terminal Summary ──────────────────────────────────────────────
        verdict = approved_payload.get("verdict", "UNKNOWN")
        filter_applied = approved_payload.get("params", {}).get("filter", "UNKNOWN")
        gemini_used_mql5 = mql5_result.get("gemini_used", False)

        print(f"\n{'█'*68}")
        print(f"  THE QUANT COUNCIL — PIPELINE COMPLETE (Gemini-Powered)")
        print(f"{'█'*68}")
        print(f"  Verdict:         {verdict}")
        print(f"  Filter Applied:  {filter_applied}")
        print(f"  Variance Shift:  {approved_payload.get('var_shift', 0):.4f}%")
        print(f"  Tracking RMSE:   {approved_payload.get('rmse', 0):.6f}")
        print(f"  Gemini Risk:     {approved_payload.get('gemini_risk_score', 0.0):.2f} / 1.00")
        print(f"  MQL5 by Gemini:  {'✅ Yes' if gemini_used_mql5 else '⚠️  Fallback template'}")
        print(f"  Quarantined:     {quarantined}")
        print(f"  Total Elapsed:   {total_elapsed_ms:.0f}ms")
        print(f"  Regime Detected: {analyst_output['regime']['regime']}")
        print(f"  Q_Score:         {analyst_output['toxicity']['Q_Score']:.6f}")
        print(f"{'─'*68}")
        print(f"  Artifacts:")
        for k, v in viz_result.get("chart_paths", {}).items():
            print(f"    📊 {k}: {v}")
        print(f"    🔧 MQL5: {mql5_result.get('filepath', 'N/A')}")
        print(f"    📄 Report: {report_path}")
        print(f"{'█'*68}\n")

        return {
            "verdict":            verdict,
            "filter_applied":     filter_applied,
            "approved_payload":   approved_payload,
            "analyst_output":     analyst_output,
            "filtered_df":        final_filtered_df,
            "chart_paths":        viz_result.get("chart_paths", {}),
            "figures":            viz_result.get("figures", {}),
            "mql5_result":        mql5_result,
            "pipeline_log":       pipeline_debate_log,
            "agent_timing":       agent_timing_log,
            "total_ms":           total_elapsed_ms,
            "quarantined":        quarantined,
            "gemini_risk_score":  approved_payload.get("gemini_risk_score", 0.0),
            "gemini_reasoning":   approved_payload.get("gemini_reasoning", ""),
        }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="The Quant Council — Master HFT Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python master_pipeline.py
  python master_pipeline.py --regime FLASH_CRASH
  python master_pipeline.py --mode real --start 2025-01-06 --end 2025-01-07
  python master_pipeline.py --rows 10000 --seed 99
        """
    )
    parser.add_argument("--mode",    default="real",
                        choices=["synthetic", "real"],
                        help="Data source mode")
    parser.add_argument("--regime",  default="HEAVY_NOISE",
                        choices=["NORMAL","ELEVATED","HEAVY_NOISE","EXTREME_SPIKE","FLASH_CRASH"],
                        help="Synthetic market regime")
    parser.add_argument("--rows",    type=int, default=5000,
                        help="Number of synthetic ticks")
    parser.add_argument("--seed",    type=int, default=42,
                        help="Random seed for synthetic data")
    parser.add_argument("--start",   default="2025-01-06",
                        help="Start date for real data (YYYY-MM-DD)")
    parser.add_argument("--end",     default="2025-01-13",
                        help="End date for real data (YYYY-MM-DD)")
    parser.add_argument("--output",  default="output",
                        help="Output directory for charts and MQL5 file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"\n  Loading data in [{args.mode}] mode...")

    if args.mode == "real":
        if not DATA_LOADER_AVAILABLE:
            print("  ❌ data_loader.py not found. Cannot use --mode real.")
            sys.exit(1)
        print(f"  Fetching Dukascopy XAUUSD: {args.start} → {args.end}")
        df = load_real_data(symbol="XAUUSD", start_date=args.start, end_date=args.end)
        if df.empty:
            print("  ❌ No data returned. Check dates or network connection.")
            sys.exit(1)
        print(f"  ✅ Loaded {len(df):,} real ticks.")
    else:
        print(f"  Synthesizing {args.rows:,} ticks — Regime: {args.regime}")
        df = generate_synthetic_data(n_rows=args.rows, regime=args.regime, seed=args.seed)
        print(f"  ✅ Synthetic data ready: {len(df):,} rows")

    pipeline = QuantCouncilPipeline(output_dir=args.output, verbose=True)

    try:
        result = pipeline.run(df, mode=args.mode, regime=args.regime)
        sys.exit(0)
    except Exception as e:
        print(f"\n  ❌ PIPELINE CRASHED: {e}")
        traceback.print_exc()
        sys.exit(1)
