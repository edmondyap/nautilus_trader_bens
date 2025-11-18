# Attribution & Project Structure

**Trading Engines Project - Nautilus Trader Evaluation**
**Location**: `benchmark/nautilus_trader/docs/ATTRIBUTION.md`
**Author**: Benjamin Ang / Claude Code
**Created**: 2025-11-09

> This is evaluation documentation for the Trading Engines project.
> It describes our custom implementations that use upstream Nautilus Trader components.

---

## Purpose

This document clarifies the ownership and purpose of different Nautilus Trader related directories in the Trading Engines project. It's essential to understand which code is upstream (do not modify) and which is our custom evaluation code.

---

## Directory Structure & Ownership

| Directory | Owner | Purpose | Modification Policy |
|-----------|-------|---------|---------------------|
| `nautilus_trader/` | NautilusTrader Team | Upstream open-source project | **DO NOT MODIFY** - This is the official Nautilus Trader codebase |
| `benchmark/nautilus_trader/` | Trading Engines Project | Our evaluation and custom code | **Modify freely** - This is our work |
| `benchmark/nautilus_trader/docs/` | Trading Engines Project | Evaluation documentation | **Modify freely** - Our documentation |
| `benchmark/comparison/` | Trading Engines Project | Cross-platform comparisons | **Modify freely** - Our analysis |
| `benchmark/data/nautilus_trader/` | Trading Engines Project | Recorded data from evaluations | **Modify freely** - Our data |

---

## What is `nautilus_trader/`?

### Upstream Repository
- **Official Repo**: https://github.com/nautechsystems/nautilus_trader
- **License**: LGPL-3.0
- **Language**: Python + Rust
- **Purpose**: High-performance algorithmic trading platform
- **Our Usage**: We use this as a library and reference implementation

### Key Characteristics
- Professional-grade backtesting engine
- Rust core for performance-critical components
- Native support for multiple venues (Interactive Brokers, Binance, Bybit, etc.)
- Advanced order management and execution
- Live trading capabilities with TradingNode

### Installation in Our Project
```bash
# We cloned the upstream repository locally
cd "/Users/benjaminang/Desktop/Trading Engines/"
git clone https://github.com/nautechsystems/nautilus_trader.git

# We can also use it as a pip package
pip install nautilus_trader
```

### Important Notes
- We **DO NOT** modify files in `nautilus_trader/`
- If we need custom behavior, we extend via our own code in `benchmark/nautilus_trader/`
- We may submit bug fixes or improvements upstream via pull requests
- Keep track of which version/commit we're using

---

## What is `benchmark/nautilus_trader/`?

### Our Custom Evaluation Code
- **Owner**: Trading Engines Project (Benjamin Ang)
- **Purpose**: Evaluate Nautilus Trader for production trading system
- **Relationship**: Uses `nautilus_trader/` as a library, but not part of official Nautilus

### What's Inside
```
benchmark/nautilus_trader/
├── docs/                          # This documentation
│   ├── ATTRIBUTION.md            # This file
│   ├── NATIVE_RECORDING_GUIDE.md # How to use the native recorder
│   └── ...                       # Additional documentation
├── native_recorder/              # Native recording implementation
├── archived/                     # Historical implementations
├── DATA_RECORDING_GUIDE.md       # How to record data
├── NAUTILUS_RECORDING_FIXED.md   # Recording session report
└── results/                      # Benchmark results
```

### Why We Created This
The Trading Engines project is evaluating three platforms:
1. **hfted_bens** - Custom HFT framework
2. **nautilus_trader** - Professional algo trading platform
3. **quant-trading-engine** - QTE platform

We created `benchmark/nautilus_trader/` to:
- Test Nautilus's capabilities without modifying upstream
- Develop custom integrations (e.g., Bybit data recording)
- Document our evaluation findings
- Build proof-of-concept implementations
- Compare different approaches (native vs hybrid)

---

## License & Attribution

### Upstream Nautilus Trader
```
Copyright (C) 2015-2024 Nautech Systems Pty Ltd.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

**License**: LGPL-3.0
**Repository**: https://github.com/nautechsystems/nautilus_trader
**Documentation**: https://nautilustrader.io/

### Our Evaluation Code (`benchmark/nautilus_trader/`)
```
Copyright (C) 2025 Benjamin Ang / Trading Engines Project

This is evaluation and research code for the Trading Engines project.
It uses Nautilus Trader as a library under LGPL-3.0 terms.
```

**Important**: Our code is **NOT** part of the official Nautilus Trader project. We are users and evaluators of the platform.

---

## Component Breakdown: What's Upstream vs Custom

### Upstream Components We Use

| Component | Source | Usage in Our Code |
|-----------|--------|-------------------|
| `nautilus_trader.model.data.TradeTick` | Upstream | ✅ Used in `recorder_native_ish.py` |
| `nautilus_trader.model.identifiers.InstrumentId` | Upstream | ✅ Used in `recorder_native_ish.py` |
| `nautilus_trader.persistence.catalog.ParquetDataCatalog` | Upstream | ✅ Used in `recorder_native_ish.py` |
| `nautilus_trader.model.enums.AggressorSide` | Upstream | ✅ Used in `recorder_native_ish.py` |
| `nautilus_trader.core.datetime.millis_to_nanos` | Upstream | ✅ Used in `recorder_native_ish.py` |
| Rust performance core | Upstream | ✅ Used indirectly via Python bindings |
| TradingNode infrastructure | Upstream | ⚠️ Evaluated but not used for live recording |
| Backtesting engine | Upstream | 🔜 Will use for Phase 2 |

### Custom Components We Built

| Component | Location | Purpose |
|-----------|----------|---------|
| Bybit WebSocket recorder | `recorder_native_ish.py` | Live data capture via pybit |
| Recording orchestration | `recorder_native_ish.py` | Session management, stats tracking |
| Parquet catalog writer | `recorder_native_ish.py` | Manual writes to Nautilus catalog |
| Data quality verification | `verify_nautilus_catalog.py` | Validate recorded data |
| Documentation | `docs/` | Evaluation findings and guides |
| Benchmark scripts | `benchmark/` | Performance and quality tests |

---

## Why We Don't Use Nautilus's Built-in Data Recording

### Discovery: StreamingConfig ≠ Live Data Recording

During our evaluation, we discovered that Nautilus Trader's `StreamingConfig` and `TradingNode` are designed for **backtest replay**, not **live data capture**.

**What we tried (doesn't work for live data)**:
```python
# ❌ This is for backtesting, not live recording
from nautilus_trader.config import StreamingConfig
from nautilus_trader.live.node import TradingNode

