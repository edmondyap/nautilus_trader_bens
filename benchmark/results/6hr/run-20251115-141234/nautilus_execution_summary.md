# Nautilus Trader Backtest Execution Summary

**Run ID:** run-20251115-141234
**Timestamp:** 2025-11-15 14:12:34 PST
**Status:** **FAILED** ❌

---

## Executive Summary

The backtest failed to execute due to a **data format incompatibility** between the recorded parquet files and Nautilus Trader's `ParquetDataCatalog` expectations. While 6 hours of high-quality market data was successfully recorded (9M order book deltas, 300K trades), the data format prevents the backtest engine from loading it.

---

## Configuration Details

### Strategy Configuration
- **Strategy:** TestSingleMakerStrategy
- **Instrument:** SOLUSDT-LINEAR.BYBIT
- **Spread:** 10.0 bps (0.1%)
- **MA Window:** 5 minutes
- **Price Tolerance:** 15.0 bps (0.15%)
- **Order Size:** 1.0 SOL
- **Max Long Position:** 5.0 SOL
- **Max Short Position:** -5.0 SOL
- **Max Budget:** 5000 USDT

### Backtest Configuration
- **Starting Balance:** 5000 USDT, 0 SOL
- **Account Type:** MARGIN
- **OMS Type:** NETTING
- **Venue:** BYBIT
- **Data Path:** `/Users/benjaminang/Desktop/Trading Engines/benchmark/data/nautilus_trader/6hr/20251110-000802`

---

## Execution Timeline

1. **14:12:34** - Backtest script launched
2. **14:12:34** - Configuration loaded successfully
3. **14:12:34** - Nautilus BacktestEngine initialized (32ms)
4. **14:12:34** - ParquetDataCatalog opened data directory
5. **14:12:34** - Instruments detected: SOLUSD-INVERSE.BYBIT, SOLUSDT-LINEAR.BYBIT
6. **14:12:34** - **WARNING:** No order book deltas loaded (catalog returned 0 records)
7. **14:12:34** - **WARNING:** No trades loaded (catalog returned 0 records)
8. **14:12:34** - **ERROR:** Backtest engine failed with `ValueError: 'data' collection was empty`

**Total Execution Time:** < 1 second (crashed before backtest started)

---

## Root Cause Analysis

### Issue: Data Format Mismatch

The Nautilus `ParquetDataCatalog` expects parquet files containing **Nautilus-serialized objects** (e.g., `OrderBookDelta`, `TradeTick` instances with full metadata), but the recorded data contains **raw CSV-like columnar data**.

#### What Was Found

**Order Book Deltas Parquet Schema:**
```
Columns: ['action', 'order_id', 'price', 'side', 'size', 'timestamp']
Rows: 7,114,080
File Size: 42 MB
```

**Trade Ticks Parquet Schema:**
```
Columns: ['price', 'side', 'size', 'timestamp', 'trade_id']
Rows: 291,552
File Size: 11 MB
```

#### What Nautilus Expects

Nautilus `ParquetDataCatalog` expects:
- **Binary-serialized Nautilus objects** with full type information
- **Instrument metadata** embedded in the parquet schema
- **Timestamp fields** in Nautilus nanosecond format (`ts_event`, `ts_init`)
- **Enum types** for sides, actions (not string literals)
- **Venue/instrument identifiers** in Nautilus format

### Verification Tests

```python
# Test 1: Catalog cannot load data
catalog = ParquetDataCatalog(data_path)
deltas = catalog.order_book_deltas()  # Returns: []
trades = catalog.trade_ticks()         # Returns: []

# Test 2: Manual pandas read works (wrong format)
df = pd.read_parquet(delta_file)       # Returns: 7M rows ✓
# But columns are simple CSV-like, not Nautilus objects
```

### Data Recording Source

The data was recorded using:
```
/Users/benjaminang/Desktop/Trading Engines/benchmark/nautilus_trader/native_recorder/run_6hr_recording.py
```

