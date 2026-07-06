import streamlit as st
import subprocess
import os
import sys
import re
import datetime
import time
import streamlit.components.v1 as components

# ==============================================================================
# CONFIGURATION & THEME
# ==============================================================================
st.set_page_config(
    page_title="The Matrix: XAUUSD Quant Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Advanced Global CSS Injection
st.markdown("""
<style>
    /* Hide Streamlit Watermarks */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Core Canvas Base Background */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Card Surfaces & Glassmorphism */
    .glass-container {
        background: rgba(22, 27, 34, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(212, 175, 55, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }

    /* Typography & Text Scaling */
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-weight: 700;
        margin-top: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #B0B5C0;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom: 2px solid #D4AF37 !important;
    }

    /* Monospace for Data & Numbers */
    .mono-text {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    }
    
    .num-align-right {
        text-align: right !important;
    }

    .metric-title {
        font-size: 18px;
        color: #B0B5C0;
        margin-bottom: 8px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 38px;
        font-weight: bold;
        color: #D4AF37;
        line-height: 1.2;
    }
    
    /* Pulsing Alert Shadow */
    .metric-alert {
        border: 1px solid #E74C3C !important;
        box-shadow: 0 0 20px rgba(231, 76, 60, 0.4) !important;
        animation: pulse-red 1.5s infinite;
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 10px rgba(231, 76, 60, 0.2); }
        50% { box-shadow: 0 0 30px rgba(231, 76, 60, 0.8); }
        100% { box-shadow: 0 0 10px rgba(231, 76, 60, 0.2); }
    }

    .regime-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 6px;
        border: 1px solid #D4AF37;
        background: rgba(212, 175, 55, 0.1);
        color: #D4AF37;
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-weight: bold;
    }

    /* Terminal Console */
    .terminal-canvas {
        background-color: #020408;
        padding: 24px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        height: 600px;
        overflow-y: auto;
        box-shadow: inset 0 0 20px rgba(0,0,0,1);
        border: 1px solid rgba(255,255,255,0.05);
    }
    .term-line {
        font-size: 14px;
        line-height: 1.6;
        margin: 0;
        white-space: pre-wrap;
    }
    .term-white { color: #FFFFFF; }
    .term-green { color: #2ECC71; font-weight: bold; }
    .term-red { color: #E74C3C; font-weight: bold; }
    .term-dim { color: #555860; }

    /* Code Block Styling */
    .stCode {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }

    /* Buttons & Interactive Components */
    .primary-btn button {
        background: linear-gradient(135deg, #D4AF37 0%, #AA7C11 100%) !important;
        color: #070A0F !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        width: 100%;
        font-size: 16px !important;
    }
    .primary-btn button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4) !important;
    }
    
    .secondary-btn button {
        background: transparent !important;
        border: 2px solid #2ECC71 !important;
        color: #2ECC71 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        width: 100%;
        transition: all 0.3s ease !important;
    }
    .secondary-btn button:hover {
        background: rgba(46, 204, 113, 0.1) !important;
        box-shadow: 0 0 15px rgba(46, 204, 113, 0.3) !important;
    }

    /* Architect Profile */
    .arch-name { font-size: 28px; font-weight: bold; color: #D4AF37; margin-bottom: 5px; }
    .arch-title { font-size: 16px; font-style: italic; color: #C0C0C0; margin-bottom: 15px; margin-top: 0; }
    .arch-bio { font-size: 15px; line-height: 1.6; color: #E2E8F0; margin-bottom: 25px; }
    .arch-links a {
        display: inline-block;
        margin-right: 15px;
        padding: 8px 16px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 6px;
        color: #D4AF37;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.2s;
    }
    .arch-links a:hover {
        background: rgba(212, 175, 55, 0.1);
        border-color: #D4AF37;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def parse_execution_report(report_path="output/HFT_Execution_Report.md"):
    metrics = {
        "Q-Score": "0.0",
        "Kurtosis": "0.0",
        "Regime": "OFFLINE"
    }
    if not os.path.exists(report_path):
        return metrics
        
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        q_match = re.search(r"Q_Score.*?([\d\.]+)", content)
        if q_match: metrics["Q-Score"] = q_match.group(1)
            
        k_match = re.search(r"kurtosis.*?([\d\.]+)", content, re.IGNORECASE)
        if k_match: metrics["Kurtosis"] = k_match.group(1)
            
        r_match = re.search(r"Regime:?\s*\**\[?([A-Z_]+)\]?\**", content)
        if r_match: metrics["Regime"] = r_match.group(1)
    except Exception:
        pass
        
    return metrics

def read_file_content(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return None

# ==============================================================================
# MAIN TABS & ROUTING
# ==============================================================================
st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>THE MATRIX: XAUUSD QUANT SUITE</h1>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎮 Command Center", 
    "🧠 Agent Debate Console", 
    "📊 Microstructure Analytics", 
    "📥 Production Export Hub", 
    "🏢 Executive System Profile"
])

# Initialize session state logs
if 'logs_html' not in st.session_state:
    st.session_state.logs_html = ""
if 'pipeline_running' not in st.session_state:
    st.session_state.pipeline_running = False

# ==============================================================================
# TAB 1: COMMAND CENTER
# ==============================================================================
with tab1:
    col_ctrl, col_hud = st.columns([1, 2.5])
    
    with col_ctrl:
        st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
        st.markdown("### Parameters Array")
        start_date = st.date_input("Start Date", value=datetime.date(2025, 1, 6))
        end_date = st.date_input("End Date", value=datetime.date(2025, 1, 7))
        
        st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
        initiate_btn = st.button("⚡ INITIATE QUANT CORE")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_hud:
        st.markdown("<div class='glass-container' style='height: 100%;'>", unsafe_allow_html=True)
        st.markdown("### LIVE PROGRESS TRACKING")
        progress_ph = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("### SYSTEM HUD")
    hud_ph = st.empty()

# ==============================================================================
# TAB 2: AGENT DEBATE CONSOLE
# ==============================================================================
with tab2:
    terminal_ph = st.empty()

# ==============================================================================
# PIPELINE EXECUTION / STREAMING LOGIC
# ==============================================================================
if initiate_btn and not st.session_state.pipeline_running:
    st.session_state.pipeline_running = True
    st.session_state.logs_html = ""
    
    progress_ph.markdown("<h4>Initializing Sterile Subprocess Environment... 🟢</h4>", unsafe_allow_html=True)
    terminal_ph.markdown('<div class="terminal-canvas"><div class="term-line term-dim">Quant Core Initializing...</div></div>', unsafe_allow_html=True)
    
    # 1. Create a clean, sterile environment dictionary copy
    env = os.environ.copy()
    # Force Python not to buffer stdout, ensuring real-time line flushing
    env["PYTHONUNBUFFERED"] = "1"
    
    # 2. Spawn the backend script master_pipeline.py completely independently of Streamlit's presentation threads
    process = subprocess.Popen(
        [sys.executable, "-u", "src/core/master_pipeline.py", "--start", str(start_date), "--end", str(end_date)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    log_buffer = ""
    # Safe while loop to pull strings line-by-line via process.stdout.readline()
    while process.poll() is None:
        line = process.stdout.readline()
        if not line:
            continue
            
        # Color mapping rules
        css_class = "term-dim"
        if "[DataAnalystAgent]" in line or "[LeadQuantAgent]" in line:
            css_class = "term-white"
        elif "[RiskOfficerAgent]" in line and "APPROVED" in line:
            css_class = "term-green"
        elif any(x in line for x in ["⚠️", "VETOED", "REJECTED"]):
            css_class = "term-red"
            
        escaped_line = line.strip().replace("<", "&lt;").replace(">", "&gt;")
        log_buffer += f'<div class="term-line {css_class}">{escaped_line}</div>'
        
        # Update the single st.empty() window placeholder dynamically without raw st.write()
        terminal_ph.markdown(f'<div class="terminal-canvas">{log_buffer}</div>', unsafe_allow_html=True)
        
        # Microstructure Phase Updates mapping to Tab 1
        if "[DATA LOADER]" in line:
            progress_ph.markdown("<h4>Phase 1: Ingesting Microstructure Ticks 🟢</h4>", unsafe_allow_html=True)
        elif "DataAnalystAgent" in line:
            progress_ph.markdown("<h4>Phase 2: Data Analyst Scanning Noise 🟢</h4>", unsafe_allow_html=True)
        elif "LeadQuantAgent" in line:
            progress_ph.markdown("<h4>Phase 3: Lead Quant Calculating Thresholds 🟢</h4>", unsafe_allow_html=True)
        elif "RiskOfficerAgent" in line:
            progress_ph.markdown("<h4>Phase 4: Risk Officer Evaluating Toxicity 🟡</h4>", unsafe_allow_html=True)
        elif "MQL5SynthesizerAgent" in line:
            progress_ph.markdown("<h4>Phase 5: Synthesizing MQL5 Production Code 🟢</h4>", unsafe_allow_html=True)
            
    # Process remaining lines after poll terminates
    for line in process.stdout:
        css_class = "term-dim"
        if "[DataAnalystAgent]" in line or "[LeadQuantAgent]" in line:
            css_class = "term-white"
        elif "[RiskOfficerAgent]" in line and "APPROVED" in line:
            css_class = "term-green"
        elif any(x in line for x in ["⚠️", "VETOED", "REJECTED"]):
            css_class = "term-red"
            
        escaped_line = line.strip().replace("<", "&lt;").replace(">", "&gt;")
        log_buffer += f'<div class="term-line {css_class}">{escaped_line}</div>'
        terminal_ph.markdown(f'<div class="terminal-canvas">{log_buffer}</div>', unsafe_allow_html=True)

    process.wait()
    st.session_state.logs_html = log_buffer
    st.session_state.pipeline_running = False
    progress_ph.markdown("<h4>Pipeline Execution Complete 🏁</h4>", unsafe_allow_html=True)

# Post-run render terminal state
if not st.session_state.pipeline_running:
    if st.session_state.logs_html:
        terminal_ph.markdown(f'<div class="terminal-canvas">{st.session_state.logs_html}</div>', unsafe_allow_html=True)
    else:
        terminal_ph.markdown('<div class="terminal-canvas"><div class="term-line term-dim">Quant Core Offline. Select parameters and initiate execution.</div></div>', unsafe_allow_html=True)

# Post-run render HUD Metrics
if not st.session_state.pipeline_running:
    metrics = parse_execution_report()
    k_val = 0.0
    try:
        k_val = float(metrics["Kurtosis"])
    except ValueError:
        pass
        
    k_class = "glass-container metric-alert" if k_val > 3.0 else "glass-container"
    regime = metrics["Regime"]
    
    if os.path.exists("output/HFT_Execution_Report.md"):
        hud_ph.markdown(f"""
        <div style="display:flex; gap:24px; width:100%;">
            <div class="glass-container" style="flex:1;">
                <div class="metric-title">Toxicity Index (Q-Score)</div>
                <div class="metric-value">{metrics['Q-Score']}</div>
            </div>
            <div class="{k_class}" style="flex:1;">
                <div class="metric-title">Fat-Tail Stress (Return Kurtosis)</div>
                <div class="metric-value">{metrics['Kurtosis']}</div>
            </div>
            <div class="glass-container" style="flex:1;">
                <div class="metric-title">Locked Volatility Regime</div>
                <div style="margin-top:10px;"><span class="regime-badge">{regime}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        hud_ph.markdown('<div class="glass-container"><div class="metric-title" style="text-align:center;">Quant Core Offline. Select parameters and initiate execution.</div></div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 3: MICROSTRUCTURE ANALYTICS
# ==============================================================================
with tab3:
    if not os.path.exists("output/chart1_price_overlay.html"):
        st.markdown('<div class="glass-container">Quant Core Offline. Select parameters and initiate execution.</div>', unsafe_allow_html=True)
    else:
        sub1, sub2, sub3 = st.tabs(["📈 Price Overlay", "📊 Return Distributions", "⏱️ Agent Timeline"])
        
        with sub1:
            st.markdown('<div class="glass-container" style="padding:0; overflow:hidden;">', unsafe_allow_html=True)
            html1 = read_file_content("output/chart1_price_overlay.html")
            if html1: components.html(html1, height=650, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with sub2:
            st.markdown('<div class="glass-container" style="padding:0; overflow:hidden;">', unsafe_allow_html=True)
            html2 = read_file_content("output/chart2_density_skewness.html")
            if html2: components.html(html2, height=650, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with sub3:
            st.markdown('<div class="glass-container" style="padding:0; overflow:hidden;">', unsafe_allow_html=True)
            html3 = read_file_content("output/chart3_agent_timeline.html")
            if html3: components.html(html3, height=650, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 4: PRODUCTION EXPORT HUB
# ==============================================================================
with tab4:
    if not os.path.exists("output/HFT_Tick_Factory.mqh"):
        st.markdown('<div class="glass-container">Quant Core Offline. Select parameters and initiate execution.</div>', unsafe_allow_html=True)
    else:
        col_code, col_report = st.columns(2)
        
        with col_code:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("### 🔧 Production MQL5 Source")
            mqh_path = "output/HFT_Tick_Factory.mqh"
            mqh_content = read_file_content(mqh_path)
            if mqh_content:
                st.code(mqh_content, language='cpp')
                st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
                st.download_button("📥 Download Expert Advisor Engine (.MQH)", data=mqh_content, file_name="HFT_Tick_Factory.mqh", mime="text/plain", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_report:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("### 📋 HFT Compliance Digest")
            md_path = "output/HFT_Execution_Report.md"
            md_content = read_file_content(md_path)
            if md_content:
                st.markdown(md_content)
                st.markdown("<div class='secondary-btn'>", unsafe_allow_html=True)
                st.download_button("📄 Export Audit Report (.MD)", data=md_content, file_name="HFT_Execution_Report.md", mime="text/markdown", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 5: EXECUTIVE SYSTEM PROFILE
# ==============================================================================
with tab5:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    col_logo, col_cred = st.columns([1, 2])
    
    with col_logo:
        st.markdown("""
        <div style="background: rgba(0,0,0,0.6); width: 250px; height: 250px; border-radius: 12px; border: 2px solid #D4AF37; box-shadow: 0 0 30px rgba(212,175,55,0.2); display: flex; align-items: center; justify-content: center; margin: auto;">
            <div style="text-align: center;">
                <h1 style="font-size: 5rem; margin:0; text-shadow: 0 0 15px #D4AF37;">⚡</h1>
                <h4 style="color: #D4AF37; letter-spacing: 2px; margin-top: 10px; font-family: 'JetBrains Mono', 'Fira Code', monospace !important;">MATRIX CORE</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_cred:
        st.markdown("""
        <div class="arch-name">Amir Mazaheri</div>
        <div class="arch-title">Lead Quant Architect & Senior Network Engineer</div>
        
        <div class="arch-bio">
        Architecting zero-latency multi-agent cognitive frameworks, real-tick filtration algorithms, and institutional network microstructures for commodity derivative execution.
        </div>
        
        <div class="arch-links">
            <a href="#">📧 Email Desk</a>
            <a href="#">💻 GitHub Source</a>
            <a href="#">🤝 LinkedIn Network</a>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
