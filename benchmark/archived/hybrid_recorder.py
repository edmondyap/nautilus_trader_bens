#!/usr/bin/env python3
"""
ARCHIVED: Hybrid Nautilus Data Recorder (70% Native)

Nautilus Trader Evaluation Code - Trading Engines Project
Location: benchmark/nautilus_trader/archived/hybrid_recorder.py
Author: Benjamin Ang / Claude Code
Archived: 2025-11-09
Original Implementation: 2025-11-08

This is the original hybrid approach that combined:
- External: pybit WebSocket library for market data streaming
- Native: Nautilus TradeTick data models for data representation
- Native: Nautilus ParquetDataCatalog for persistence

Archived because: Replaced by more native Strategy-based implementation
Status: Working, proven approach (446 trades in 116 seconds)
Proven Recording: /benchmark/data/nautilus_trader/run-20251108-175256/

Nautilus Dependencies:
- nautilus_trader.adapters.bybit.BYBIT
- nautilus_trader.model.data.TradeTick
- nautilus_trader.model.enums.AggressorSide
- nautilus_trader.model.identifiers.InstrumentId, TradeId
- nautilus_trader.model.objects.Price, Quantity
- nautilus_trader.persistence.catalog.ParquetDataCatalog

External Dependencies:
- pybit.unified_trading.WebSocket (for live data streaming)

Upstream: nautilus_trader/ (DO NOT MODIFY)
Custom: This file (Archived, do not edit)

Usage (if needed):
    python hybrid_recorder.py SOLUSDT 120
"""
import asyncio
import json
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from pybit.unified_trading import WebSocket
from nautilus_trader.adapters.bybit import BYBIT
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.identifiers import InstrumentId, TradeId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.persistence.catalog import ParquetDataCatalog


