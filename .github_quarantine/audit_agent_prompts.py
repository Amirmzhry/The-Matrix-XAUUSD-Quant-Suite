import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.agent1_data_analyst import DataAnalystAgent
from src.agents.agent2_lead_quant import LeadQuantAgent
from src.agents.agent3_risk_officer import RiskOfficerAgent
from src.agents.agent4_visualizer import VisualizerAgent
from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent

def extract_prompts():
    output_lines = ["# XAUUSD Agent Prompts Audit\n"]
    
    agents = [
        ("Agent 1: Data Analyst", DataAnalystAgent),
        ("Agent 2: Lead Quant", LeadQuantAgent),
        ("Agent 3: Risk Officer", RiskOfficerAgent),
        ("Agent 4: Visualizer", VisualizerAgent),
        ("Agent 5: MQL5 Synthesizer", MQL5SynthesizerAgent),
    ]
    
    for name, cls in agents:
        output_lines.append(f"## {name}\n")
        
        prompts_found = False
        for attr in ['SYSTEM_PROMPT', 'USER_PROMPT_TEMPLATE', 'MQL5_PROMPT_TEMPLATE']:
            if hasattr(cls, attr):
                prompts_found = True
                prompt_text = getattr(cls, attr)
                output_lines.append(f"### {attr}\n")
                output_lines.append("```text\n")
                output_lines.append(str(prompt_text).strip() + "\n")
                output_lines.append("```\n")
                
        if not prompts_found:
            output_lines.append("*No LLM prompts found for this agent.*\n")
            
        output_lines.append("\n---\n")
        
    os.makedirs("output", exist_ok=True)
    with open("output/XAUUSD_Agent_Prompts_Audit.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
        
    print("Prompts extracted to output/XAUUSD_Agent_Prompts_Audit.md")

if __name__ == "__main__":
    extract_prompts()
