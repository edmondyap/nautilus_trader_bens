# Nautilus Backtest Results - Run 20251115-141234

## Status: ❌ EXECUTION FAILED

**Issue:** Data format incompatibility - ParquetDataCatalog cannot load CSV-like parquet files

## Quick Access

- **Full Report:** `nautilus_execution_summary.md` (detailed analysis with solutions)
- **Data Analysis:** `data_analysis.txt` (validates data quality is excellent)
- **Metrics:** `preliminary_metrics.json` (structured failure data)
- **Logs:** `console_output.log` (complete execution trace)
- **Status:** `EXECUTION_STATUS.md` (checklist and next steps)

## One-Line Summary

6 hours of excellent market data (7.1M deltas, 291K trades) recorded but in wrong format for Nautilus - conversion required before backtest can run.

## Resolution Required

**Recommended:** Convert existing parquet files to Nautilus format (2-4 hours)
**See:** `nautilus_execution_summary.md` Section "Recommended Solutions"

## Key Findings

✅ **Data Quality:** Excellent
- 7,114,080 order book deltas
- 291,552 trade ticks
- 6 hours continuous coverage
- No data corruption

❌ **Format:** Incompatible
- CSV-like columns: ['action', 'price', 'side', 'size', 'timestamp']
- Need: Nautilus binary-serialized objects

## File Locations

**Results:** `/Users/benjaminang/Desktop/Trading Engines/benchmark/results/nautilus/6hr/run-20251115-141234/`
**Source Data:** `/Users/benjaminang/Desktop/Trading Engines/benchmark/data/nautilus_trader/6hr/20251110-000802/`
**Config:** `/Users/benjaminang/Desktop/Trading Engines/benchmark/strategies/nautilus/test_single_maker_config.yaml`

## Escalation

**Priority:** HIGH - Critical path blocker for Phase 3
**Awaiting:** Decision from orchestrator on resolution strategy
**Options:** (1) Convert data, (2) Re-record, (3) Modify script

---
Generated: 2025-11-15 14:13 PST | Agent: Subagent 1
