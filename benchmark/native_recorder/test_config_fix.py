"""
Test Configuration Fix - Verify instrument loading config is set correctly

This script validates that the RecorderConfigBuilder correctly sets up
the InstrumentProviderConfig to enable instrument loading.

Expected behavior:
1. Build config using RecorderConfigBuilder
2. Verify instrument_provider config has load_all=True
3. Confirm config is valid for TradingNode
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder


def test_config_has_instrument_provider():
    """Test that config builder sets instrument_provider with load_all=True."""
    print("=" * 80)
    print("TEST: RecorderConfigBuilder Instrument Provider Configuration")
    print("=" * 80)
    print()

    # Create builder and build config
    print("Step 1: Creating RecorderConfigBuilder...")
    builder = RecorderConfigBuilder(trader_id="TEST-RECORDER-001")
    builder.add_instrument("SOLUSDT-SPOT.BYBIT")
    builder.set_output_dir("./test_output")
    builder.enable_public_only_mode()
    print("✓ Builder created")
    print()

    print("Step 2: Building configuration...")
    node_config, strategy_config = builder.build()
    print("✓ Configuration built")
    print()

    # Verify the config
    print("Step 3: Verifying configuration...")
    print()

    # Check that BYBIT data client exists
    assert "BYBIT" in node_config.data_clients, "BYBIT data client not found"
    bybit_config = node_config.data_clients["BYBIT"]
    print(f"✓ BYBIT data client config found: {type(bybit_config).__name__}")

    # Check that instrument_provider is set
    assert bybit_config.instrument_provider is not None, "instrument_provider is None"
    print(f"✓ instrument_provider is set: {type(bybit_config.instrument_provider).__name__}")

    # Check that load_all is True
    assert bybit_config.instrument_provider.load_all is True, "load_all is not True"
    print(f"✓ load_all = {bybit_config.instrument_provider.load_all}")

    # Check log_warnings
    print(f"✓ log_warnings = {bybit_config.instrument_provider.log_warnings}")
    print()

    # Display full config details
    print("Step 4: Configuration details:")
    print(f"   Trader ID: {node_config.trader_id}")
    print(f"   Product Types: {bybit_config.product_types}")
    print(f"   API Key: {repr(bybit_config.api_key)}")
    print(f"   API Secret: {repr(bybit_config.api_secret)}")
    print(f"   Testnet: {bybit_config.testnet}")
    print()
    print(f"   Instrument Provider:")
    print(f"      - load_all: {bybit_config.instrument_provider.load_all}")
    print(f"      - load_ids: {bybit_config.instrument_provider.load_ids}")
    print(f"      - log_warnings: {bybit_config.instrument_provider.log_warnings}")
    print()

    print("Step 5: Strategy configuration:")
    print(f"   Instruments: {strategy_config.instrument_ids}")
    print(f"   Output Dir: {strategy_config.output_dir}")
    print(f"   Record Quotes: {strategy_config.record_quotes}")
    print(f"   Record Orderbook: {strategy_config.record_orderbook}")
    print()

    print("=" * 80)
    print("TEST RESULT: SUCCESS")
    print("=" * 80)
    print()
    print("✓ InstrumentProviderConfig is correctly set")
    print("✓ load_all=True will enable instrument loading")
    print("✓ Configuration is ready for TradingNode")
    print()
    print("ROOT CAUSE IDENTIFIED:")
    print("   The original config was missing instrument_provider config,")
    print("   which defaults to load_all=False and load_ids=None.")
    print("   This caused the 'No loading configured' warning.")
    print()
    print("FIX APPLIED:")
    print("   Added InstrumentProviderConfig(load_all=True) to enable")
    print("   automatic loading of all SPOT instruments on startup.")
    print()

    return True


def main():
    """Run the test."""
    print("\n")
    print("*" * 80)
    print("CONFIGURATION FIX VALIDATION TEST")
    print("*" * 80)
    print()

    try:
        success = test_config_has_instrument_provider()
        if success:
            print("*" * 80)
            print("CONFIGURATION FIX VALIDATED")
            print("*" * 80)
            print()
            print("Next Steps:")
            print("1. Re-run the integration test")
            print("2. Verify instruments load without 'No loading configured' warning")
            print("3. Verify order book data can be parsed (instruments available)")
            print()
            return True
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
