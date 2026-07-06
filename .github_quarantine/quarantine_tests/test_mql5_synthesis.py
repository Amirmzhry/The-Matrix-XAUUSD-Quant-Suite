import os
import sys

# Purge ADC
for _v in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
           "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    os.environ.pop(_v, None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

from src.agents.agent5_mql5_synthesizer import MQL5SynthesizerAgent

if __name__ == "__main__":
    agent = MQL5SynthesizerAgent(output_dir="output", verbose=True)
    
    # Approved payload from the 1-week stress test
    approved_payload = {
        "params": {
            "filter": "MAD",
            "window": 50,
            "mad_threshold": 1.0,
            "tolerance": 0.02
        }
    }
    
    print("\nRunning MQL5 Synthesis with updated prompt skeleton...")
    result = agent.run(approved_payload, output_filename="HFT_Tick_Factory.mqh")
    
    filepath = result["filepath"]
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"\nFile generated: {filepath}")
        print(f"File size: {size} bytes")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if "bool UpdateTick" in content:
                print("✅ Found 'bool UpdateTick' in the generated file!")
            else:
                print("❌ 'bool UpdateTick' is MISSING in the generated file!")
    else:
        print("❌ File was not generated!")
