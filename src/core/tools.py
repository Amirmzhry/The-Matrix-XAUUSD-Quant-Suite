# =============================================================================
# tools.py — The Arsenal
# The Quant Council: Callable Tool Library for LLM Agents
# =============================================================================
# These 3 functions are the mathematical core of the system.
# They are designed to be called directly by agent classes as discrete,
# stateless tools — each takes a DataFrame and returns a structured dict.
#
# Extracted and refactored from: data_toxicity_profiler.py
# =============================================================================

import numpy as np
import pandas as pd
from typing import Dict, Any


# =============================================================================
# TOOL 1: Toxicity Scorer
# =============================================================================

def toxicity_scorer_tool(df: pd.DataFrame) -> Dict[str, Any]:
    """
    TOOL: toxicity_scorer_tool
    --------------------------
    Calculates a 5-dimensional toxicity score for a raw tick DataFrame.

    Each dimension captures a distinct pathological market condition:
      1. RV       — Relative Volatility (realized vol vs EWMA baseline)
      2. Spike    — Anomalous spike density via MAD thresholding (>3 sigma)
      3. CV       — Time-Asymmetry (Coefficient of Variation of time deltas)
      4. Spread   — Bid-Ask spread expansion toxicity (MAD normalized)
      5. Gap      — Price jumps during time gaps > 500ms

    Returns:
        Dict with keys:
          - Q_Score (float): Weighted composite score [0.0, 1.0]
          - dimensions (dict): Individual scores for all 5 axes
          - weights (list): [0.20, 0.25, 0.15, 0.20, 0.20]
          - interpretation (str): Human-readable severity label
    """

    def _normalize(score: float, min_val: float, max_val: float) -> float:
        if np.isnan(score) or np.isinf(score):
            return 0.0
        return float(np.clip((score - min_val) / (max_val - min_val + 1e-9), 0.0, 1.0))

    # --- Pre-compute shared mid-price series (avoids redundant (Bid+Ask)/2) ---
    mid         = (df['Bid'] + df['Ask']) * 0.5          # vectorized
    returns     = mid.pct_change().dropna()
    spread_s    = (df['Ask'] - df['Bid'])                 # vectorized
    timestamps  = pd.to_datetime(df['DateTime'])
    dt_sec      = timestamps.diff().dt.total_seconds().dropna()

    # --- Dimension 1: Relative Volatility (vectorized rolling) ---
    def _calc_rv() -> float:
        if returns.empty:
            return 0.0
        rv       = returns.rolling(window=10).std()
        ewma_rv  = rv.ewm(span=20).mean()
        rel_vol  = (rv / (ewma_rv + 1e-9)).mean()
        return _normalize(rel_vol, 0.0, 5.0)

    # --- Dimension 2: Spike Density (MAD-based, fully vectorized) ---
    def _calc_spike() -> float:
        if returns.empty:
            return 0.0
        median  = returns.median()
        mad     = (returns - median).abs().median()
        if mad == 0:
            return 0.0
        spike_mask = (returns - median).abs() > (3.0 * mad)
        return _normalize(spike_mask.sum() / len(returns), 0.0, 0.1)

    # --- Dimension 3: Time Asymmetry (CV of deltas, vectorized) ---
    def _calc_cv() -> float:
        if dt_sec.empty or dt_sec.mean() == 0:
            return 0.0
        return _normalize(dt_sec.std() / dt_sec.mean(), 0.0, 5.0)

    # --- Dimension 4: Spread Toxicity (vectorized MAD normalization) ---
    def _calc_spread() -> float:
        if spread_s.empty:
            return 0.0
        median_s = spread_s.median()
        mad_s    = (spread_s - median_s).abs().median()
        if mad_s == 0:
            return 0.0
        tox      = (spread_s - median_s) / mad_s
        pos_tox  = tox[tox > 0]
        avg_tox  = pos_tox.mean() if not pos_tox.empty else 0.0
        return _normalize(avg_tox, 0.0, 10.0)

    # --- Dimension 5: Gap Score (vectorized boolean mask join) ---
    def _calc_gap() -> float:
        if dt_sec.empty:
            return 0.0
        jumps      = mid.diff().abs().dropna()             # vectorized
        large_mask = dt_sec > 0.500
        # Align index — dt_sec and jumps both have 1 less row than df
        aligned_jumps = jumps.reindex(large_mask.index)
        gap_jumps = aligned_jumps[large_mask]
        if gap_jumps.empty:
            return 0.0
        avg_jump = gap_jumps.mean()
        return _normalize(avg_jump, 0.0, 2.0)

    # --- Compute all 5 dimensions in one sweep ---
    rv     = _calc_rv()
    spike  = _calc_spike()
    cv     = _calc_cv()
    spread = _calc_spread()
    gap    = _calc_gap()

    weights = np.array([0.20, 0.25, 0.15, 0.20, 0.20])
    metrics = np.array([rv, spike, cv, spread, gap])
    q_score = float(np.dot(metrics, weights))

    # Human-readable interpretation
    if q_score >= 0.70:
        interpretation = "CRITICAL — Flash Crash conditions detected."
    elif q_score >= 0.45:
        interpretation = "HIGH — Heavy microstructure noise. Aggressive filtering required."
    elif q_score >= 0.20:
        interpretation = "MODERATE — Elevated noise. Standard filtering recommended."
    else:
        interpretation = "LOW — Market data is relatively clean."

    return {
        "Q_Score": round(q_score, 6),
        "dimensions": {
            "RV":     round(rv, 6),
            "Spike":  round(spike, 6),
            "CV":     round(cv, 6),
            "Spread": round(spread, 6),
            "Gap":    round(gap, 6),
        },
        "weights": weights.tolist(),
        "interpretation": interpretation,
    }


