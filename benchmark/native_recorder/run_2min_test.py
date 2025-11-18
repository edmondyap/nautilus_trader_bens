#!/usr/bin/env python3
"""
2-Minute Native Recorder Test
Directly imports from benchmark directory
"""
import sys
import asyncio
import os
from pathlib import Path

# Ensure no Bybit credentials in environment (for testing public-only mode)
for key in ['BYBIT_API_KEY', 'BYBIT_API_SECRET',
            'BYBIT_TESTNET_API_KEY', 'BYBIT_TESTNET_API_SECRET',
            'BYBIT_DEMO_API_KEY', 'BYBIT_DEMO_API_SECRET']:
    os.environ.pop(key, None)

# Add parent directory to Python path
parent_path = Path(__file__).parent
sys.path.insert(0, str(parent_path))

# No monkey patch needed! With use_env_fallback=False and api_key=None:
# - Rust client has credential=None
# - get_fee_rate() returns MissingCredentials (handled gracefully)
# - Instruments load via public API with default fees
print("✓ Public-only mode enabled (no monkey patch needed)")

print("=" * 80)
print("NAUTILUS NATIVE DATA RECORDER - 2 MINUTE TEST")
print("=" * 80)
print()

# Now import from our implementation (note: benchmark.nautilus_trader.native_recorder)
try:
    from benchmark.nautilus_trader.native_recorder.strategy import (
        NativeDataRecorderStrategy,
        NativeDataRecorderConfig,
    )
    from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder
    print("✓ Successfully imported native_recorder modules")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Import Nautilus components
from nautilus_trader.adapters.bybit.factories import BybitLiveDataClientFactory
from nautilus_trader.adapters.bybit.config import BybitDataClientConfig
from nautilus_trader.core.nautilus_pyo3 import BybitProductType
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.live.node import TradingNode

print()
print("Creating configuration...")

# Use the builder for cleaner code
builder = RecorderConfigBuilder(trader_id="TEST-RECORDER")
builder.add_instrument("SOLUSDT-SPOT.BYBIT")
builder.set_output_dir("data/test_recordings")
builder.set_duration(120)  # 2 minutes
builder.set_flush_interval(30)  # Flush every 30 seconds
builder.enable_public_only_mode()  # Enable public-only mode (no credentials required)
builder.enable_orderbook(depth=50)  # Enable 50-level orderbook recording (matching QTE)

node_config, strategy_config = builder.build()

print("✓ Configuration created")
print(f"  Instrument: {strategy_config.instrument_ids}")
print(f"  Duration: {strategy_config.run_duration_seconds}s")
print(f"  Output: {strategy_config.output_dir}")
print()

# Create event loop first (required for Nautilus async operations)
print("Setting up async event loop...")
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
print("✓ Event loop ready")
print()

# Create strategy and node
print("Creating TradingNode...")
strategy = NativeDataRecorderStrategy(config=strategy_config)
node = TradingNode(config=node_config)
node.add_data_client_factory("BYBIT", BybitLiveDataClientFactory)
node.trader.add_strategy(strategy)
node.build()
print("✓ TradingNode built successfully")
print()

# Run
print("=" * 80)
print("STARTING 2-MINUTE RECORDING")
print("=" * 80)
print("Will auto-stop after 120 seconds...")
print("Press Ctrl+C to stop early (data will be saved)")
print()

try:
    node.run()
except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted, stopping gracefully...")
finally:
    if node.trader.is_running:
        print("Stopping node...")
        node.stop()

print()
print("=" * 80)
print("RECORDING COMPLETE")
print("=" * 80)
print(f"Output directory: {strategy_config.output_dir}")
print()
print("To validate:")
print(f"  cd /Users/benjaminang/Desktop/Trading\\ Engines")
print(f"  ls -lh {strategy_config.output_dir}/")
