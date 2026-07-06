import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(ROOT, "backup_matrix_stable")

EXCLUDE_DIRS = {".venv", "backup_matrix_stable", ".git"}
EXCLUDE_EXTENSIONS = {".bi5"}

def run_backup():
    print(f"Starting backup from {ROOT} to {BACKUP_DIR}...")
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    for root, dirs, files in os.walk(ROOT):
        # Filter directories to exclude .venv, backup_matrix_stable, etc.
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # Calculate relative path
        rel_path = os.path.relpath(root, ROOT)
        target_root = BACKUP_DIR if rel_path == "." else os.path.join(BACKUP_DIR, rel_path)
        
        if not os.path.exists(target_root):
            os.makedirs(target_root)
            
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in EXCLUDE_EXTENSIONS:
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            
            # Copy file
            shutil.copy2(src_file, dst_file)
            
    print("Backup completed successfully!")

if __name__ == "__main__":
    run_backup()