**Session Metadata** (from `session_metadata.json`):
```json
{
  "run_id": "20251110-000802",
  "duration_seconds": 21599,
  "instruments": ["SOLUSDT-LINEAR.BYBIT", "SOLUSD-INVERSE.BYBIT"],
  "quote_count": 245375,
  "trade_count": 300098,
  "delta_count": 9052347
}
```

The recorder successfully captured data but exported it in a format incompatible with Nautilus backtesting.

---

## Validation Checks

| Check | Status | Details |
|-------|--------|---------|
| ✅ Config file valid | PASS | YAML parsed successfully |
| ✅ Data directory exists | PASS | Path found |
| ✅ Parquet files exist | PASS | All expected files present |
| ✅ Parquet files readable | PASS | Manual pandas read works |
| ✅ Data size reasonable | PASS | 42MB deltas, 11MB trades |
| ❌ Catalog can load data | **FAIL** | Returns empty collections |
| ❌ Backtest executed | **FAIL** | Crashed before start |
| ❌ Trades generated | **FAIL** | No execution |

---

## Output Files Generated

All files saved to: `/Users/benjaminang/Desktop/Trading Engines/benchmark/results/nautilus/6hr/run-20251115-141234/`

| File | Description | Status |
|------|-------------|--------|
| `console_output.log` | Complete execution log with error details | ✅ Created |
| `preliminary_metrics.json` | Structured failure analysis | ✅ Created |
| `nautilus_execution_summary.md` | This document | ✅ Created |
| `fills.csv` | Order fills report | ❌ Not generated (no execution) |
| `account.csv` | Account balance history | ❌ Not generated (no execution) |
| `positions.csv` | Position history | ❌ Not generated (no execution) |

---

## Recommended Solutions

### Option 1: Use Nautilus Native Recording (RECOMMENDED)

Re-record data using Nautilus's official `BacktestDataClientConfig` and `ParquetDataCatalog` write methods:

```python
# Use Nautilus native recording API
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog.from_env()
catalog.write_data(deltas)  # Writes in Nautilus native format
catalog.write_data(trades)
```

**Pros:**
- Native format compatibility
- Full metadata preservation
- Works with all Nautilus features

**Cons:**
- Requires re-recording 6 hours of data
- May need to adapt recording script

### Option 2: Convert Existing Data to Nautilus Format

Write a conversion script to transform CSV-like parquet into Nautilus objects:

```python
import pandas as pd
from nautilus_trader.model.data import OrderBookDelta, TradeTick

# Read raw parquet
df = pd.read_parquet("order_book_deltas.parquet")

# Convert to Nautilus objects
deltas = [
    OrderBookDelta(
        instrument_id=InstrumentId.from_str("SOLUSDT-LINEAR.BYBIT"),
        action=BookAction[row.action],
        order=BookOrder(
            price=Price(row.price),
            size=Quantity(row.size),
            side=OrderSide[row.side],
        ),
        ts_event=row.timestamp,
        ts_init=row.timestamp,
    )
    for row in df.itertuples()
]

# Write to catalog
catalog.write_data(deltas)
```

**Pros:**
- Preserves existing recorded data
- No re-recording needed

**Cons:**
- Complex conversion logic
- Potential timestamp/precision issues
- Time-consuming for 7M+ records

### Option 3: Modify Backtest Script to Load Raw Parquet

Bypass `ParquetDataCatalog` and load data directly, manually creating Nautilus objects:

```python
# Skip catalog, load parquet directly
df_deltas = pd.read_parquet(deltas_file)
df_trades = pd.read_parquet(trades_file)

# Convert and inject into engine
for row in df_deltas.itertuples():
    delta = create_delta_from_row(row)
    engine.add_data([delta])
```

**Pros:**
- Uses existing data as-is
- Quick implementation

**Cons:**
- Bypasses Nautilus data validation
- Manual timestamp handling
- May miss edge cases

---

## Impact Assessment

### Immediate Impact
- **No backtest results** for comparison with QTE
- **Cannot validate** TestSingleMakerStrategy behavior
- **Cannot measure** PnL, fill rates, or execution quality
- **Benchmark scorecard incomplete** - missing Nautilus column

