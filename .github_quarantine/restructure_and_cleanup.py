import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

def move_file(src_rel, dst_rel):
    src = os.path.join(ROOT, src_rel)
    dst = os.path.join(ROOT, dst_rel)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        print(f"Moved: {src_rel} -> {dst_rel}")

def delete_path(path_rel):
    path = os.path.join(ROOT, path_rel)
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Deleted directory: {path_rel}")
        else:
            os.remove(path)
            print(f"Deleted file: {path_rel}")

def run_restructure():
    print("=== STARTING CODEBASE RESTRUCTURE & CLEANUP ===")
    
    # 1. Create target directories
    os.makedirs(os.path.join(ROOT, "src", "core"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "src", "agents"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "quarantine_tests"), exist_ok=True)

    # 2. Move core files
    move_file("data_loader.py", "src/core/data_loader.py")
    move_file("tick_factory_engine.py", "src/core/tick_factory_engine.py")

    # 3. Delete duplicates and legacy folders
    delete_path("master_pipeline.py")  # Delete root duplicate
    delete_path("agents")              # Delete root agents folder

    # 4. Quarantine temporary audit and test files
    temp_files = [
        "test_api.py",
        "test_dukascopy_api.py",
        "test_mql5_synthesis.py",
        "audit_all_agents.py",
        "final_isolated_test.py",
        "check_key.py",
        "advanced_api_stress_test.py",
        "architectural_review.py",
        "restructure_workspace.py",
        "cleanup.py",
        "simple_echo.py"
    ]
    for file in temp_files:
        move_file(file, f"quarantine_tests/{file}")

    print("=== CODEBASE RESTRUCTURE & CLEANUP COMPLETE ===")

if __name__ == "__main__":
    run_restructure()
