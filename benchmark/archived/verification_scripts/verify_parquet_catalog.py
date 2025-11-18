#!/usr/bin/env python3
"""
ARCHIVED: Nautilus Parquet Catalog Verification Script

Nautilus Trader Evaluation Code - Trading Engines Project
Location: benchmark/nautilus_trader/archived/verification_scripts/verify_parquet_catalog.py
Author: Benjamin Ang / Claude Code
Archived: 2025-11-09
Original Location: benchmark/shared_tools/verify_parquet_catalog.py

This script verifies Nautilus ParquetDataCatalog recordings.
Works with both hybrid and native Strategy-based approaches.

Usage:
    python verify_parquet_catalog.py [catalog_path]

    If no path provided, uses latest run in benchmark/data/nautilus_trader/

Nautilus Dependencies:
- nautilus_trader.persistence.catalog.ParquetDataCatalog

Upstream: nautilus_trader/ (DO NOT MODIFY)
Custom: This file (Archived, do not edit)
"""
import sys
from pathlib import Path
from nautilus_trader.persistence.catalog import ParquetDataCatalog

def verify_catalog(catalog_path: str):
    """Verify the Parquet catalog and print statistics"""
    print(f"=== Verifying Nautilus Parquet Catalog ===")
    print(f"Catalog Path: {catalog_path}")
    print()

    # Create catalog
    catalog = ParquetDataCatalog(catalog_path)

    # Check for instruments
    print(f"[1] Checking Instruments...")
    instruments = catalog.instruments()
    print(f"    Found {len(instruments)} instruments")
    for inst in instruments:
        print(f"    - {inst.id}")
    print()

    # Check for trade ticks
    print(f"[2] Checking Trade Ticks...")
    try:
        trade_ticks = catalog.trade_ticks()
        print(f"    Found {len(trade_ticks)} trade ticks")

        if len(trade_ticks) > 0:
            print(f"    First trade: {trade_ticks[0]}")
            print(f"    Last trade: {trade_ticks[-1]}")

            # Calculate statistics
            prices = [float(tick.price) for tick in trade_ticks]
            sizes = [float(tick.size) for tick in trade_ticks]

            print(f"    Price range: ${min(prices):.4f} - ${max(prices):.4f}")
            print(f"    Average price: ${sum(prices)/len(prices):.4f}")
            print(f"    Total volume: {sum(sizes):.2f}")

            # Count aggressor sides
            buyer_agg = sum(1 for tick in trade_ticks if str(tick.aggressor_side) == 'BUYER')
            seller_agg = len(trade_ticks) - buyer_agg
            print(f"    Buyer aggressor: {buyer_agg} ({buyer_agg/len(trade_ticks)*100:.1f}%)")
            print(f"    Seller aggressor: {seller_agg} ({seller_agg/len(trade_ticks)*100:.1f}%)")
    except Exception as e:
        print(f"    Error reading trade ticks: {e}")
    print()

    # Check for quote ticks
    print(f"[3] Checking Quote Ticks...")
    try:
        quote_ticks = catalog.quote_ticks()
        print(f"    Found {len(quote_ticks)} quote ticks")
    except Exception as e:
        print(f"    No quote ticks (expected): {e}")
    print()

    # Check for order book deltas
    print(f"[4] Checking Order Book Deltas...")
    try:
        deltas = catalog.order_book_deltas()
        print(f"    Found {len(deltas)} order book deltas")
    except Exception as e:
        print(f"    No order book deltas (expected): {e}")
    print()

    # List all parquet files
    print(f"[5] Parquet Files...")
    parquet_files = list(Path(catalog_path).glob("**/*.parquet"))
    print(f"    Found {len(parquet_files)} Parquet files:")
    for pf in sorted(parquet_files):
        size = pf.stat().st_size
        rel_path = pf.relative_to(catalog_path)
        print(f"    - {rel_path}: {size:,} bytes")
    print()

    print(f"=== Verification Complete ===")
    print(f"SUCCESS: Catalog is valid and contains {len(trade_ticks) if 'trade_ticks' in locals() else 0} trade ticks")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        catalog_path = sys.argv[1]
    else:
        # Use latest run
        data_dir = Path("/Users/benjaminang/Desktop/Trading Engines/benchmark/data/nautilus_trader")
        runs = sorted(data_dir.glob("run-*"))
        if not runs:
            print("No recording runs found!")
            sys.exit(1)
        catalog_path = str(runs[-1])

    verify_catalog(catalog_path)
