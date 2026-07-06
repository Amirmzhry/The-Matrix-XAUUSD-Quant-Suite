import os

def fix_ports():
    target_ports = [("localhost:8000", "localhost:8080"), 
                    ("127.0.0.1:8000", "localhost:8080")]
    
    # 1. Scan frontend/src/ folder
    src_dir = os.path.join("frontend", "src")
    if os.path.exists(src_dir):
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith((".ts", ".tsx", ".js", ".jsx", ".css")):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    original_content = content
                    for search_str, replace_str in target_ports:
                        content = content.replace(search_str, replace_str)
                    
                    if content != original_content:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"✅ Updated ports in: {filepath}")

    # 2. Update frontend/vite.config.ts
    vite_config = os.path.join("frontend", "vite.config.ts")
    if os.path.exists(vite_config):
        with open(vite_config, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        for search_str, replace_str in target_ports:
            content = content.replace(search_str, replace_str)
            
        if content != original_content:
            with open(vite_config, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Updated ports in: {vite_config}")

    # 3. Update app_api.py
    api_file = "app_api.py"
    if os.path.exists(api_file):
        with open(api_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        original_content = content
        # Change the default startup port in uvicorn
        content = content.replace("port=8000", "port=8080")
        
        if content != original_content:
            with open(api_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Updated default port in: {api_file}")

if __name__ == "__main__":
    fix_ports()
