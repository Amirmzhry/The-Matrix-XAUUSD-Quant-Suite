import os
import shutil

# Files to delete
LEGACY_FILES = [
    "matrix_agent.py",
    "matrix_orchestrator.py",
    "matrix_orchestrator_v2.py",
    "matrix_quant_agent.py",
    "master_pipeline_orchestrator.py",
    "mql5_synthesizer.py",
    "mcp_data_server.py",
    "volume_filter_tool.py",
    "data_toxicity_profiler.py",
    "main.py",
    "dashboard.py",
    "debug_runner.py",
    "test_api.py",
    "test_filters.py",
    "test_terminal.py",
    "test_volume_filter.py",
    "tester.py",
    "run_debug_wrapper.py",
    "ping.py",
    "test.bat"
]

AUTO_GENERATED_OUTPUTS = [
    "HFT_Distribution.png",
    "HFT_Execution_Report.md",
    "HFT_Tick_Factory.mqh",
    "MatrixTickFactory.mqh",
    "Kaggle_Submission.md",
    "chart1_price_overlay.html",
    "chart2_density_skewness.html",
    "chart3_agent_timeline.html",
    "cleaned_tick_sample.csv",
    "dummy_market_data.csv",
    "extreme_market_data.csv",
    "orchestrator_market_data.csv",
    "full_cleaned_ticks.csv",
    "error_traceback.log"
]

def main():
    print("=== STARTING WORKSPACE CLEANUP ===")
    
    # 1. Delete legacy files
    for file in LEGACY_FILES:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Deleted legacy file: {file}")
            except Exception as e:
                print(f"Error deleting legacy file {file}: {e}")
                
    # 2. Delete auto-generated outputs
    for file in AUTO_GENERATED_OUTPUTS:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Deleted auto-generated output: {file}")
            except Exception as e:
                print(f"Error deleting output {file}: {e}")

    # Delete legacy web directory
    if os.path.exists("web"):
        try:
            shutil.rmtree("web")
            print("Deleted legacy directory: web")
        except Exception as e:
            print(f"Error deleting web directory: {e}")

    # 3. Create output directory
    os.makedirs("output", exist_ok=True)
    print("Created directory: output")
    
    # 4. Delete __pycache__ directories
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                print(f"Deleted cache directory: {pycache_path}")
            except Exception as e:
                print(f"Error deleting cache directory {pycache_path}: {e}")

    print("=== WORKSPACE CLEANUP COMPLETE ===")

if __name__ == "__main__":
    main()
