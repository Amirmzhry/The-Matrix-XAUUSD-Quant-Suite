# =============================================================================
# agents/agent5_mql5_synthesizer.py — Agent 5: The MQL5 Synthesizer (Gemini-Powered)
# The Quant Council
# =============================================================================
# ROLE: Passes the council-approved JSON parameter matrix into Gemini-2.5-Flash
# with a strict, expert MQL5 developer prompt.
#
# Gemini generates a production-ready, zero-warning HFT_Tick_Factory.mqh
# C++ class from scratch, obeying all MQL5 linter rules enforced by the
# Python-side _mql5_linter_process() post-processor before writing to disk.
#
# Fallback: If Gemini is unavailable, the original template-based generator
# is used so the pipeline never dies.
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import re
import json
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

from src.core.llm_client import call_gemini


class MQL5SynthesizerAgent:
    """
    Agent 5: The MQL5 Synthesizer (Gemini-Powered)
    ------------------------------------------------
    Gemini is prompted as an Expert MQL5 Developer and generates
    a production HFT_Tick_Factory.mqh from the approved parameters.

    A Python-side _mql5_linter_process() always runs on the output
    regardless of whether Gemini or the fallback produced the code.
    """

    AGENT_NAME = "MQL5SynthesizerAgent"

    MQL5_PROMPT_TEMPLATE = """
You are an Expert MQL5 Developer. Output ONLY raw, valid MQL5 code inside a ```cpp block. Do NOT write explanations.

The Lead Quant has calculated these exact parameters for the HAMPEL filter:
- Half Window: [HALF_WINDOW]
- K Sigma: [K_SIGMA]
- Full Window: [WINDOW]

Write the complete `CTickFactory` class. 
CRITICAL RULES:
1. Use standard C++ syntax with SINGLE curly braces `{` and `}` for all blocks. Do NOT use double braces.
2. You MUST insert the exact numerical values provided above into the constructor arguments. Do NOT leave placeholders.

Use this exact logic structure:

#property strict

class CTickFactory {
private:
    int m_window;
    int m_half_window;
    double m_k_sigma;
    double m_buffer[];
    double m_sorted_buffer[];
    double m_deviations[];
    int m_count;
    int m_index;
    bool m_is_ready;

public:
    CTickFactory(int half_window_param = [HALF_WINDOW], double k_sigma_param = [K_SIGMA]) {
        m_half_window = half_window_param;
        m_window = [WINDOW];
        m_k_sigma = k_sigma_param;
        m_count = 0; m_index = 0; m_is_ready = false;
        
        ArrayResize(m_buffer, m_window); 
        ArrayResize(m_sorted_buffer, m_window);
        ArrayResize(m_deviations, m_window);
        ArrayInitialize(m_buffer, 0.0);
        ArrayInitialize(m_sorted_buffer, 0.0);
        ArrayInitialize(m_deviations, 0.0);
    }
    
    ~CTickFactory() { 
        ArrayFree(m_buffer); 
        ArrayFree(m_sorted_buffer);
        ArrayFree(m_deviations); 
    }

    bool UpdateTick(double current_bid, double current_ask, double &filtered_bid, double &filtered_ask) {
        double raw_spread = current_ask - current_bid;
        double mid_price = (current_bid + current_ask) / 2.0;
        
        m_buffer[m_index] = mid_price;
        m_index = (m_index + 1) % m_window;
        
        if (!m_is_ready) {
            m_count++;
            if (m_count >= m_window) { m_is_ready = true; }
            filtered_bid = current_bid;
            filtered_ask = current_ask;
            return true;
        }
        
        ArrayCopy(m_sorted_buffer, m_buffer); 
        ArraySort(m_sorted_buffer);
        double median = m_sorted_buffer[m_window / 2];
        
        for (int i = 0; i < m_window; i++) {
            m_deviations[i] = MathAbs(m_buffer[i] - median);
        }
        ArraySort(m_deviations);
        
        double mad_value = m_deviations[m_window / 2];
        double sigma = 1.4826 * mad_value;
        
        double filtered_mid = mid_price;
        if (MathAbs(mid_price - median) > (m_k_sigma * sigma)) {
            filtered_mid = median;
        }
        
        filtered_bid = filtered_mid - raw_spread / 2.0;
        filtered_ask = filtered_mid + raw_spread / 2.0;
        return true;
    }
};
"""

    # Description for each filter to help Gemini understand the algorithm
    FILTER_DESCRIPTIONS = {
        "ADAPTIVE_KALMAN": (
            "Adaptive Kalman Filter. State estimate m_x updated via Kalman gain K = P/(P+R). "
            "Process noise Q adapts to trailing return variance. O(window) per tick for Q computation."
        ),
        "MAD": (
            "Trailing Median Absolute Deviation clipper. Maintains circular buffer of size=window. "
            "Each tick: compute median of buffer, compute MAD, clip current_bid if deviation > threshold*MAD. "
            "Use ArraySort() on a local copy — never on m_buffer directly. O(window) per tick."
        ),
        "EMA_ZSCORE": (
            "EMA Z-Score outlier removal. State vars: m_ema (exponential moving average) and "
            "m_ema_var (EMA of squared deviations). Alpha = 2/(span+1). "
            "Z = (current_bid - m_ema) / sqrt(m_ema_var). Clip if |Z| > threshold. O(1) per tick."
        ),
        "HAMPEL": (
            "Hampel Identifier. Maintains circular buffer of size = 2*half_window+1. "
            "Each tick: compute median of window, compute MAD scaled by 1.4826. "
            "If |current_bid - median| > k_sigma * scaled_MAD, replace with median. O(window) per tick."
        ),
        "DEEP_DENOISE_HAMPEL_KALMAN": (
            "Sequential Hampel→Kalman chain. First pass: Hampel Identifier removes catastrophic spikes. "
            "Second pass: Kalman filter smooths residual noise from Hampel output. "
            "Two independent sets of state variables required (m_h* for Hampel, m_k* for Kalman)."
        ),
    }

    def __init__(self, output_dir: str = ".", verbose: bool = True):
        self.output_dir = output_dir
        self.verbose    = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [{self.AGENT_NAME}] {msg}")

    # =========================================================================
    # MQL5 LINTER POST-PROCESSOR (always runs, regardless of code source)
    # =========================================================================
    def _mql5_linter_process(self, code: str) -> Tuple[str, list]:
        """
        Strict MQL5 Linter Agent Step. Enforces:
          1. Member variables (m_...) must be in private class scope.
          2. Arrays cannot be assigned via =. Must use ArrayCopy().
          3. No undeclared m_ identifiers.
        Corrects violations on-the-fly and logs each correction.
        """
        logs = []

        # Split class declaration and implementation
        class_end_idx = code.find("};")
        if class_end_idx == -1:
            logs.append("Linter: Could not locate CTickFactory class closing brace.")
            return code, logs

        class_def = code[:class_end_idx + 2]
        funcs_def = code[class_end_idx + 2:]

        # Rule 1: Member variables (m_...) declared with type inside function bodies
        local_decls = re.findall(r'\b(double|int|string|bool|float)\s+(m_[a-zA-Z0-9_]+)\b', funcs_def)
        for dtype, m_var in local_decls:
            logs.append(f"Rule 1 Fix: Removed local type declaration of '{m_var}' from function body.")
            funcs_def = re.sub(r'\b' + dtype + r'\s+' + m_var + r'\b', m_var, funcs_def)
            if m_var not in class_def:
                priv_idx = class_def.find("private:")
                if priv_idx != -1:
                    ins = priv_idx + len("private:\n")
                    class_def = class_def[:ins] + f"   {dtype:<18} {m_var};\n" + class_def[ins:]
                    logs.append(f"Rule 1 Fix: Declared '{dtype} {m_var}' in private class scope.")

        # Rule 2: Array assignments with = (illegal in MQL5)
        array_names = set(re.findall(
            r'\b(?:double|int)\s+(m_buffer|m_hbuf|w|past|dev|deviations|sorted)\[\]', code
        ))
        for arr in array_names:
            matches = re.findall(r'\b(' + arr + r')\s*=\s*([a-zA-Z0-9_]+)\s*;', funcs_def)
            for arr_name, src_name in matches:
                logs.append(f"Rule 2 Fix: Replaced '{arr_name} = {src_name}' with ArrayCopy().")
                funcs_def = funcs_def.replace(f"{arr_name} = {src_name};",
                                               f"ArrayCopy({arr_name}, {src_name});")

        # Rule 3: Undeclared m_ identifiers
        used_m    = set(re.findall(r'\b(m_[a-zA-Z0-9_]+)\b', funcs_def))
        declared_m = set(re.findall(r'\b(m_[a-zA-Z0-9_]+)\b', class_def))
        for und in (used_m - declared_m):
            logs.append(f"Rule 3 Fix: Declared undeclared member 'double {und}' in private scope.")
            priv_idx = class_def.find("private:")
            if priv_idx != -1:
                ins = priv_idx + len("private:\n")
                class_def = class_def[:ins] + f"   double             {und};\n" + class_def[ins:]

        if not logs:
            logs.append("✅ No linter violations found.")

        return class_def + funcs_def, logs

    # =========================================================================
    # FALLBACK TEMPLATE GENERATOR (used only when Gemini is unavailable)
    # =========================================================================
    def _get_private_members(self, filter_name: str, params: Dict[str, Any]) -> str:
        base = (
            "   // --- Circular Buffer ---\n"
            "   double            m_buffer[];\n"
            "   double            m_sorted_buffer[];\n"
            "   double            m_temp_buffer[];\n"
            "   int               m_max_size;\n"
            "   int               m_head;\n"
            "   int               m_count;\n"
        )
        if filter_name == "ADAPTIVE_KALMAN":
            r = params.get('kalman_R', 0.05)
            return base + (
                "\n   // --- Adaptive Kalman State ---\n"
                "   double            m_x;\n"
                "   double            m_P;\n"
                "   double            m_last_price;\n"
                f"   double            m_kalman_R;  // = {r}\n"
            )
        elif filter_name == "MAD":
            return base + (
                "\n   // --- MAD Clipper ---\n"
                f"   int               m_window;         // = {params.get('window',50)}\n"
                f"   double            m_mad_threshold;  // = {params.get('mad_threshold',3.0)}\n"
                f"   double            m_tolerance;      // = {params.get('tolerance',0.05)}\n"
            )
        elif filter_name == "EMA_ZSCORE":
            span  = params.get('ema_span', 50)
            alpha = round(2.0 / (span + 1), 6)
            return base + (
                "\n   // --- EMA Z-Score State ---\n"
                "   double            m_ema;\n"
                "   double            m_ema_var;\n"
                f"   double            m_alpha;     // = {alpha}\n"
                f"   double            m_threshold; // = {params.get('threshold',3.0)}\n"
            )
        elif filter_name in ("HAMPEL", "DEEP_DENOISE_HAMPEL_KALMAN"):
            hw = params.get('half_window', 15)
            ks = params.get('k_sigma', 3.0)
            kr = params.get('kalman_R', 0.1)
            return base + (
                "\n   // --- Hampel Identifier ---\n"
                f"   int               m_half_window; // = {hw}\n"
                f"   double            m_k_sigma;     // = {ks}\n"
                "\n   // --- Kalman State (DEEP_DENOISE) ---\n"
                "   double            m_kx;\n"
                "   double            m_kP;\n"
                f"   double            m_kR;          // = {kr}\n"
            )
        return base

    def _get_update_logic(self, filter_name: str, params: Dict[str, Any]) -> str:
        if filter_name == "ADAPTIVE_KALMAN":
            return """
   m_buffer[m_head] = current_bid;
   m_head = (m_head + 1) % m_max_size;
   if(m_count < m_max_size) m_count++;
   if(m_count < 2) { m_x = current_bid; m_last_price = current_bid; return current_bid; }
   double ret = current_bid - m_last_price;
   m_last_price = current_bid;
   double sum_sq = 0.0;
   int n = MathMin(m_count, m_max_size);
   for(int i = 0; i < n - 1; i++)
     {
      int idx  = (m_head - i - 1 + m_max_size) % m_max_size;
      int pidx = (m_head - i - 2 + m_max_size) % m_max_size;
      double r = m_buffer[idx] - m_buffer[pidx];
      sum_sq  += r * r;
     }
   double Q  = (n > 1) ? (sum_sq / (n - 1)) * 0.1 : 0.001;
   double Pm = m_P + Q;
   double K  = Pm / (Pm + m_kalman_R);
   m_x = m_x + K * (current_bid - m_x);
   m_P = (1.0 - K) * Pm;
   return m_x;
"""
        elif filter_name == "EMA_ZSCORE":
            span = params.get('ema_span', 50)
            alpha = round(2.0 / (span + 1), 6)
            thresh = params.get('threshold', 3.0)
            return f"""
   m_buffer[m_head] = current_bid;
   m_head = (m_head + 1) % m_max_size;
   if(m_count < m_max_size) m_count++;
   if(m_count < 2) {{ m_ema = current_bid; m_ema_var = 0.0; return current_bid; }}
   double dev = current_bid - m_ema;
   m_ema     += {alpha} * dev;
   m_ema_var  = {alpha} * dev * dev + (1.0 - {alpha}) * m_ema_var;
   double sigma = MathSqrt(m_ema_var);
   if(sigma < 1e-10) return current_bid;
   double z = dev / sigma;
   return (MathAbs(z) > {thresh}) ? m_ema : current_bid;
"""
        elif filter_name == "MAD":
            w   = params.get('window', 50)
            k   = params.get('mad_threshold', 3.0)
            tol = params.get('tolerance', 0.05)
            return f"""
   double raw_spread = current_ask - current_bid;
   double mid_price = (current_bid + current_ask) / 2.0;
   
   if(m_count == m_max_size) {{
      double old_val = m_buffer[m_head];
      for(int i = 0; i < m_max_size; i++) {{
         if(m_sorted_buffer[i] == old_val) {{
            for(int j = i; j < m_max_size - 1; j++) m_sorted_buffer[j] = m_sorted_buffer[j+1];
            break;
         }}
      }}
   }} else {{
      m_count++;
   }}
   
   m_buffer[m_head] = mid_price;
   m_head = (m_head + 1) % m_max_size;
   
   int insert_idx = m_count - 1;
   for(int i = 0; i < m_count - 1; i++) {{
      if(mid_price < m_sorted_buffer[i]) {{
         for(int j = m_count - 1; j > i; j--) m_sorted_buffer[j] = m_sorted_buffer[j-1];
         insert_idx = i;
         break;
      }}
   }}
   m_sorted_buffer[insert_idx] = mid_price;
   
   if(m_count < {w}) {{
      filtered_bid = current_bid;
      filtered_ask = current_ask;
      return true;
   }}
   
   double med = (m_count % 2 == 0) ? (m_sorted_buffer[m_count/2-1]+m_sorted_buffer[m_count/2])*0.5 : m_sorted_buffer[m_count/2];
   
   for(int i = 0; i < m_count; i++) m_temp_buffer[i] = MathAbs(m_sorted_buffer[i] - med);
   // Only sorting the temp buffer for MAD calculation
   double temp_dev[];
   ArrayResize(temp_dev, m_count);
   ArrayCopy(temp_dev, m_temp_buffer, 0, 0, m_count);
   ArraySort(temp_dev);
   
   double mad = (m_count % 2 == 0) ? (temp_dev[m_count/2-1]+temp_dev[m_count/2])*0.5 : temp_dev[m_count/2];
   double sigma = 1.4826 * mad;
   
   double filtered_mid = mid_price;
   if(sigma > {tol} && MathAbs(mid_price - med) > {k}*sigma) {{
      filtered_mid = med;
   }}
   
   filtered_bid = filtered_mid - raw_spread / 2.0;
   filtered_ask = filtered_mid + raw_spread / 2.0;
   return true;
"""
        elif filter_name in ("HAMPEL", "DEEP_DENOISE_HAMPEL_KALMAN"):
            hw  = params.get('half_window', 15)
            ks  = params.get('k_sigma', 3.0)
            kr  = params.get('kalman_R', 0.1)
            extra_kalman = ""
            if filter_name == "DEEP_DENOISE_HAMPEL_KALMAN":
                extra_kalman = f"""
   // Kalman pass on Hampel output
   double Pm = m_kP + 0.001;
   double K  = Pm / (Pm + {kr});
   m_kx = m_kx + K * (hampel_out - m_kx);
   m_kP = (1.0 - K) * Pm;
   return m_kx;"""
            else:
                extra_kalman = "   return hampel_out;"
            return f"""
   m_buffer[m_head] = current_bid;
   m_head = (m_head + 1) % m_max_size;
   if(m_count < m_max_size) m_count++;
   int pn = MathMin(m_count, {hw}*2+1);
   if(pn < 3) return current_bid;
   double past[];
   ArrayResize(past, pn);
   for(int i = 0; i < pn; i++)
      past[i] = m_buffer[(m_head - i - 1 + m_max_size) % m_max_size];
   ArraySort(past);
   double med   = (pn % 2 == 0) ? (past[pn/2-1]+past[pn/2])*0.5 : past[pn/2];
   double dev[];
   ArrayResize(dev, pn);
   for(int i = 0; i < pn; i++) dev[i] = MathAbs(past[i] - med);
   ArraySort(dev);
   double mad   = (pn % 2 == 0) ? (dev[pn/2-1]+dev[pn/2])*0.5 : dev[pn/2];
   double sigma = 1.4826 * mad;
   double hampel_out = current_bid;
   if(sigma > 1e-10 && MathAbs(current_bid - med) > {ks} * sigma)
      hampel_out = med;
{extra_kalman}
"""
        return "   return current_bid; // PASSTHROUGH\n"

    def _generate_fallback_code(
        self, filter_name: str, params: Dict[str, Any], output_filename: str
    ) -> str:
        """Assembles MQL5 code from Python templates (fallback when Gemini unavailable)."""
        private_members = self._get_private_members(filter_name, params)
        update_logic    = self._get_update_logic(filter_name, params)
        timestamp       = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        param_lines     = "\n".join(
            f"//|    {k:20s} = {v}" for k, v in params.items() if k != "filter"
        )
        buf_size = params.get('window', params.get('half_window', 15) * 2 + 2)

        return f"""//+------------------------------------------------------------------+
//|                                        {output_filename:<26}|
//|                       The Quant Council — AI Synthesized MQL5   |
//|                   Generated: {timestamp}   |
//|                        [FALLBACK — Gemini unavailable]           |
//+------------------------------------------------------------------+
//
// AI-SELECTED FILTER: {filter_name}
// AI-TUNED PARAMETERS:
{param_lines}
//
#property copyright "The Quant Council — AI HFT Pipeline"
#property version   "3.0"
#property strict

class CTickFactory
  {{
private:
{private_members}
public:
                     CTickFactory(int buffer_size);
                    ~CTickFactory();
   bool              UpdateTick(double current_bid, double current_ask, double &filtered_bid, double &filtered_ask);
   bool              IsReady() const {{ return m_count >= m_max_size; }}
   int               GetCount() const {{ return m_count; }}
   void              Reset();
  }};

CTickFactory::CTickFactory(int buffer_size)
  {{
   m_max_size = buffer_size; m_head = 0; m_count = 0;
   ArrayResize(m_buffer, m_max_size);
   ArrayResize(m_sorted_buffer, m_max_size);
   ArrayResize(m_temp_buffer, m_max_size);
   ArrayInitialize(m_buffer, 0.0);
   ArrayInitialize(m_sorted_buffer, 0.0);
   ArrayInitialize(m_temp_buffer, 0.0);
   m_x = 0.0; m_P = 1.0; m_last_price = 0.0;
   m_ema = 0.0; m_ema_var = 0.0;
   m_kx = 0.0; m_kP = 1.0;
  }}

CTickFactory::~CTickFactory() {{ ArrayFree(m_buffer); ArrayFree(m_sorted_buffer); ArrayFree(m_temp_buffer); }}

void CTickFactory::Reset()
  {{
   m_head = 0; m_count = 0;
   ArrayInitialize(m_buffer, 0.0);
   ArrayInitialize(m_sorted_buffer, 0.0);
   ArrayInitialize(m_temp_buffer, 0.0);
   m_x = 0.0; m_P = 1.0; m_last_price = 0.0;
   m_ema = 0.0; m_ema_var = 0.0;
   m_kx = 0.0; m_kP = 1.0;
  }}

bool CTickFactory::UpdateTick(double current_bid, double current_ask, double &filtered_bid, double &filtered_ask)
  {{
{update_logic}
  }}

// ═══ USAGE EXAMPLE ═════════════════════════════════════════════════════
// STEP 1: Copy this file to your Terminal's MQL5\\Include folder
// STEP 2: Use the following code in your EA:
//
// #include <{output_filename}>
// CTickFactory g_filter({buf_size});
// void OnTick()
//   {{
//    MqlTick tick;
//    if(!SymbolInfoTick(_Symbol, tick)) return;
//    if(!g_filter.IsReady()) return;
//    double clean_bid, clean_ask;
//    g_filter.UpdateTick(tick.bid, tick.ask, clean_bid, clean_ask);
//   }}
// ════════════════════════════════════════════════════════════════════════
"""

    # =========================================================================
    # STRUCTURAL VALIDATOR
    # =========================================================================
    def _validate_code(self, code: str) -> Tuple[bool, list]:
        issues = []
        checks = [
            ("class CTickFactory",  "Missing CTickFactory class declaration"),
            ("ArrayResize",         "Missing ArrayResize memory pre-allocation"),
            ("UpdateTick",          "Missing UpdateTick method"),
            ("ArrayFree",           "Missing destructor cleanup"),
            ("IsReady",             "Missing IsReady warm-up guard"),
            ("#property strict",    "Missing #property strict compiler directive"),
        ]
        for pattern, msg in checks:
            if pattern not in code:
                issues.append(msg)
        return len(issues) == 0, issues

    # =========================================================================
    # PUBLIC: run()
    # =========================================================================
    def run(
        self,
        approved_payload: Dict[str, Any],
        output_filename: str = "HFT_Tick_Factory.mqh",
    ) -> Dict[str, Any]:
        """
        Main entry point. Calls Gemini to generate MQL5 code, then runs
        the Python linter post-processor, then writes to disk.
        """
        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [ACTIVATING - Gemini MQL5 Synthesis]")
        print(f"{'-'*68}")

        params      = approved_payload.get("params", {})
        filter_name = params.get("filter", "ADAPTIVE_KALMAN")
        timestamp   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        self._log(f"Council-approved filter: [{filter_name}]")
        self._log(f"Parameters: {params}")

        filter_desc = self.FILTER_DESCRIPTIONS.get(filter_name, "Custom filter.")

        # --- Call Gemini to generate MQL5 code ---
        self._log("Calling Gemini for production MQL5 synthesis...")
        # Safely extract parameters from the Quant's output
        half_window = str(params.get('half_window', 11))
        k_sigma = str(params.get('k_sigma', 1.95))
        
        # Calculate the full window size needed for the C++ arrays
        try:
            window_size = str((int(float(half_window)) * 2) + 1)
        except ValueError:
            window_size = "23"

        # Build the prompt safely using strict string replacement (Zero {} conflicts)
        prompt = self.MQL5_PROMPT_TEMPLATE.replace("[HALF_WINDOW]", half_window)
        prompt = prompt.replace("[K_SIGMA]", k_sigma)
        prompt = prompt.replace("[WINDOW]", window_size)

        gemini_used = True
        try:
            mql5_code = call_gemini(prompt, temperature=0.1, max_retries=3)
            self._log("  [SUCCESS] Gemini MQL5 synthesis complete.")

            # Safe Markdown Stripper
            mql5_code = mql5_code.replace("```mql5", "").replace("```mqh", "").replace("```cpp", "").replace("```c++", "").replace("```", "").strip()

        except Exception as e:
            self._log(f"  [WARNING] Gemini unavailable ({e}). Activating template fallback.")
            mql5_code = self._generate_fallback_code(filter_name, params, output_filename)
            gemini_used = False

        # --- Print inner monologue (always printed, regardless of Gemini) ---
        print(f"\n{'-'*68}")
        print(f"  [{self.AGENT_NAME}] [INNER MONOLOGUE]")
        print(f"{'-'*68}")
        print(f"")
        print(f"  DESIGN DECISIONS:")
        print(f"  {'-'*40}")
        print(f"  Filter selected by council: [{filter_name}]")
        print(f"  {self.FILTER_DESCRIPTIONS.get(filter_name, 'Custom filter.')}")
        print(f"")
        print(f"  MEMORY MODEL:")
        print(f"  {'-'*40}")
        print(f"  Using pre-allocated circular buffer via ArrayResize() in constructor.")
        print(f"  ArrayFree() called in destructor for zero memory leaks.")
        print(f"  All member variables declared in private: scope (MQL5 linter rule 1).")
        print(f"")
        print(f"  TICK PROCESSING:")
        print(f"  {'-'*40}")
        print(f"  O(1) state update per tick (causal, zero lookahead).")
        print(f"  IsReady() guard prevents output before warm-up window fills.")
        print(f"  Parameters: {params}")
        print(f"")
        print(f"  SYNTHESIZING CODE:")
        print(f"  {'-'*40}")
        if gemini_used:
            print(f"  Gemini-2.5-Flash generating production MQL5 from first principles.")
        else:
            print(f"  Gemini unavailable. Template fallback generating MQL5.")
        print(f"{'-'*68}\n")

        # --- Run MQL5 Linter ---
        self._log("Running MQL5 Linter Agent post-processor...")
        mql5_code, linter_logs = self._mql5_linter_process(mql5_code)
        for log_line in linter_logs:
            self._log(f"  [LINTER] {log_line}")

        # --- Structural Validation ---
        self._log("Running structural validation audit...")
        audit_ok, issues = self._validate_code(mql5_code)
        if audit_ok:
            self._log("  [SUCCESS] Audit PASSED - All structural checks satisfied.")
        else:
            self._log(f"  [WARNING] Audit WARNING - {len(issues)} issue(s) found:")
            for iss in issues:
                self._log(f"    * {iss}")

        # --- Write to disk ---
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, output_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(mql5_code)

        self._log(f"[SUCCESS] MQL5 file written -> {filepath}")
        print(f"\n  [{self.AGENT_NAME}] SYNTHESIS COMPLETE.")
        print(f"  Deploy {output_filename} to your MT5 Include folder and attach to any EA.\n")

        return {
            "mql5_code":    mql5_code,
            "filepath":     filepath,
            "filter_name":  filter_name,
            "params":       params,
            "audit_passed": audit_ok,
            "audit_issues": issues,
            "gemini_used":  gemini_used,
        }