class BybitSimpleRecorder:
    """Records live Bybit trade data and saves to Parquet catalog"""

    def __init__(
        self,
        symbol: str = "SOLUSDT",
        catalog_path: str | None = None,
        duration_seconds: int = 120,
    ):
        self.symbol = symbol
        self.duration_seconds = duration_seconds
        self._stop_event = asyncio.Event()
        self.trade_ticks = []
        self.raw_trades = []

        # Determine catalog path
        if catalog_path is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            catalog_path = f"/Users/benjaminang/Desktop/Trading Engines/benchmark/data/nautilus_trader/run-{timestamp}"

        self.catalog_path = Path(catalog_path)
        self.catalog_path.mkdir(parents=True, exist_ok=True)

        # Create instrument ID
        self.instrument_id = InstrumentId.from_str(f"{symbol}-SPOT.{BYBIT}")

        # WebSocket connection
        self.ws = None

        print(f"[Recorder] Initializing Bybit Simple Recorder")
        print(f"[Recorder] Symbol: {symbol}")
        print(f"[Recorder] Instrument ID: {self.instrument_id}")
        print(f"[Recorder] Catalog Path: {self.catalog_path}")
        print(f"[Recorder] Duration: {duration_seconds}s")

    def _handle_trade(self, message):
        """Handle trade tick messages"""
        try:
            if 'data' not in message:
                return

            for trade in message['data']:
                # Store raw trade for debugging
                self.raw_trades.append(trade)

                # Parse trade data
                trade_id = TradeId(str(trade['i']))
                price = Price.from_str(str(trade['p']))
                size = Quantity.from_str(str(trade['v']))
                aggressor_side = AggressorSide.BUYER if trade['S'] == 'Buy' else AggressorSide.SELLER

                # Convert timestamp (milliseconds to nanoseconds)
                ts_event = int(trade['T']) * 1_000_000
                ts_init = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)

                # Create TradeTick
                tick = TradeTick(
                    instrument_id=self.instrument_id,
                    price=price,
                    size=size,
                    aggressor_side=aggressor_side,
                    trade_id=trade_id,
                    ts_event=ts_event,
                    ts_init=ts_init,
                )

                self.trade_ticks.append(tick)

                if len(self.trade_ticks) % 10 == 0:
                    print(f"[Recorder] Collected {len(self.trade_ticks)} trades")

        except Exception as e:
            print(f"[Recorder] Error handling trade: {e}")
            import traceback
            traceback.print_exc()

    async def record(self):
        """Start recording market data"""
        print(f"[Recorder] Starting data recording...")

        # Create WebSocket connection
        self.ws = WebSocket(
            testnet=False,
            channel_type="spot",
        )

        # Subscribe to trade stream
        self.ws.trade_stream(
            symbol=self.symbol,
            callback=self._handle_trade
        )

        print(f"[Recorder] Subscribed to trade stream")
        print(f"[Recorder] Recording for {self.duration_seconds} seconds...")
        print(f"[Recorder] Press Ctrl+C to stop early")

        # Wait for duration or stop signal
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self.duration_seconds
            )
        except asyncio.TimeoutError:
            print(f"[Recorder] Recording duration ({self.duration_seconds}s) completed")

        # Stop recording
        await self.stop()

    async def stop(self):
        """Stop recording and save data"""
        print(f"[Recorder] Stopping recorder...")

        # Disconnect WebSocket
        if self.ws:
            try:
                self.ws.exit()
            except:
                pass

        # Save to Parquet
        print(f"[Recorder] Writing data to Parquet catalog...")
        self._write_to_catalog()

        print(f"[Recorder] Data saved to: {self.catalog_path}")
        print(f"[Recorder] Recording complete!")

    def _write_to_catalog(self):
        """Write collected data to ParquetDataCatalog"""
        trade_count = len(self.trade_ticks)

        print(f"[Recorder] Collected {trade_count} trades")

        if trade_count == 0:
            print(f"[Recorder] No data collected, nothing to write")
            # Save raw trades for debugging
            if self.raw_trades:
                raw_file = self.catalog_path / "raw_trades.json"
                with open(raw_file, 'w') as f:
                    json.dump(self.raw_trades, f, indent=2)
                print(f"[Recorder] Saved {len(self.raw_trades)} raw trades to: {raw_file}")
            return

        # Create catalog
        catalog = ParquetDataCatalog(str(self.catalog_path))

        # Write trade ticks
        print(f"[Recorder] Writing {trade_count} trade ticks to Parquet...")
        try:
            catalog.write_data(self.trade_ticks)
            print(f"[Recorder] Data persistence complete!")

            # Verify by reading back
            print(f"[Recorder] Verifying data...")
            # List parquet files
            parquet_files = list(self.catalog_path.glob("**/*.parquet"))
            print(f"[Recorder] Created {len(parquet_files)} Parquet files:")
            for pf in parquet_files:
                size = pf.stat().st_size
                print(f"[Recorder]   - {pf.relative_to(self.catalog_path)}: {size:,} bytes")

        except Exception as e:
            print(f"[Recorder] Error writing to catalog: {e}")
            import traceback
            traceback.print_exc()

        # Save summary statistics
        stats = {
            "symbol": self.symbol,
            "instrument_id": str(self.instrument_id),
            "duration_seconds": self.duration_seconds,
            "trade_count": trade_count,
            "catalog_path": str(self.catalog_path),
            "timestamp": datetime.now().isoformat(),
        }

        stats_file = self.catalog_path / "recording_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"[Recorder] Statistics saved to: {stats_file}")

        # Save sample of raw trades for debugging
        if self.raw_trades:
            sample_size = min(10, len(self.raw_trades))
            raw_sample = self.raw_trades[:sample_size]
            raw_file = self.catalog_path / "raw_trades_sample.json"
            with open(raw_file, 'w') as f:
                json.dump(raw_sample, f, indent=2)
            print(f"[Recorder] Saved sample of {sample_size} raw trades to: {raw_file}")

    def handle_signal(self, signum):
        """Handle shutdown signals"""
        print(f"\n[Recorder] Received signal {signum}, stopping...")
        self._stop_event.set()


async def main():
    """Main entry point"""
    # Parse command line arguments
    symbol = "SOLUSDT"
    duration = 120  # 2 minutes

    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    if len(sys.argv) > 2:
        duration = int(sys.argv[2])

    # Create recorder
    recorder = BybitSimpleRecorder(
        symbol=symbol,
        duration_seconds=duration,
    )

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: recorder.handle_signal(s))

    # Start recording
    await recorder.record()


if __name__ == "__main__":
    asyncio.run(main())
