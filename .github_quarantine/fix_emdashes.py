import os

filepath = r"src\agents\agent1_data_analyst.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('—', '-')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced all em-dashes.")
