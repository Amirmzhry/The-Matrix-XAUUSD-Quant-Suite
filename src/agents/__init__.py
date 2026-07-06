# src/agents/__init__.py
# The Quant Council — Agent Package
from .agent1_data_analyst import DataAnalystAgent
from .agent2_lead_quant import LeadQuantAgent
from .agent3_risk_officer import RiskOfficerAgent
from .agent4_visualizer import VisualizerAgent
from .agent5_mql5_synthesizer import MQL5SynthesizerAgent

__all__ = [
    "DataAnalystAgent",
    "LeadQuantAgent",
    "RiskOfficerAgent",
    "VisualizerAgent",
    "MQL5SynthesizerAgent",
]
