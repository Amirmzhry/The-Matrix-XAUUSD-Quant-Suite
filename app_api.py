import os
import sys
import subprocess
import re
import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse

app = FastAPI(title="The Matrix: XAUUSD Quant Suite API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the Vite host (e.g. ["http://localhost:5173"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": str(datetime.date.today())}

@app.get("/api/run")
def run_pipeline(start: str = "2025-01-06", end: str = "2025-01-07", mock: bool = False):
    """
    Spawns the master pipeline and streams execution logs to the frontend via SSE.
    """
    def log_generator():
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        cmd = [sys.executable, "-u", "src/core/master_pipeline.py", "--start", start, "--end", end]
        if mock:
            cmd.extend(["--mode", "synthetic"])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            # Stream output line-by-line
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    yield f"data: {line}\n\n"
                    
            # Read any leftover lines
            for line in process.stdout:
                yield f"data: {line}\n\n"
                
            process.wait()
            yield "data: [FINISHED] Pipeline run complete.\n\n"
        except Exception as e:
            yield f"data: ⚠️ Execution Error: {str(e)}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/metrics")
def get_metrics():
    """
    Parses and returns metrics from output/HFT_Execution_Report.md
    """
    report_path = os.path.join(OUTPUT_DIR, "HFT_Execution_Report.md")
    if not os.path.exists(report_path):
        return {
            "q_score": "0.0",
            "kurtosis": "0.0",
            "regime": "OFFLINE",
            "error": "No execution report found. Run pipeline first."
        }
        
    metrics = {
        "q_score": "0.0",
        "kurtosis": "0.0",
        "regime": "OFFLINE"
    }
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        q_match = re.search(r"Q_Score.*?([\d\.]+)", content)
        if q_match:
            metrics["q_score"] = q_match.group(1)
            
        k_match = re.search(r"kurtosis.*?([\d\.]+)", content, re.IGNORECASE)
        if k_match:
            metrics["kurtosis"] = k_match.group(1)
            
        r_match = re.search(r"Regime.*?([A-Z_]+)", content)
        if r_match:
            metrics["regime"] = r_match.group(1)
    except Exception as e:
        metrics["error"] = f"Failed to parse report: {str(e)}"
        
    return metrics

@app.get("/api/charts/{chart_name}")
def get_chart(chart_name: str):
    """
    Serves generated Plotly charts (e.g. chart1_price_overlay.html)
    """
    chart_path = os.path.join(OUTPUT_DIR, chart_name)
    if not os.path.exists(chart_path):
        raise HTTPException(status_code=404, detail="Chart not found")
    return FileResponse(chart_path)

@app.get("/api/download/{file_type}")
def download_artifact(file_type: str):
    """
    Downloads compiled artifacts (mqh or report)
    """
    if file_type == "mqh":
        filepath = os.path.join(OUTPUT_DIR, "HFT_Tick_Factory.mqh")
        filename = "HFT_Tick_Factory.mqh"
        media_type = "text/plain"
    elif file_type == "report":
        filepath = os.path.join(OUTPUT_DIR, "HFT_Execution_Report.md")
        filename = "HFT_Execution_Report.md"
        media_type = "text/markdown"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(filepath, media_type=media_type, filename=filename)

@app.get("/api/ticks")
def get_ticks(limit: int = 100):
    """
    Reads output/cleaned_ticks.csv and returns the last `limit` ticks as JSON.
    """
    csv_path = os.path.join(OUTPUT_DIR, "cleaned_ticks.csv")
    if not os.path.exists(csv_path):
        return []
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return []
        
        # Ensure Spread and ROC are present
        if 'Spread' not in df.columns and 'Bid' in df.columns and 'Ask' in df.columns:
            df['Spread'] = (df['Ask'] - df['Bid']).round(2)
        # Calculate 14-period Rate of Change (ROC) Percentage from actual tick data
        if 'ROC' not in df.columns and 'Bid' in df.columns:
            df['ROC'] = (df['Bid'].diff(14) / df['Bid'].shift(14)) * 100
            df['ROC'] = df['ROC'].fillna(0).round(4)
        sub_df = df.tail(limit).copy()
        ticks_list = []
        for idx, row in sub_df.iterrows():
            time_val = str(row.get('DateTime', '')).split(' ')[-1] if 'DateTime' in row else ''
            if not time_val and 'time' in row:
                time_val = str(row['time'])
            
            roc = float(row.get('ROC', 0.0))
            verdict = 'Veto' if abs(roc) > 0.02 else 'Pass'
            
            ticks_list.append({
                "id": idx,
                "time": time_val,
                "bid": float(row.get('Bid', 0.0)),
                "ask": float(row.get('Ask', 0.0)),
                "raw_bid": float(row.get('Raw_Bid', row.get('Bid', 0.0))),
                "raw_ask": float(row.get('Raw_Ask', row.get('Ask', 0.0))),
                "spread": float(row.get('Spread', 0.0)),
                "roc": roc,
                "qScore": float(row.get('Q_Score', 0.01 + abs(roc) * 5)),
                "verdict": verdict
            })
        return ticks_list
    except Exception as e:
        print(f"Error loading ticks: {str(e)}")
        return []

# ==========================================
# React Frontend Serving (Cloud Run)
# ==========================================
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    from fastapi.staticfiles import StaticFiles
    
    # Mount assets folder for JS/CSS
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API Route Not Found")
            
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
            
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
            
        raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    import os
    import uvicorn
    
    # Dynamically bind to the port provided by Google Cloud, default to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_api:app", host="0.0.0.0", port=port)