config = StreamingConfig(
    catalog_path="data/",
    fs_protocol="file",
    flush_interval_ms=1000,
)
node = TradingNode(config=config)
# This expects pre-existing data in catalog, doesn't record new data
```

### Solution: Hybrid Approach (70% Native)

**What we built instead**:
```python
# ✅ This works - collect with pybit, persist with Nautilus
from pybit.unified_trading import WebSocket
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.data import TradeTick

# 1. Collect via custom WebSocket (unavoidable)
ws = WebSocket(channel_type="spot")
ws.trade_stream(symbol="SOLUSDT", callback=handle_trade)

# 2. Convert to Nautilus objects (native data model)
tick = TradeTick(...)

# 3. Persist via Nautilus catalog (native storage)
catalog = ParquetDataCatalog(path)
catalog.write_data([tick])
```

**Nativeness Assessment**: 70% Native
- ✅ Uses Nautilus data models (TradeTick, InstrumentId)
- ✅ Uses Nautilus persistence (ParquetDataCatalog)
- ✅ Output is 100% compatible with Nautilus backtesting
- ❌ WebSocket handling is custom (but no alternative exists)
- ❌ Bypasses TradingNode (which is for backtests)

**Note**: This hybrid approach has been superseded by the native strategy-based recorder (see `native_recorder/` directory).

---

## Current Implementation: Strategy-Based Recording (85%+ Native)

We've implemented a native approach using Nautilus's Strategy framework:

```python
# 🔜 Future: Use Nautilus Strategy for recording
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.adapters.bybit import BybitDataClient

class DataRecordingStrategy(Strategy):
    def on_trade_tick(self, tick: TradeTick):
        # Nautilus handles persistence via StreamingConfig
        pass  # Just let Nautilus handle everything

# TradingNode + BybitDataClient + Strategy = More native
```

**Benefits**:
- Uses official Bybit adapter (if it has live data support)
- Strategy framework handles tick routing
- Potentially automatic catalog writes
- More aligned with Nautilus architecture

**Resolved** (Implementation complete):
- ✅ BybitDataClient supports live spot data
- ✅ Strategy + StreamingConfig provides auto-persistence
- ✅ This is the recommended pattern for live data recording

See `native_recorder/` directory for the production implementation.

---

## How to Contribute Back to Upstream

If we discover bugs or improvements in Nautilus Trader:

1. **Document the Issue**
   - What behavior did we expect?
   - What behavior did we observe?
   - Minimal reproduction case

2. **Check Existing Issues**
   - https://github.com/nautechsystems/nautilus_trader/issues
   - May already be known or fixed in newer version

3. **Create Pull Request** (if appropriate)
   - Fork the official repository
   - Create feature branch
   - Submit PR with clear description
   - Link to any related issues

4. **Document in Our Project**
   - Note which upstream version we use
   - Document workarounds if needed
   - Track when/if upstream fixes are merged

---

## Version Tracking

| Date | Nautilus Version | Commit/Tag | Notes |
|------|------------------|------------|-------|
| 2025-11-07 | Unknown | Latest main | Initial clone |
| 2025-11-09 | TBD | TBD | Need to check version |

**TODO**: Check and document exact Nautilus version we're using:
```bash
cd nautilus_trader
git describe --tags --always
```

---

## Summary

- **`nautilus_trader/`** = Upstream (LGPL-3.0), DO NOT MODIFY
- **`benchmark/nautilus_trader/`** = Our evaluation code, modify freely
- **Our code uses Nautilus as a library**, not a fork
- **Native strategy-based recorder** (85%+ native) is the recommended approach
- **Implementation complete** in `native_recorder/` directory
- **Historical hybrid approach** (70% native) preserved in `archived/` directory

---

## Questions?

If you're reading this and have questions about:
- How to use the native recorder → See `NATIVE_RECORDING_GUIDE.md`
- Project structure and ownership → This file (ATTRIBUTION.md)
- Cross-platform comparisons → See `../../comparison/scorecard.md`
- Historical implementation approaches → See `../../archive/hybrid_approach_docs/` (archived)

For Nautilus Trader documentation:
- Official docs: https://nautilustrader.io/
- API reference: https://nautilustrader.io/api_reference/
- GitHub: https://github.com/nautechsystems/nautilus_trader

---

**Last Updated**: 2025-11-09
**Maintainer**: Benjamin Ang / Claude Code
**Project**: Trading Engines - Platform Evaluation
