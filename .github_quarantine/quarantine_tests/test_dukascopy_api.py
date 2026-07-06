# =============================================================================
# test_dukascopy_api.py — Live Dukascopy XAUUSD Tick Data Integration Test
# The Quant Council
# =============================================================================
# Tests live download of 1 hour of real XAUUSD tick data from Dukascopy.
# Validates data shape, column types, spread integrity, and tick frequency.
#
# EXIT CODES:
#   0 = PASS — data is valid, pipeline can use REAL_DUKASCOPY mode
#   1 = FAIL — network error or empty data; pipeline falls back to SYNTHETIC
# =============================================================================

import os
import sys
import time
import requests
import lzma
import struct
import pandas as pd
from datetime import datetime, timedelta, timezone

# ─── CRITICAL: Purge ADC / OAuth2 credentials ──────────────────────────────
for _v in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
           "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    os.environ.pop(_v, None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "  [PASS]"
FAIL = "  [FAIL]"
results = []

def check(label, fn):
    t0 = time.time()
    try:
        r = fn()
        ms = (time.time() - t0) * 1000
        results.append((True, label))
        print(f"{PASS}  {label}  ({ms:.0f}ms)")
        return r
    except Exception as e:
        ms = (time.time() - t0) * 1000
        results.append((False, f"{label} — {e}"))
        print(f"{FAIL}  {label}")
        print(f"          Error: {e}")
        return None


print("\n" + "=" * 65)
print("  DUKASCOPY LIVE DATA INTEGRATION TEST")
print("  Symbol: XAUUSD (Gold)  |  Window: 1 hour")
print("=" * 65 + "\n")

# ─── Configuration ───────────────────────────────────────────────────────────
# Use the most recent full trading hour (UTC) to guarantee data exists.
# Dukascopy data is usually available with a ~2 hour lag.
TARGET_DATE = datetime(2025, 1, 6, 10, tzinfo=timezone.utc)   # Known good session
SYMBOL      = "XAUUSD"
POINT       = 1000.0   # XAUUSD price divisor in Dukascopy .bi5 encoding


# ─── TEST 1: Network connectivity to Dukascopy CDN ───────────────────────────
def _t1():
    url = "https://datafeed.dukascopy.com/"
    r = requests.get(url, timeout=10)
    assert r.status_code in (200, 301, 302, 403), \
        f"Unexpected status {r.status_code} — CDN may be down"

check("Network: Dukascopy CDN reachable", _t1)


# ─── TEST 2: Download 1 raw .bi5 hour file ───────────────────────────────────
raw_ticks = []

