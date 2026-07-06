import os
import sys

# Ensure src modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent

def run_fast_test():
    print("🚀 Starting FAST SYNTHETIC MQL5 TEST...")
    
    # 1. Initialize Agent 5 directly
    agent = MQL5SynthesizerAgent()
    
    # 2. Create a mocked, synthetic Council payload
    mock_payload = {
        "filter": "HAMPEL",
        "half_window": 11,
        "k_sigma": 1.95
    }
    
    print(f"Injecting mock parameters: {mock_payload}")
    
    # 3. Run only Agent 5
    result = agent.run(mock_payload)
    file_path = result.get("file_path", "output/HFT_Tick_Factory.mqh")
    
    print("\n" + "="*60)
    print(f"✅ SYNTHESIS COMPLETE. Output File: {file_path}")
    print("="*60)
    
    # 4. Perform an automatic Syntax Sanity Check
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            print("\n--- C++ SYNTAX AUDIT ---")
            
            # Check for double braces hallucination
            if "{{" in content or "}}" in content:
                print("❌ FAILED: Double braces '{{' or '}}' detected!")
            else:
                print("✅ PASSED: No double braces.")
                
            # Check for unreplaced variables
            if "[HALF_WINDOW]" in content or "{half_window}" in content:
                print("❌ FAILED: Unreplaced variable placeholders detected!")
            else:
                print("✅ PASSED: Variables successfully injected.")
                
            print("\n--- FILE PREVIEW (First 25 Lines) ---")
            print('\n'.join(content.split('\n')[:25]))

if __name__ == "__main__":
    run_fast_test()
