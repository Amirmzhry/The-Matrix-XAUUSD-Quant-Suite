import subprocess
import sys
import os

def run_and_log():
    log_file_path = os.path.join("output", "terminal_execution.log")
    os.makedirs("output", exist_ok=True)
    
    # We will run the main test suite
    command = [sys.executable, "run_all_tests.py"]
    
    print(f"🚀 Starting Execution Logger...")
    print(f"📁 Log will be saved to: {log_file_path}\n")
    print("="*60)
    
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log_file.write(line)
            log_file.flush()
            
        process.wait()
        
    print("="*60)
    print(f"✅ Execution Complete. Full log saved to: {log_file_path}")

if __name__ == "__main__":
    run_and_log()
