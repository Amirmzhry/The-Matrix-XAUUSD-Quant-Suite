# data_loader.py — Full 24-Hour Dukascopy Tick Ingestion with Progress Streaming
import requests
import lzma
import struct
import pandas as pd
from datetime import datetime, timedelta, timezone
import concurrent.futures
import threading

# Thread-safe progress state
_progress_lock = threading.Lock()
_progress_state = {"total": 0, "done": 0, "ticks_so_far": 0, "message": ""}

def get_progress():
    with _progress_lock:
        return dict(_progress_state)

def _update_progress(done, total, ticks, msg):
    with _progress_lock:
        _progress_state["done"] = done
        _progress_state["total"] = total
        _progress_state["ticks_so_far"] = ticks
        _progress_state["message"] = msg

def _fetch_hour(symbol, year, month_0idx, day, hour):
    """Fetch a single hourly .bi5 file from Dukascopy and decode all ticks."""
    url = f"https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{month_0idx:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    headers = {'User-Agent': 'Mozilla/5.0 (Matrix Core Quant Engine)'}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200 or len(resp.content) == 0:
            return []
        data = lzma.decompress(resp.content)
    except Exception:
        return []

    point = 1000.0 if symbol == "XAUUSD" else 100000.0
    tick_size = 20
    base_time = datetime(year, month_0idx + 1, day, hour, tzinfo=timezone.utc)
    ticks = []

    for i in range(0, len(data), tick_size):
        chunk = data[i:i + tick_size]
        if len(chunk) < tick_size:
            break
        time_delta_ms, ask_raw, bid_raw, ask_vol, bid_vol = struct.unpack(">3I2f", chunk)
        ticks.append({
            'DateTime': base_time + timedelta(milliseconds=time_delta_ms),
            'Bid': bid_raw / point,
            'Ask': ask_raw / point,
            'Tick_Volume': round(bid_vol + ask_vol, 2)
        })
    return ticks


def load_real_data(symbol="XAUUSD", start_date="2025-01-06", end_date="2025-01-13"):
    """
    Full 24-hour Dukascopy tick ingestion with multi-threaded download.
    Reports progress via the global _progress_state for SSE streaming.
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    if start > end:
        start, end = end, start

    # Build task list: every hour of every day in range
    tasks = []
    cur = start
    while cur <= end:
        month_0 = cur.month - 1  # Dukascopy months are 0-indexed
        for hour in range(24):
            tasks.append((symbol, cur.year, month_0, cur.day, hour))
        cur += timedelta(days=1)

    total_tasks = len(tasks)
    _update_progress(0, total_tasks, 0, f"Starting download: {total_tasks} hourly files...")
    print(f"\n[DATA LOADER] Fetching {total_tasks} hourly .bi5 files for {symbol} ({start_date} -> {end_date})...")

    all_dfs = []
    completed = 0
    ticks_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_to_key = {}
        for t in tasks:
            f = executor.submit(_fetch_hour, *t)
            future_to_key[f] = t

        for future in concurrent.futures.as_completed(future_to_key):
            result = future.result()
            if result:
                chunk_df = pd.DataFrame(result)
                all_dfs.append(chunk_df)
                ticks_count += len(chunk_df)
            completed += 1
            key = future_to_key[future]
            day_str = f"{key[2]+1:02d}/{key[3]:02d}"
            _update_progress(
                completed, total_tasks, ticks_count,
                f"Downloaded {completed}/{total_tasks} — Day {day_str} Hour {key[4]:02d} — {ticks_count:,} ticks so far"
            )

    if all_dfs:
        df = pd.concat(all_dfs, ignore_index=True)
    else:
        df = pd.DataFrame(columns=['DateTime', 'Bid', 'Ask', 'Tick_Volume'])

    if not df.empty:
        df.sort_values('DateTime', inplace=True)
        df.reset_index(drop=True, inplace=True)
        _update_progress(total_tasks, total_tasks, len(df), f"Complete: {len(df):,} ticks decoded.")
        print(f"[DATA LOADER] Successfully decoded {len(df):,} ticks across the requested period.")
    else:
        _update_progress(total_tasks, total_tasks, 0, "Warning: No data found for the requested period.")
        print("[DATA LOADER] Warning: No data found.")

    return df
