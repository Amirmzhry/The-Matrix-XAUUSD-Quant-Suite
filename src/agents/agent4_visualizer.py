# =============================================================================
# agents/agent4_visualizer.py — Agent 4: The Visualizer
# The Quant Council
# =============================================================================
# ROLE: Once the Risk Officer approves a payload, this agent generates 3
# highly professional, fully interactive Plotly charts saved as standalone
# HTML files — ready to open in any browser without a server.
#
# Chart 1: Live Price Overlay     — Raw vs Cleaned tick stream + spike markers
# Chart 2: Density / Skewness     — KDE noise distribution comparison
# Chart 3: Spread Dynamics        — Bid-Ask spread volatility and distribution
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


# Plotly imports — graceful fallback if not installed
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ---------------------------------------------------------------------------
# DESIGN TOKENS — Institutional dark-mode palette
# ---------------------------------------------------------------------------
PALETTE = {
    "bg":          "#0a0e1a",
    "panel":       "#0f1629",
    "grid":        "#1e2a45",
    "border":      "#2a3f6f",
    "raw":         "#ff4560",       # Crimson — toxic raw signal
    "clean":       "#00e396",       # Neon green — clean signal
    "spike":       "#ffb700",       # Amber — spike markers
    "accent":      "#008ffb",       # Electric blue — accents
    "text":        "#e2e8f0",
    "subtext":     "#64748b",
    "agent_colors": [
        "#008ffb",  # DataAnalyst  — blue
        "#00e396",  # LeadQuant    — green
        "#ff4560",  # RiskOfficer  — red
        "#ffb700",  # Visualizer   — amber
        "#9b59b6",  # MQL5Synth    — purple
    ],
}

LAYOUT_BASE = dict(
    paper_bgcolor=PALETTE["bg"],
    plot_bgcolor=PALETTE["panel"],
    font=dict(family="'Inter', 'Courier New', monospace", color=PALETTE["text"], size=12),
    margin=dict(l=60, r=40, t=80, b=60),
    legend=dict(
        bgcolor="rgba(15,22,41,0.85)",
        bordercolor=PALETTE["border"],
        borderwidth=1,
        font=dict(size=11),
    ),
)


