"""
Test Recording Script - Nautilus Trader Native Data Recorder

This script tests the native recorder implementation with a short recording session.

Usage:
    python test_recording.py

Expected Output:
    - 2-minute recording of SOLUSDT
    - Parquet files in data/test_recordings/
    - Session metadata and checksums
"""

import sys
from pathlib import Path

# Add benchmark to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark.nautilus_trader.native_recorder.config import create_quick_config
from benchmark.nautilus_trader.native_recorder.strategy import NativeDataRecorderStrategy
from nautilus_trader.adapters.bybit.factories import BybitLiveDataClientFactory
from nautilus_trader.live.node import TradingNode


def main():
    """Run test recording session."""
    print("=" * 80)
    print("NAUTILUS TRADER NATIVE DATA RECORDER - TEST RECORDING")
    print("=" * 80)
    print()

    # Create quick configuration
    print("Creating configuration...")
    node_config, strategy_config = create_quick_config(
        instruments=["SOLUSDT-SPOT.BYBIT"],
        output_dir="data/test_recordings",
        duration_seconds=120,  # 2 minutes
        with_orderbook=False,  # Quotes only for simplicity
    )
    print(f"✓ Configuration created")
    print(f"  - Instrument: SOLUSDT-SPOT.BYBIT")
    print(f"  - Duration: 120 seconds (2 minutes)")
    print(f"  - Output: data/test_recordings/")
    print()

    # Create strategy
    print("Creating strategy...")
    strategy = NativeDataRecorderStrategy(config=strategy_config)
    print("✓ Strategy created")
    print()

    # Create trading node
    print("Creating TradingNode...")
    node = TradingNode(config=node_config)
    node.add_data_client_factory("BYBIT", BybitLiveDataClientFactory)
    node.trader.add_strategy(strategy)
    node.build()
    print("✓ TradingNode initialized")
    print()

    # Run recording
    print("=" * 80)
    print("STARTING RECORDING SESSION")
    print("=" * 80)
    print()
    print("Recording will run for 2 minutes...")
    print("Press Ctrl+C to stop early (data will be saved)")
    print()

    try:
        node.run()
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        if node.trader.is_running:
            node.stop()

    print()
    print("=" * 80)
    print("RECORDING COMPLETE")
    print("=" * 80)
    print()
    print(f"Output directory: {strategy_config.output_dir}")
    print()
    print("Next steps:")
    print("1. Validate recording:")
    print(f"   python validation/validate_recording.py {strategy_config.output_dir}/[run_id]")
    print()
    print("2. Analyze data:")
    print("   python -c \"from benchmark.nautilus_trader.native_recorder.persistence import RecordingReader; r = RecordingReader('[path]'); print(r.get_statistics())\"")
    print()


if __name__ == "__main__":
    main()
