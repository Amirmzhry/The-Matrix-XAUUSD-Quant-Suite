# 🏛️ The Quant Council — Institutional-Grade HFT Tick Filtering System

> **Kaggle AI Agents Intensive Capstone** — Agents for Business Track  
> An enterprise Multi-Agent AI system that autonomously filters, validates, and synthesizes production-grade MQL5 trading code for XAUUSD (Gold) High-Frequency Trading.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Gemini 2.5 Flash](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange.svg)](https://ai.google.dev/)
[![Dukascopy](https://img.shields.io/badge/Data-Dukascopy%20Live-green.svg)](https://www.dukascopy.com/)
[![MQL5](https://img.shields.io/badge/Output-MQL5%20.mqh-purple.svg)](https://www.mql5.com/)

---

## 🎯 Project Overview

**The Quant Council** is a 5-agent ReAct (Reason + Act) pipeline that replaces human quant analysts in the HFT tick pre-processing workflow. Each agent is powered by Google Gemini 2.5 Flash and collaborates through structured JSON contracts, inner monologue transparency, and risk-gated consensus.

```
RAW XAUUSD TICK DATA (Dukascopy)
         │
    ┌────▼────────────────────────────────────────────────────┐
    │  AGENT 1: DataAnalystAgent  (Market Intelligence Scan)  │
    │  • Computes Q_Score, Volatility Matrix, Regime Tag      │
    │  • Gemini synthesizes executive narrative report        │
    └────────────────────────┬────────────────────────────────┘
                             │  {report_text, toxicity, regime, volatility}
    ┌────────────────────────▼────────────────────────────────┐
    │  AGENT 2: LeadQuantAgent  (Filter Strategy Engine)      │
    │  • Gemini reasons from first principles                 │
    │  • Selects from 5 institutional-grade filters           │
    │  • Derives parameter values with inner monologue        │
    └────────────────────────┬────────────────────────────────┘
                             │  {filter_name, params, inner_monologue}
    ┌────────────────────────▼────────────────────────────────┐
    │  AGENT 3: RiskOfficerAgent  (Safety Gatekeeper)         │
    │  • 4 Python-enforced hard floors (non-overridable)      │
    │  • Gemini issues compliance verdict + risk score        │
    │  • VETO → escalation loop (max 3 ReAct iterations)     │
    └────────────────────────┬────────────────────────────────┘
                             │  APPROVED payload
         ┌───────────────────┴──────────────────┐
    ┌────▼────────────────┐        ┌────────────▼────────────────┐
    │ AGENT 4: Visualizer │        │ AGENT 5: MQL5Synthesizer    │
    │ • 3 Plotly HTML     │        │ • Gemini writes C++ MQL5    │
    │   charts            │        │ • Strict 3-rule linter      │
    │ • Agent timeline    │        │ • Structural validator      │
    └─────────────────────┘        └─────────────────────────────┘
                             │
              HFT_Tick_Factory.mqh  +  Charts  +  MD Report
```

---

## 🏗️ Architecture

### Directory Structure

```
d:\The Matrix\
│
├── agents/                        # All 5 Gemini agent definitions
│   ├── agent1_data_analyst.py     # Market intelligence scan
│   ├── agent2_lead_quant.py       # Filter strategy engine
│   ├── agent3_risk_officer.py     # Safety gatekeeper (hard floors)
│   ├── agent4_visualizer.py       # Plotly chart generation
│   └── agent5_mql5_synthesizer.py # MQL5 C++ code synthesis
│
├── data/                          # Real tick CSVs and Dukascopy cache
│   └── XAUUSD_*.csv               # Cached hourly tick files
│
├── mql5_export/                   # Generated .mqh production files
│   └── HFT_Tick_Factory.mqh       # Deploy to MT5 Include folder
│
├── output/                        # Charts, HTML dashboards, reports
│   ├── chart1_price_overlay.html
│   ├── chart2_density_skewness.html
│   ├── chart3_agent_timeline.html
│   └── HFT_Execution_Report.md
│
├── tests/                         # Unit test suite (5 agents + E2E)
│   ├── test_agent1.py
│   ├── test_agent2.py
│   ├── test_agent3.py
│   ├── test_agent4.py
│   └── test_agent5.py
│
├── master_pipeline.py             # 🎯 Main entry point (ReAct orchestrator)
├── llm_client.py                  # Shared Gemini client (ClientOptions auth)
├── tools.py                       # Arsenal: 3 vectorized quant tools
├── tick_factory_engine.py         # Causal stateful tick filter engines
├── data_loader.py                 # Dukascopy multi-threaded data ingestion
├── app_dashboard.py               # Streamlit real-time dashboard
│
├── test_dukascopy_api.py          # Phase 2: Live data connectivity test
├── advanced_api_stress_test.py    # Phase 1: Auth & concurrent API stress test
├── run_all_tests.py               # Full test suite runner
├── smoke_test.py                  # 17-point import/unit smoke test
│
└── .env                           # API keys (never commit to git)
```

---

## 🤖 Multi-Agent Architecture

### Agent 1 — DataAnalystAgent
**Role:** Quantitative Market Intelligence  
**LLM Task:** Synthesize raw metric outputs into an executive-level narrative report  
**Tools:** `toxicity_scorer_tool`, `volatility_matrix_tool`, `market_regime_detector`  
**Output:** `{report_text, toxicity{Q_Score, dimensions}, volatility, regime}`

The Q_Score is a 5-dimensional composite toxicity metric:
| Dimension | Weight | Captures |
|---|---|---|
| RV (Relative Volatility) | 20% | Vol regime vs EWMA baseline |
| Spike Density | 25% | MAD-thresholded anomalies |
| CV (Time Asymmetry) | 15% | Tick arrival irregularity |
| Spread Toxicity | 20% | Bid-Ask spread expansion |
| Gap Score | 20% | Price jumps on time gaps >500ms |

### Agent 2 — LeadQuantAgent
**Role:** Filter Strategy Engine with Inner Monologue  
**LLM Task:** Reason from first principles to select and tune one of 5 institutional filters  
**Filter Toolkit:**
| Filter | Best For |
|---|---|
| `ADAPTIVE_KALMAN` | Normal/clean markets, zero-lag tracking |
| `MAD` | Heavy noise, non-Gaussian distributions |
| `HAMPEL` | Extreme spikes, outlier replacement |
| `EMA_ZSCORE` | Elevated/trending noise |
| `DEEP_DENOISE_HAMPEL_KALMAN` | Flash crash, nuclear recovery |

### Agent 3 — RiskOfficerAgent
**Role:** Institutional Safety Gatekeeper  
**Hard Floors (Python-enforced, LLM cannot override):**
- `MAX_VARIANCE_SHIFT = 20.0%` — Filter must not destroy price structure
- `MAX_RMSE = 0.50` — Maximum allowed signal distortion
- `MAX_NEGATIVE_SPREADS = 0` — Zero tolerance for bid-ask corruption
- `MAX_MEAN_DRIFT_PCT = 0.5%` — Preserves long-run price level

### Agent 4 — VisualizerAgent  
Generates 3 Plotly HTML interactive charts: price overlay comparison, return distribution density + skewness, and agent execution timeline waterfall.

### Agent 5 — MQL5SynthesizerAgent
**Role:** C++ Production Code Generation  
**LLM Task:** Write a complete `CTickFactory` MQL5 class from scratch  
**Linter Rules (auto-corrected):**
1. Member variables (`m_*`) must be in `private:` class scope
2. Array assignment via `=` is illegal → replaced with `ArrayCopy()`
3. All `m_*` identifiers used in method bodies must be declared

---

## 🔌 Dukascopy Live Data Integration

Real tick data is fetched directly from Dukascopy's public CDN in `.bi5` (LZMA-compressed binary) format:

```
https://datafeed.dukascopy.com/datafeed/XAUUSD/{YEAR}/{MM}/{DD}/{HH}h_ticks.bi5
```

Each 20-byte tick record is decoded as `>3I2f` (big-endian):
```
[time_delta_ms][ask_raw_int][bid_raw_int][ask_vol_float][bid_vol_float]
```
Prices are divided by `1000.0` for XAUUSD to recover the actual price.

Multi-threaded download uses 12 concurrent workers for institutional-grade throughput.

---

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and enter workspace
cd "d:\The Matrix"

# Install dependencies
.venv\Scripts\pip install google-generativeai python-dotenv requests pandas numpy plotly streamlit
```

### 2. Configure API Key
```
# .env file
GEMINI_API_KEY=AQ.<your_key_from_google_ai_studio>
```

### 3. Test Authentication
```bash
.venv\Scripts\python.exe advanced_api_stress_test.py
```

### 4. Test Dukascopy Live Data
```bash
.venv\Scripts\python.exe test_dukascopy_api.py
```

### 5. Run the Full Pipeline

**Synthetic mode (instant, no network):**
```bash
.venv\Scripts\python.exe master_pipeline.py --mode synthetic --regime HEAVY_NOISE
```

**Live Dukascopy mode:**
```bash
.venv\Scripts\python.exe master_pipeline.py --mode real --start 2025-01-06 --end 2025-01-07
```

**Flash Crash stress test:**
```bash
.venv\Scripts\python.exe master_pipeline.py --mode synthetic --regime FLASH_CRASH --rows 10000
```

### 6. Run Full Test Suite
```bash
.venv\Scripts\python.exe run_all_tests.py
```

### 7. Launch Dashboard
```bash
.venv\Scripts\streamlit run app_dashboard.py
```

---

## 📊 Output Artifacts

After each pipeline run, the `output/` folder contains:

| Artifact | Description |
|---|---|
| `HFT_Tick_Factory.mqh` | Production MQL5 header — deploy to MT5 |
| `HFT_Execution_Report.md` | Full agent debate log and metrics |
| `chart1_price_overlay.html` | Raw vs filtered price comparison |
| `chart2_density_skewness.html` | Return distribution analysis |
| `chart3_agent_timeline.html` | Agent execution waterfall |
| `cleaned_ticks.csv` | Filtered tick data ready for backtesting |

---

## 🔐 Security Architecture

- API keys are **never hardcoded** — always loaded from `.env`
- **OAuth 401 fix:** `client_options.ClientOptions(api_key=...)` bypasses Google Cloud ADC
- 4 Google Cloud credential env vars are purged at module import time
- Agent 3's hard safety floors **cannot be overridden by any LLM response**

---

## 📐 Kaggle Capstone Scorecard

| Criterion | Implementation |
|---|---|
| **Multi-Agent Architecture** | ✅ 5 specialized agents with distinct roles |
| **LLM Autonomy** | ✅ Gemini reasons from first principles (no hardcoded if/else) |
| **Inner Monologue Transparency** | ✅ All agents print structured reasoning chains |
| **Real-World Business Problem** | ✅ Institutional HFT tick filtering — $100M+ relevance |
| **Live Data Integration** | ✅ Dukascopy multi-threaded LZMA decoder |
| **Production Code Synthesis** | ✅ LLM generates deployable MQL5 C++ |
| **Safety Guardrails** | ✅ Python-enforced floors, LLM compliance auditing |
| **Reproducibility** | ✅ Synthetic mode + random seed for deterministic runs |

---

## 📄 License

MIT License — The Quant Council Team, 2025  
*Built for the Google AI Studio × Kaggle AI Agents Intensive Capstone*
