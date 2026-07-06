import os
import shutil
import re

ROOT = r"d:\The Matrix"

DIRS = [
    r"src\core",
    r"src\agents",
    r"data\raw",
    r"data\processed",
    r"export\mql5",
    r"export\reports"
]

for d in DIRS:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)

# 1. Update Imports
def update_file(path, replacements):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

agent_files = [
    "agents/agent1_data_analyst.py",
    "agents/agent2_lead_quant.py",
    "agents/agent3_risk_officer.py",
    "agents/agent4_visualizer.py",
    "agents/agent5_mql5_synthesizer.py",
]

for agent in agent_files:
    agent_path = os.path.join(ROOT, agent)
    update_file(agent_path, [
        ("from tools import", "from src.core.tools import"),
        ("from llm_client import", "from src.core.llm_client import"),
        ("sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))", "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))")
    ])

master_path = os.path.join(ROOT, "master_pipeline.py")
update_file(master_path, [
    ("from agents.", "from src.agents."),
    ("import argparse", "import sys\nimport os\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))\nimport argparse")
])

# 2. Move Files
def move_file(src, dst):
    s = os.path.join(ROOT, src)
    d = os.path.join(ROOT, dst)
    if os.path.exists(s):
        shutil.move(s, d)

move_file("master_pipeline.py", r"src\core\master_pipeline.py")
move_file("tools.py", r"src\core\tools.py")
move_file("llm_client.py", r"src\core\llm_client.py")

for agent in agent_files:
    move_file(agent, agent.replace("agents/", r"src\agents\\"))

# Output parsing
if os.path.exists(os.path.join(ROOT, "output")):
    for f in os.listdir(os.path.join(ROOT, "output")):
        src = os.path.join(ROOT, "output", f)
        if f.endswith(".mqh"):
            shutil.move(src, os.path.join(ROOT, r"export\mql5", f))
        elif f.endswith(".html") or f.endswith(".md") or f.endswith(".csv"):
            shutil.move(src, os.path.join(ROOT, r"export\reports", f))

print("Workspace Restructuring Complete. Zero ModuleNotFoundError expected.")