### Downstream Impact
- **Phase 3 (Metrics Analysis) blocked** - no data to analyze
- **Phase 4 (Final Comparison) incomplete** - need both systems' results
- **CEO decision-making delayed** - missing critical data point

### Time Impact
- **Option 1 (re-record):** 6+ hours (recording time) + setup
- **Option 2 (convert):** 2-4 hours (development + conversion)
- **Option 3 (modify script):** 1-2 hours (implementation)

---

## Next Steps

### Immediate Actions Required

1. **Decision Point:** Choose resolution strategy (Option 1, 2, or 3)
2. **If Option 1 (re-record):**
   - Investigate Nautilus native recording API
   - Update `run_6hr_recording.py` to use ParquetDataCatalog.write()
   - Schedule 6-hour recording window
   - Verify output format before full run

3. **If Option 2 (convert):**
   - Develop conversion script
   - Test on small sample (100 records)
   - Run full conversion
   - Validate catalog can load converted data

4. **If Option 3 (modify script):**
   - Update `run_backtest.py` to bypass catalog
   - Implement manual parquet loading
   - Create Nautilus objects from raw data
   - Test with small dataset first

### Escalation

**Report to:** Orchestrator Agent
**Status:** BLOCKED - Awaiting decision on resolution strategy
**Priority:** HIGH - Critical path blocker for benchmark completion
**Estimated Resolution:** 1-6 hours depending on chosen approach

---

## Technical Appendix

### File Paths (Absolute)

**Configuration:**
- Config: `/Users/benjaminang/Desktop/Trading Engines/benchmark/strategies/nautilus/test_single_maker_config.yaml`
- Backtest Script: `/Users/benjaminang/Desktop/Trading Engines/benchmark/strategies/nautilus/run_backtest.py`

**Data Files:**
- Base Path: `/Users/benjaminang/Desktop/Trading Engines/benchmark/data/nautilus_trader/6hr/20251110-000802`
- Deltas (SOLUSDT): `./order_book_deltas/SOLUSDT-LINEAR.BYBIT/order_book_deltas.parquet`
- Trades (SOLUSDT): `./trade_ticks/SOLUSDT-LINEAR.BYBIT/trade_ticks.parquet`
- Metadata: `./session_metadata.json`

**Results:**
- Output Dir: `/Users/benjaminang/Desktop/Trading Engines/benchmark/results/nautilus/6hr/run-20251115-141234/`

### Error Stack Trace

```
File "run_backtest.py", line 187, in run_backtest
    engine.run(start=start_dt, end=end_dt)
File "nautilus_trader/backtest/engine.pyx", line 1092, in BacktestEngine.run
File "nautilus_trader/backtest/engine.pyx", line 1214, in BacktestEngine._run
File "nautilus_trader/core/correctness.pyx", line 532, in Condition.not_empty
ValueError: 'data' collection was empty
```

### System Environment

- **OS:** macOS 14.5 Sonoma (Darwin 23.5.0)
- **CPU:** Apple M1, 8 cores @ 3204 MHz
- **RAM:** 8 GB (79.55% used)
- **Python:** 3.x (invoked as `python3`)
- **Nautilus Version:** Latest installed via pip

---

## Conclusion

While the backtest infrastructure is correctly configured and the Nautilus engine initializes properly, the data format incompatibility prevents execution. The issue is **not** with the strategy code or backtest configuration, but with **how data was recorded**.

**The data exists and is valid** - it just needs to be in Nautilus-compatible format. Once resolved, the backtest should execute successfully and generate the metrics needed for Phase 3 comparison.

**Recommendation:** Proceed with **Option 2 (convert existing data)** as it balances speed (no 6-hour re-recording) with reliability (proper Nautilus format), unless the orchestrator identifies issues with the original recording methodology that warrant re-recording with a different approach.

---

**Generated by:** Nautilus Backtest Executor (Subagent 1)
**Date:** 2025-11-15
**Report Version:** 1.0