def _t2():
    global raw_ticks
    year   = TARGET_DATE.year
    month0 = TARGET_DATE.month - 1      # 0-indexed as Dukascopy requires
    day    = TARGET_DATE.day
    hour   = TARGET_DATE.hour

    url = (f"https://datafeed.dukascopy.com/datafeed/{SYMBOL}/"
           f"{year}/{month0:02d}/{day:02d}/{hour:02d}h_ticks.bi5")

    print(f"\n          URL: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (The Matrix HFT System; Institutional)'}
    resp = requests.get(url, headers=headers, timeout=20)

    assert resp.status_code == 200, \
        f"HTTP {resp.status_code} — file missing or network blocked"
    assert len(resp.content) > 0, "Response body is empty"

    # Decompress LZMA
    raw_bytes = lzma.decompress(resp.content)
    tick_size = 20   # Each tick = 3 uint32 + 2 float = 20 bytes

    base_time = datetime(year, month0 + 1, day, hour, tzinfo=timezone.utc)
    for i in range(0, len(raw_bytes), tick_size):
        chunk = raw_bytes[i:i + tick_size]
        if len(chunk) < tick_size:
            break
        td_ms, ask_raw, bid_raw, ask_vol, bid_vol = struct.unpack(">3I2f", chunk)
        raw_ticks.append({
            'DateTime':    base_time + timedelta(milliseconds=td_ms),
            'Bid':         bid_raw / POINT,
            'Ask':         ask_raw / POINT,
            'Tick_Volume': round(bid_vol + ask_vol, 2),
        })

    assert len(raw_ticks) > 0, "LZMA decompressed but no ticks decoded"
    print(f"\n          Decoded {len(raw_ticks):,} raw ticks")

check("Download: 1-hour .bi5 XAUUSD file (LZMA decode)", _t2)


# ─── TEST 3: DataFrame validation ────────────────────────────────────────────
df = None

def _t3():
    global df
    assert raw_ticks, "No raw ticks to build DataFrame from"
    df = pd.DataFrame(raw_ticks).sort_values("DateTime").reset_index(drop=True)

    required_cols = {"DateTime", "Bid", "Ask", "Tick_Volume"}
    assert required_cols.issubset(df.columns), f"Missing columns: {required_cols - set(df.columns)}"
    assert len(df) >= 10, f"Too few ticks: {len(df)}"
    assert df["Bid"].dtype in (float, "float64"), f"Bid dtype wrong: {df['Bid'].dtype}"
    assert df["Ask"].dtype in (float, "float64"), f"Ask dtype wrong: {df['Ask'].dtype}"

    print(f"\n          Shape: {df.shape}")
    print(f"          Time range: {df['DateTime'].min()} → {df['DateTime'].max()}")
    print(f"          Bid range:  {df['Bid'].min():.3f} → {df['Bid'].max():.3f}")
    print(f"          Ask range:  {df['Ask'].min():.3f} → {df['Ask'].max():.3f}")

check("Validate: DataFrame shape, columns, dtypes", _t3)


# ─── TEST 4: Spread integrity (no negative spreads) ───────────────────────────
def _t4():
    assert df is not None, "No DataFrame"
    spreads = df["Ask"] - df["Bid"]
    neg = (spreads < 0).sum()
    assert neg == 0, f"{neg} negative spreads detected — data corruption"
    avg_spread = spreads.mean()
    max_spread = spreads.max()
    print(f"\n          Avg spread: {avg_spread:.5f}  |  Max spread: {max_spread:.5f}")
    print(f"          Negative spreads: {neg}  ✅")

check("Integrity: Zero negative spreads", _t4)


# ─── TEST 5: Tick frequency validation (institutional HFT quality) ────────────
def _t5():
    assert df is not None, "No DataFrame"
    dt_diff = df["DateTime"].diff().dropna().dt.total_seconds() * 1000
    median_ms = dt_diff.median()
    pct_sub100ms = (dt_diff < 100).mean() * 100
    print(f"\n          Median tick interval: {median_ms:.1f}ms")
    print(f"          Sub-100ms ticks: {pct_sub100ms:.1f}%")
    assert median_ms < 5000, f"Tick frequency too low ({median_ms:.0f}ms) — likely holiday or thin market"

check("Quality: Tick frequency (median interval)", _t5)


# ─── TEST 6: Save sample to /data/ for pipeline use ──────────────────────────
data_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(data_dir, exist_ok=True)
csv_path = os.path.join(data_dir, f"XAUUSD_{TARGET_DATE.strftime('%Y%m%d_%H')}h_sample.csv")

def _t6():
    assert df is not None, "No DataFrame"
    df.to_csv(csv_path, index=False)
    size_kb = os.path.getsize(csv_path) / 1024
    print(f"\n          Saved → {csv_path}")
    print(f"          File size: {size_kb:.1f} KB")

check(f"Cache: Save sample CSV to /data/", _t6)


# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
print(f"  DUKASCOPY TEST RESULTS: {passed}/{len(results)} passed | {failed} failed")

if df is not None and not df.empty:
    print(f"\n  DATA STATUS: REAL_DUKASCOPY MODE AVAILABLE")
    print(f"  Ticks loaded: {len(df):,} | Period: 1 hour of {TARGET_DATE.date()}")
    print(f"  CSV cached: {csv_path}")
    print(f"\n  To run pipeline with real data:")
    print(f"    .venv\\Scripts\\python.exe master_pipeline.py --mode real")
    print(f"    .venv\\Scripts\\python.exe master_pipeline.py --mode real --start 2025-01-06 --end 2025-01-07")
    print("=" * 65 + "\n")
    sys.exit(0)
else:
    print(f"\n  DATA STATUS: FALLBACK TO SYNTHETIC MODE")
    print(f"  Run: .venv\\Scripts\\python.exe master_pipeline.py --mode synthetic")
    print("=" * 65 + "\n")
    sys.exit(1)