# =============================================================================
# TOOL 2: Volatility Matrix
# =============================================================================

def volatility_matrix_tool(df: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
    """
    TOOL: volatility_matrix_tool
    ----------------------------
    Calculates a multi-dimensional volatility and momentum profile
    from raw tick data over a configurable rolling window.

    Metrics:
      - realized_vol:   Rolling std of mid-price returns (proxy for realized vol)
      - ewma_baseline:  EWMA of realized_vol (the 'calm' reference)
      - vol_ratio:      realized_vol / ewma_baseline  (>1.0 = elevated stress)
      - roc_mean:       Mean Rate of Change over window
      - roc_std:        Std of Rate of Change (core noise metric used by V1/V2)
      - price_range:    [min, max] of mid-price
      - kurtosis:       Tail fatness of return distribution (>3 = fat tails)
      - skewness:       Return asymmetry (|val|>1 = strongly skewed)
      - stress_flag:    True if vol_ratio>1.5 OR kurtosis>5 (pathological)

    Returns:
        Dict with all volatility metrics and a boolean stress_flag.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}

    mid = (df['Bid'] + df['Ask']) / 2.0
    returns = mid.pct_change().dropna()

    if returns.empty:
        return {"error": "Insufficient data for returns calculation"}

    realized_vol   = returns.rolling(window=window).std().dropna()
    ewma_baseline  = realized_vol.ewm(span=window * 2).mean()
    vol_ratio_s    = realized_vol / (ewma_baseline + 1e-9)
    vol_ratio      = float(vol_ratio_s.mean())

    roc = mid.pct_change(periods=5).dropna()

    return {
        "realized_vol":  round(float(realized_vol.mean()), 8),
        "ewma_baseline": round(float(ewma_baseline.mean()), 8),
        "vol_ratio":     round(vol_ratio, 6),
        "roc_mean":      round(float(roc.mean()), 8),
        "roc_std":       round(float(roc.std()), 8),
        "price_range":   [round(float(mid.min()), 5), round(float(mid.max()), 5)],
        "kurtosis":      round(float(returns.kurtosis()), 4),
        "skewness":      round(float(returns.skew()), 4),
        "tick_count":    len(df),
        "window_used":   window,
        "stress_flag":   bool(vol_ratio > 1.5 or abs(returns.kurtosis()) > 5),
    }


# =============================================================================
# TOOL 3: Market Regime Detector
# =============================================================================

def market_regime_detector(
    toxicity_result: Dict[str, Any],
    volatility_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    TOOL: market_regime_detector
    ----------------------------
    Combines Q_Score from toxicity_scorer_tool and volatility metrics from
    volatility_matrix_tool to produce a definitive market regime tag and
    recommended filter strategy for all downstream agents.

    Regime Decision Tree (Priority Order):
      1. FLASH_CRASH   -> Q_Score >= 0.70 OR vol_ratio > 3.0 OR gap_dim > 0.8
      2. EXTREME_SPIKE -> Q_Score >= 0.55 OR (Spike dim > 0.6 AND kurtosis > 5)
      3. HEAVY_NOISE   -> Q_Score >= 0.35 OR vol_ratio > 1.5
      4. ELEVATED      -> Q_Score >= 0.20 OR stress_flag = True
      5. NORMAL        -> Everything else

    Returns:
        Dict with:
          - regime (str):             Tagged market state
          - confidence (float):       0.0-1.0 classification confidence
          - recommended_filter (str): Optimal filter for LeadQuantAgent
          - recommended_k (float):    Aggressiveness parameter (None = self-tuning)
          - reasoning (str):          Plain-English inner monologue explanation
    """
    q        = toxicity_result.get("Q_Score", 0.0)
    dims     = toxicity_result.get("dimensions", {})
    spike_d  = dims.get("Spike", 0.0)
    gap_d    = dims.get("Gap", 0.0)

    vol_ratio = volatility_result.get("vol_ratio", 1.0)
    kurtosis  = volatility_result.get("kurtosis", 0.0)
    stress    = volatility_result.get("stress_flag", False)
    roc_std   = volatility_result.get("roc_std", 0.0)

    # --- Regime Classification (cascading priority) ---
    if q >= 0.70 or vol_ratio > 3.0 or gap_d > 0.8:
        regime     = "FLASH_CRASH"
        confidence = min(1.0, q * 0.5 + min(vol_ratio / 4.0, 0.5))
        rec_filter = "DEEP_DENOISE_HAMPEL_KALMAN"
        rec_k      = 2.0
        reasoning  = (
            f"FLASH CRASH confirmed. Q_Score={q:.3f}, vol_ratio={vol_ratio:.2f}, "
            f"gap_dim={gap_d:.3f}. Nuclear Hampel->Kalman chained pipeline "
            "is the only safe recovery protocol."
        )

    elif q >= 0.55 or (spike_d > 0.6 and abs(kurtosis) > 5):
        regime     = "EXTREME_SPIKE"
        confidence = min(1.0, q * 0.9 + spike_d * 0.1)
        rec_filter = "HAMPEL"
        rec_k      = 2.5
        reasoning  = (
            f"Extreme spike regime. Q_Score={q:.3f}, spike_dim={spike_d:.3f}, "
            f"kurtosis={kurtosis:.2f}. Hampel Identifier is optimal — replaces "
            "confirmed outliers with local trailing median, preserving structure."
        )

    elif q >= 0.35 or vol_ratio > 1.5:
        regime     = "HEAVY_NOISE"
        confidence = min(1.0, q * 0.7 + min(vol_ratio / 2.0, 0.3))
        rec_filter = "MAD"
        rec_k      = 3.0
        reasoning  = (
            f"Heavy noise regime. Q_Score={q:.3f}, vol_ratio={vol_ratio:.2f}. "
            "Trailing MAD Clipper is optimal — robust adaptive containment "
            "without Gaussian assumptions."
        )

    elif q >= 0.20 or stress:
        regime     = "ELEVATED"
        confidence = max(0.4, q * 0.8)
        rec_filter = "EMA_ZSCORE"
        rec_k      = 3.0
        reasoning  = (
            f"Elevated noise. Q_Score={q:.3f}, stress_flag={stress}. "
            "EMA-weighted Z-Score provides smooth adaptive filtering "
            "suitable for mildly elevated microstructure conditions."
        )

    else:
        regime     = "NORMAL"
        confidence = max(0.85, 1.0 - q * 2)
        rec_filter = "ADAPTIVE_KALMAN"
        rec_k      = None   # Adaptive Kalman self-tunes its noise covariance
        reasoning  = (
            f"Normal market conditions. Q_Score={q:.3f}, vol_ratio={vol_ratio:.2f}. "
            "Adaptive Kalman Tracker is ideal — zero-lag tracking with minimal "
            "intervention under stable microstructure."
        )

    return {
        "regime":             regime,
        "confidence":         round(confidence, 4),
        "Q_Score":            q,
        "vol_ratio":          round(vol_ratio, 4),
        "roc_std":            round(roc_std, 8),
        "recommended_filter": rec_filter,
        "recommended_k":      rec_k,
        "reasoning":          reasoning,
    }
