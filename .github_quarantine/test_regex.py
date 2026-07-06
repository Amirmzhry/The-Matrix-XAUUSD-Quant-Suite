import re
import json

with open("output/HFT_Execution_Report.md", "r", encoding="utf-8") as f:
    content = f.read()

metrics = {}
metrics["q_score"] = re.search(r"Q_Score.*?([\d\.]+)", content).group(1)
metrics["kurtosis"] = re.search(r"kurtosis.*?([\d\.]+)", content, re.IGNORECASE).group(1)
metrics["regime"] = re.search(r"Regime.*?([A-Z_]+)", content).group(1)

with open("output/test_regex.json", "w") as f:
    json.dump(metrics, f)
