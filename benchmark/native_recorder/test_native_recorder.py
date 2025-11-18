"""
Simple test of native recorder - 2 minute SOLUSDT recording
"""
import sys
from pathlib import Path

# Add benchmark to path
sys.path.insert(0, str(Path(__file__).parent / "benchmark"))

from nautilus_trader.adapters.bybit.factories import BybitLiveDataClientFactory
from nautilus_trader.adapters.bybit.config import BybitDataClientConfig
from nautilus_trader.adapters.bybit.common.enums import BybitProductType
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.live.node import TradingNode

# Import our native recorder
from nautilus_trader.native_recorder.strategy import (
    NativeDataRecorderStrategy,
    NativeDataRecorderConfig,
)

print("=" * 80)
print("NAUTILUS NATIVE DATA RECORDER - 2 MINUTE TEST")
print("=" * 80)
print()

# Create config
print("Creating configuration...")
strategy_config = NativeDataRecorderConfig(
    instrument_ids=["SOLUSDT-SPOT.BYBIT"],
    output_dir="data/test_recordings",
    flush_interval_seconds=30,  # Flush every 30 seconds for testing
    record_quotes=True,
    record_orderbook=False,
    orderbook_depth=50,
    connection_timeout_seconds=120,
    run_duration_seconds=120,  # 2 minutes
)

bybit_config = BybitDataClientConfig(
    api_key=None,  # Public data only
    api_secret=None,
    product_types=[BybitProductType.SPOT],
    testnet=False,
)

node_config = TradingNodeConfig(
    trader_id=TraderId("RECORDER-TEST"),
    data_clients={"BYBIT": bybit_config},
    timeout_connection=30.0,
)

print("✓ Configuration created")
print()

# Create strategy and node
print("Creating strategy and TradingNode...")
strategy = NativeDataRecorderStrategy(config=strategy_config)
node = TradingNode(config=node_config)
node.add_data_client_factory("BYBIT", BybitLiveDataClientFactory)
node.trader.add_strategy(strategy)
node.build()
print("✓ TradingNode ready")
print()

# Run
print("=" * 80)
print("STARTING 2-MINUTE RECORDING")
print("=" * 80)
print("Instrument: SOLUSDT-SPOT.BYBIT")
print("Duration: 120 seconds")
print("Output: data/test_recordings/")
print()
print("Recording will auto-stop after 2 minutes...")
print("Press Ctrl+C to stop early")
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
print(f"Check output: {strategy_config.output_dir}")
