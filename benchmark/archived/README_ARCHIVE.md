# Nautilus Trader Hybrid Recorder Archive

**Archive Date:** 2025-11-09
**Original Implementation:** 2025-11-08
**Status:** Working, Proven Implementation

---

## Overview

This directory contains the **hybrid (70% native)** Nautilus Trader data recording implementation that was successfully used to record and persist live market data from Bybit. While this approach worked well, it has been archived in favor of a more native Strategy-based implementation that better aligns with Nautilus Trader's architecture.

## What's Preserved

### Core Recording Implementation

**File:** `hybrid_recorder.py` (originally `recorder_native_ish.py`)

This is a working data recorder that combines:
- **External Component (30%):** pybit WebSocket library for live market data streaming
- **Native Components (70%):**
  - Nautilus `TradeTick` data models for data representation
  - Nautilus `ParquetDataCatalog` for data persistence
  - Nautilus instrument identifiers and type system

### Verification Tools

**Directory:** `verification_scripts/`

Contains `verify_parquet_catalog.py` - a utility script that:
- Loads and validates Parquet catalog recordings
- Displays trade statistics and data quality metrics
- Confirms data integrity across the persistence layer

## Proven Performance

### Successful Recording Session

**Recording:** `/benchmark/data/nautilus_trader/run-20251108-175256/`

**Results:**
- **Duration:** 120 seconds (2 minutes)
- **Trades Captured:** 446 trade ticks
- **Symbol:** SOLUSDT (Bybit Spot)
- **File Format:** Parquet (12,649 bytes compressed)
- **Data Quality:** ✅ Verified and readable
- **Status:** Production-ready data for backtesting

**Key Statistics:**
- Price Range: $160.99 - $161.28
- Average Price: $161.13
- Total Volume: 1,125.78 SOL
- Data Integrity: 100% (all trades preserved)

### Success Report

See `/benchmark/data/nautilus_trader/run-20251108-175256/SUCCESS_REPORT.md` for complete details.

## Why This Approach Worked

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                Hybrid Recorder                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [1] pybit WebSocket  ─────>  Bybit Live Stream    │
│           │                                          │
│           ├─> Raw JSON Trade Messages               │
│           │                                          │
│  [2] Parse & Transform                              │
│           │                                          │
│           ├─> Nautilus TradeTick Objects            │
│           │    - InstrumentId                        │
│           │    - Price, Quantity                     │
│           │    - AggressorSide                       │
│           │    - Timestamps (ns precision)           │
│           │                                          │
│  [3] In-Memory Collection                           │
│           │                                          │
│           └─> List[TradeTick]                       │
│                     │                                │
│  [4] Persistence                                    │
│           │                                          │
│           └─> ParquetDataCatalog.write_data()       │
│                     │                                │
│                     └─> Parquet Files (columnar)    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Key Insights

1. **Simple Data Flow:** Collect-then-write pattern is straightforward and reliable
2. **No Complex State:** Avoids TradingNode complexity and actor model overhead
3. **Direct Control:** Full visibility into WebSocket connection and data pipeline
4. **Proven Persistence:** Uses Nautilus's canonical Parquet format correctly
5. **Debugging Support:** Saves raw JSON for troubleshooting

### What Made This "Hybrid"

**Native (70%):**
- Nautilus data models (TradeTick, InstrumentId, Price, Quantity)
- Nautilus persistence layer (ParquetDataCatalog)
- Nautilus type system and enums
- Nautilus timestamp precision (nanoseconds)

**External (30%):**
- pybit WebSocket client (instead of Nautilus BybitDataClient)
- Custom event loop (instead of TradingNode/Actor system)
- Manual data collection (instead of streaming config)

## Why It Was Archived

### Reasons for Replacement

1. **Architecture Mismatch:** Doesn't use Nautilus's Strategy/Actor architecture
2. **Limited Integration:** Can't leverage Nautilus's live trading infrastructure
3. **External Dependency:** Relies on pybit instead of native Nautilus adapters
4. **No Strategy Framework:** Just data collection, not a full trading system

### More Native Approach

The replacement implementation:
- Uses Nautilus `Strategy` class for data handling
- Integrates with TradingNode and Actor system
- Uses native Bybit data client (when available)
- Supports full Nautilus ecosystem (backtesting, live trading, etc.)
- Better aligns with Nautilus best practices

## When to Use This Archive

### Good Use Cases

✅ **Quick Data Collection:**
If you just need to record market data quickly without TradingNode overhead.

✅ **Learning & Debugging:**
Simpler codebase makes it easier to understand Nautilus data models.

✅ **Standalone Recording:**
When you need data recording independent of a full trading system.

✅ **Reference Implementation:**
Example of how to use ParquetDataCatalog programmatically.

✅ **Minimal Dependencies:**
Fewer moving parts than full Strategy-based approach.

### When NOT to Use

❌ **Production Trading System:**
Use native Strategy-based approach for full trading capabilities.

❌ **Complex Strategies:**
This only records data; no strategy execution logic.

❌ **Live Trading:**
Not designed for order execution or position management.

❌ **Multi-Asset Systems:**
Better to use TradingNode for portfolio-level coordination.

## Usage Instructions

### Running the Hybrid Recorder

```bash
# Navigate to archive directory
cd /Users/benjaminang/Desktop/Trading\ Engines/benchmark/nautilus_trader/archived

# Record 2 minutes of SOLUSDT data
python3 hybrid_recorder.py SOLUSDT 120

# Record 5 minutes of BTCUSDT data
python3 hybrid_recorder.py BTCUSDT 300

# Press Ctrl+C to stop early
```

### Verifying Recordings