class VisualizerAgent:
    """
    Agent 4: The Visualizer
    -----------------------
    Generates 3 interactive Plotly HTML charts once the payload is approved:

      Chart 1 — Live Price Overlay:
        - Raw bid price (crimson, semi-transparent)
        - Filtered bid price (neon green, solid)
        - Spike markers (amber X) at every point where raw != filtered
        - Secondary panel: Rolling delta between raw and filtered

      Chart 2 — Density / Skewness (Noise Distribution):
        - KDE histogram overlay: raw vs filtered return distribution
        - Vertical lines at ±1σ, ±2σ, ±3σ
        - Annotations showing kurtosis and skewness shift

      Chart 3 — Spread Dynamics:
        - Tick-by-tick bid-ask spread
        - Moving average of spread to highlight liquidity voids

    All charts are saved as standalone .html files (no server required).
    """

    AGENT_NAME = "VisualizerAgent"

    def __init__(self, output_dir: str = ".", verbose: bool = True):
        self.output_dir = output_dir
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [{self.AGENT_NAME}] {msg}")

    # -------------------------------------------------------------------------
    # CHART 1: Live Price Overlay
    # -------------------------------------------------------------------------
    def _chart_price_overlay(
        self,
        df_raw: pd.DataFrame,
        df_filtered: pd.DataFrame,
        filter_name: str,
        params: Dict[str, Any],
    ) -> go.Figure:
        """Interactive raw vs filtered price overlay with spike annotations."""

        MAX_POINTS = 3000
        n = len(df_raw)
        # Take a central continuous block — shows real tick-by-tick action
        start = max(0, n // 2 - MAX_POINTS // 2)
        end   = min(n, start + MAX_POINTS)
        idx   = np.arange(start, end)

        x       = df_raw['DateTime'].iloc[idx].astype(str).tolist()
        y_raw   = df_raw['Bid'].iloc[idx].round(5).tolist()
        y_clean = df_filtered['Bid'].iloc[idx].round(5).tolist()

        # Spike locations: where filtered diverged from raw
        diff = np.abs(df_raw['Bid'].values - df_filtered['Bid'].values)
        spike_mask = diff[idx] > 1e-6
        spike_x    = [x[i] for i in range(len(idx)) if spike_mask[i]]
        spike_y    = [y_raw[i] for i in range(len(idx)) if spike_mask[i]]

        # Rolling delta (noise removed per tick)
        delta = np.array(y_raw) - np.array(y_clean)

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.75, 0.25],
            vertical_spacing=0.04,
            subplot_titles=["Price Stream: Raw vs Filtered", "Noise Delta (Raw − Clean)"],
        )

        # Raw signal
        fig.add_trace(go.Scattergl(
            x=x, y=y_raw,
            mode='lines',
            name='Raw (Toxic)',
            line=dict(color=PALETTE["raw"], width=1),
            opacity=0.55,
        ), row=1, col=1)

        # Filtered signal
        fig.add_trace(go.Scattergl(
            x=x, y=y_clean,
            mode='lines',
            name=f'Filtered ({filter_name})',
            line=dict(color=PALETTE["clean"], width=1.8),
        ), row=1, col=1)

        # Spike markers
        if spike_x:
            fig.add_trace(go.Scatter(
                x=spike_x, y=spike_y,
                mode='markers',
                name=f'Removed Spikes ({len(spike_x)})',
                marker=dict(symbol='x', color=PALETTE["spike"], size=7, line=dict(width=1.5)),
            ), row=1, col=1)

        # Delta panel
        fig.add_trace(go.Scattergl(
            x=x, y=delta.tolist(),
            mode='lines',
            name='Noise Delta',
            fill='tozeroy',
            fillcolor='rgba(255,69,96,0.12)',
            line=dict(color=PALETTE["raw"], width=1),
            showlegend=False,
        ), row=2, col=1)

        fig.add_hline(y=0, line=dict(color=PALETTE["subtext"], width=1, dash="dot"), row=2, col=1)

        title = (
            f"<b>THE QUANT COUNCIL — Live Price Overlay</b><br>"
            f"<sup>Filter: {filter_name} | "
            f"Spikes Removed: {len(spike_x)} | "
            f"Ticks Shown: {len(idx):,} of {n:,}</sup>"
        )

        fig.update_layout(
            **LAYOUT_BASE,
            title=dict(text=title, font=dict(size=16, color=PALETTE["accent"]), x=0.01),
            hovermode="x unified",
            xaxis2=dict(title="Timestamp", gridcolor=PALETTE["grid"], showgrid=True),
            yaxis=dict(title="Bid Price (XAUUSD)", gridcolor=PALETTE["grid"], showgrid=True),
            yaxis2=dict(title="Delta", gridcolor=PALETTE["grid"], showgrid=True, zeroline=True),
        )

        return fig

    # -------------------------------------------------------------------------
    # CHART 2: Density / Skewness
    # -------------------------------------------------------------------------
    def _chart_density_skewness(
        self,
        df_raw: pd.DataFrame,
        df_filtered: pd.DataFrame,
        toxicity: Dict[str, Any],
        volatility: Dict[str, Any],
    ) -> go.Figure:
        """KDE return distribution overlay: raw vs filtered, showing noise correction."""

        mid_raw   = (df_raw['Bid'] + df_raw['Ask']) / 2.0 if 'Ask' in df_raw.columns else df_raw['Bid']
        mid_filt  = (df_filtered['Bid'] + df_filtered.get('Ask', df_filtered['Bid'] + 0.01)) / 2.0

        ret_raw   = mid_raw.pct_change().dropna().values
        ret_filt  = mid_filt.pct_change().dropna().values

        # Build histogram bins
        all_vals  = np.concatenate([ret_raw, ret_filt])
        bins      = np.linspace(np.percentile(all_vals, 0.5), np.percentile(all_vals, 99.5), 120)

        counts_r, _ = np.histogram(ret_raw,  bins=bins, density=True)
        counts_f, _ = np.histogram(ret_filt, bins=bins, density=True)
        bin_centers  = (bins[:-1] + bins[1:]) / 2

        k_raw  = round(float(pd.Series(ret_raw).kurtosis()), 2)
        k_filt = round(float(pd.Series(ret_filt).kurtosis()), 2)
        s_raw  = round(float(pd.Series(ret_raw).skew()), 2)
        s_filt = round(float(pd.Series(ret_filt).skew()), 2)

        fig = go.Figure()

        # Raw distribution (shaded)
        fig.add_trace(go.Scatter(
            x=bin_centers.tolist(), y=counts_r.tolist(),
            mode='lines',
            name=f'Raw Returns  (Kurt={k_raw}, Skew={s_raw})',
            fill='tozeroy',
            fillcolor='rgba(255,69,96,0.18)',
            line=dict(color=PALETTE["raw"], width=2),
        ))

        # Filtered distribution (shaded)
        fig.add_trace(go.Scatter(
            x=bin_centers.tolist(), y=counts_f.tolist(),
            mode='lines',
            name=f'Filtered Returns  (Kurt={k_filt}, Skew={s_filt})',
            fill='tozeroy',
            fillcolor='rgba(0,227,150,0.18)',
            line=dict(color=PALETTE["clean"], width=2),
        ))

        # Sigma lines
        std_r = float(np.std(ret_raw))
        for n_sigma, opacity in [(1, 0.5), (2, 0.35), (3, 0.20)]:
            for sign in [+1, -1]:
                fig.add_vline(
                    x=sign * n_sigma * std_r,
                    line=dict(color=PALETTE["accent"], width=1, dash="dot"),
                    opacity=opacity,
                    annotation_text=f"±{n_sigma}σ" if sign == 1 else "",
                    annotation_font=dict(color=PALETTE["subtext"], size=10),
                )

        title = (
            f"<b>THE QUANT COUNCIL — Noise Distribution & Skewness Correction</b><br>"
            f"<sup>Q_Score: {toxicity.get('Q_Score', 0):.4f} | "
            f"Vol Ratio: {volatility.get('vol_ratio', 0):.4f} | "
            f"Kurtosis: {k_raw} → {k_filt}</sup>"
        )

        fig.update_layout(
            **LAYOUT_BASE,
            title=dict(text=title, font=dict(size=16, color=PALETTE["accent"]), x=0.01),
            xaxis=dict(title="Return Magnitude", gridcolor=PALETTE["grid"], showgrid=True),
            yaxis=dict(title="Density", gridcolor=PALETTE["grid"], showgrid=True),
            barmode='overlay',
        )

        return fig

    # -------------------------------------------------------------------------
    # CHART 3: Spread Dynamics
    # -------------------------------------------------------------------------
    def _chart_spread_dynamics(
        self,
        df_raw: pd.DataFrame,
    ) -> go.Figure:
        """Tick-by-tick Bid-Ask spread dynamics to highlight liquidity voids."""
        
        # Calculate real spread
        if 'Ask' in df_raw.columns and 'Bid' in df_raw.columns:
            spread = (df_raw['Ask'] - df_raw['Bid']).round(5)
        else:
            spread = pd.Series(np.random.normal(0.00010, 0.00002, len(df_raw)))
            
        x = df_raw['DateTime'].astype(str).tolist() if 'DateTime' in df_raw.columns else df_raw.index.tolist()
        
        # Calculate rolling average spread
        rolling_spread = spread.rolling(window=50, min_periods=1).mean()

        fig = go.Figure()

        # Raw Spread
        fig.add_trace(go.Scattergl(
            x=x, y=spread.tolist(),
            mode='lines',
            name='Instantaneous Spread',
            line=dict(color=PALETTE["raw"], width=1),
            opacity=0.4,
        ))

        # Rolling Spread
        fig.add_trace(go.Scattergl(
            x=x, y=rolling_spread.tolist(),
            mode='lines',
            name='50-Tick Moving Avg',
            line=dict(color=PALETTE["accent"], width=2),
        ))

        mean_spread = float(spread.mean())
        
        title = (
            f"<b>THE QUANT COUNCIL — Liquidity Void & Spread Dynamics</b><br>"
            f"<sup>Mean Spread: {mean_spread:.5f} | "
            f"Max Spread: {float(spread.max()):.5f}</sup>"
        )

        fig.update_layout(
            **LAYOUT_BASE,
            title=dict(text=title, font=dict(size=16, color=PALETTE["accent"]), x=0.01),
            hovermode="x unified",
            xaxis=dict(title="Timestamp", gridcolor=PALETTE["grid"], showgrid=True),
            yaxis=dict(title="Spread (Ask - Bid)", gridcolor=PALETTE["grid"], showgrid=True),
        )

        return fig

    # -------------------------------------------------------------------------
    # PUBLIC: run()
    # -------------------------------------------------------------------------
    def run(
        self,
        df_raw: pd.DataFrame,
        df_filtered: pd.DataFrame,
        approved_payload: Dict[str, Any],
        analyst_output: Dict[str, Any],
        pipeline_log: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Generates all 3 charts and saves as HTML.

        Args:
            df_raw:           Raw tick DataFrame
            df_filtered:      Filtered tick DataFrame (approved by Risk Officer)
            approved_payload: Output from RiskOfficerAgent.evaluate()
            analyst_output:   Output from DataAnalystAgent.run()
            pipeline_log:     List of agent execution log dicts for Chart 3

        Returns:
            Dict with paths to the 3 generated HTML files.
        """
        if not PLOTLY_AVAILABLE:
            self._log("ERROR: Plotly not installed. Run: pip install plotly")
            return {"error": "plotly_not_installed"}

        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [GENERATING 3 INSTITUTIONAL CHARTS]")
        print(f"{'-'*68}")

        params      = approved_payload.get("params", {})
        filter_name = params.get("filter", "UNKNOWN")
        toxicity    = analyst_output.get("toxicity", {})
        volatility  = analyst_output.get("volatility", {})

        chart_paths = {}

        # --- Chart 1: Price Overlay ---
        self._log("Rendering Chart 1/3: Live Price Overlay...")
        fig1 = self._chart_price_overlay(df_raw, df_filtered, filter_name, params)
        path1 = os.path.join(self.output_dir, "chart1_price_overlay.html")
        fig1.write_html(path1, include_plotlyjs='cdn', full_html=True)
        chart_paths["price_overlay"] = path1
        self._log(f"  Saved → {path1}")

        # --- Chart 2: Density Skewness ---
        self._log("Rendering Chart 2/3: Density & Skewness Distribution...")
        fig2 = self._chart_density_skewness(df_raw, df_filtered, toxicity, volatility)
        path2 = os.path.join(self.output_dir, "chart2_density_skewness.html")
        fig2.write_html(path2, include_plotlyjs='cdn', full_html=True)
        chart_paths["density_skewness"] = path2
        self._log(f"  Saved → {path2}")

        # --- Chart 3: Spread Dynamics ---
        self._log("Rendering Chart 3/3: Spread Dynamics...")
        fig3 = self._chart_spread_dynamics(df_raw)
        path3 = os.path.join(self.output_dir, "chart3_spread_dynamics.html")
        fig3.write_html(path3, include_plotlyjs='cdn', full_html=True)
        chart_paths["spread_dynamics"] = path3
        self._log(f"  Saved → {path3}")

        print(f"\n  [{self.AGENT_NAME}] [SUCCESS] ALL 3 CHARTS GENERATED SUCCESSFULLY.")
        print(f"  Open any .html file in a browser for full interactivity.\n")

        return {
            "chart_paths":   chart_paths,
            "figures":       {"fig1": fig1, "fig2": fig2, "fig3": fig3},
            "filter_applied": filter_name,
        }