```bash
# Verify latest recording
cd verification_scripts
python3 verify_parquet_catalog.py

# Verify specific recording
python3 verify_parquet_catalog.py /path/to/catalog

# Example: Verify the proven recording
python3 verify_parquet_catalog.py \
  /Users/benjaminang/Desktop/Trading\ Engines/benchmark/data/nautilus_trader/run-20251108-175256
```

### Expected Output

**Recording:**
```
[Recorder] Initializing Bybit Simple Recorder
[Recorder] Symbol: SOLUSDT
[Recorder] Instrument ID: SOLUSDT-SPOT.BYBIT
[Recorder] Catalog Path: /path/to/catalog
[Recorder] Duration: 120s
[Recorder] Starting data recording...
[Recorder] Subscribed to trade stream
[Recorder] Recording for 120 seconds...
[Recorder] Collected 10 trades
[Recorder] Collected 20 trades
...
[Recorder] Collected 446 trades
[Recorder] Writing 446 trade ticks to Parquet...
[Recorder] Data persistence complete!
[Recorder] Recording complete!
```

**Verification:**
```
=== Verifying Nautilus Parquet Catalog ===
Catalog Path: /path/to/catalog

[1] Checking Instruments...
    Found 1 instruments
    - SOLUSDT-SPOT.BYBIT

[2] Checking Trade Ticks...
    Found 446 trade ticks
    Price range: $160.9900 - $161.2800
    Average price: $161.1297
    Total volume: 1125.78
    Buyer aggressor: 221 (49.6%)
    Seller aggressor: 225 (50.4%)

[5] Parquet Files...
    Found 1 Parquet files:
    - data/trade_tick/SOLUSDT-SPOT.BYBIT/2025-11-08T09-52-59-751063040Z_2025-11-08T09-54-56-039462144Z.parquet: 12,649 bytes

=== Verification Complete ===
SUCCESS: Catalog is valid and contains 446 trade ticks
```

## Technical Details

### Dependencies

**Python Packages:**
```
nautilus_trader>=1.190.0  # Core framework
pybit>=5.7.0              # Bybit WebSocket client
```

### Data Flow Details

**Timestamp Conversion:**
```python
# Bybit provides milliseconds
ts_event = int(trade['T']) * 1_000_000  # Convert to nanoseconds

# Nautilus expects nanosecond precision
ts_init = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)
```

**Aggressor Side Mapping:**
```python
# Bybit: 'Buy' or 'Sell' (taker side)
aggressor_side = AggressorSide.BUYER if trade['S'] == 'Buy' else AggressorSide.SELLER
```

**Instrument ID Format:**
```python
# Nautilus format: {symbol}-{venue_type}.{venue}
instrument_id = InstrumentId.from_str(f"{symbol}-SPOT.{BYBIT}")
# Example: SOLUSDT-SPOT.BYBIT
```

### Output Structure

```
run-YYYYMMDD-HHMMSS/
├── data/
│   └── trade_tick/
│       └── SOLUSDT-SPOT.BYBIT/
│           └── 2025-11-08T09-52-59-751063040Z_2025-11-08T09-54-56-039462144Z.parquet
├── recording_stats.json       # Session metadata
├── raw_trades_sample.json     # First 10 raw trades for debugging
└── SUCCESS_REPORT.md          # Generated if verification run
```

## Comparison: Hybrid vs Native

| Aspect | Hybrid (This Archive) | Native Strategy-Based |
|--------|----------------------|----------------------|
| **Complexity** | Low (200 lines) | Medium (500+ lines) |
| **Dependencies** | pybit + Nautilus | Nautilus only |
| **Architecture** | Simple async script | TradingNode + Strategy |
| **Data Models** | ✅ Native Nautilus | ✅ Native Nautilus |
| **Persistence** | ✅ ParquetDataCatalog | ✅ ParquetDataCatalog |
| **Live Trading** | ❌ Not supported | ✅ Full support |
| **Backtesting** | ❌ Data only | ✅ Full support |
| **Learning Curve** | Easy | Moderate |
| **Maintenance** | Low | Higher |
| **Production Ready** | For recording only | For full trading |

## Related Documentation

- **Hybrid Success Report:** `/benchmark/data/nautilus_trader/run-20251108-175256/SUCCESS_REPORT.md`
- **Recording Guide:** `/benchmark/nautilus_trader/DATA_RECORDING_GUIDE.md`
- **Nautilus Fixed Documentation:** `/benchmark/nautilus_trader/NAUTILUS_RECORDING_FIXED.md`
- **Main Nautilus README:** `/benchmark/nautilus_trader/README.md`

## Archive Maintenance

### Do NOT Edit

This archive is frozen for historical reference. Any modifications should be:
1. Documented in git history
2. Explained in this README
3. Minimal (bug fixes only, no enhancements)

### If You Need to Modify

Instead of editing archived files:
1. Copy the file to a new location
2. Make your modifications there
3. Update documentation to point to new version
4. Keep archive intact for comparison

## Credits

**Original Implementation:** Benjamin Ang / Claude Code
**Implementation Date:** 2025-11-08
**Proven Recording:** 446 trades in 120 seconds
**Archive Date:** 2025-11-09

**Nautilus Trader:** NautilusTrader/nautilus_trader (upstream)
**Bybit API:** Bybit official WebSocket API

---

## Summary

This hybrid approach successfully demonstrated that:
1. Nautilus data models work correctly
2. ParquetDataCatalog persistence is reliable
3. Live data can be recorded and verified
4. The system is ready for more native implementations

While archived, this implementation remains valuable as:
- A proven reference for ParquetDataCatalog usage
- A simpler alternative for basic data collection
- A learning resource for Nautilus data models
- A debugging baseline for comparison

**Status: ARCHIVED BUT WORKING** ✅

---

*Last Updated: 2025-11-09*
*Archive Version: 1.0*
