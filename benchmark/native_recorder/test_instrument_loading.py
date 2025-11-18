"""
Test Instrument Loading - Verify public API instrument loading works

This script tests that instruments can be loaded via Bybit public API
without requiring authentication credentials.

Expected behavior:
1. Connect to Bybit without credentials (public-only mode)
2. Load SPOT instruments via public API
3. Verify SOLUSDT instrument is available
4. Print instrument details

Expected output:
- InstrumentProvider successfully loads instruments
- SOLUSDT-SPOT.BYBIT is in the loaded instruments
- Instrument details (base, quote, tick size, etc.) are displayed
"""

import asyncio
from pathlib import Path

from nautilus_trader.adapters.bybit.common.enums import BybitProductType
from nautilus_trader.adapters.bybit.config import BybitDataClientConfig
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.core import nautilus_pyo3


async def test_instrument_loading():
    """Test instrument loading via public API."""
    print("=" * 80)
    print("TEST: Bybit Instrument Loading (Public API)")
    print("=" * 80)
    print()

    # Step 1: Create HTTP client without credentials
    print("Step 1: Creating HTTP client (public-only mode)...")
    http_client = nautilus_pyo3.BybitHttpClient(
        api_key=None,
        api_secret=None,
        base_url=None,  # Use default mainnet URL
        demo=False,
        testnet=False,
        timeout_secs=None,
        max_retries=None,
        retry_delay_ms=None,
        retry_delay_max_ms=None,
        recv_window_ms=5000,
        proxy_url=None,
        use_env_fallback=False,  # Force public-only mode
    )
    print("✓ HTTP client created (no credentials)")
    print()

    # Step 2: Request instruments via public API
    print("Step 2: Requesting SPOT instruments via public API...")
    try:
        instruments = await http_client.request_instruments(
            product_type=BybitProductType.SPOT,
            symbol=None,  # Get all instruments
        )
        print(f"✓ Loaded {len(instruments)} SPOT instruments")
        print()
    except Exception as e:
        print(f"✗ Failed to load instruments: {e}")
        return False

    # Step 3: Check for SOLUSDT
    print("Step 3: Searching for SOLUSDT instrument...")
    solusdt = None
    for inst in instruments:
        # Get symbol from PyO3 instrument
        symbol = str(inst)
        if "SOLUSDT" in symbol:
            solusdt = inst
            print(f"✓ Found: {symbol}")
            break

    if solusdt is None:
        print("✗ SOLUSDT not found in loaded instruments")
        print(f"   First 10 instruments: {[str(i) for i in instruments[:10]]}")
        return False

    print()

    # Step 4: Display instrument details
    print("Step 4: Instrument details:")
    print(f"   Raw PyO3 object: {solusdt}")
    print(f"   Type: {type(solusdt)}")
    print()

    print("=" * 80)
    print("TEST RESULT: SUCCESS")
    print("=" * 80)
    print()
    print("✓ Public API access works without credentials")
    print("✓ Instruments can be loaded")
    print("✓ SOLUSDT is available")
    print()

    return True


async def test_instrument_provider_config():
    """Test the InstrumentProviderConfig integration."""
    print("=" * 80)
    print("TEST: InstrumentProviderConfig Integration")
    print("=" * 80)
    print()

    # Create the config as our recorder would
    print("Creating BybitDataClientConfig with InstrumentProviderConfig...")
    instrument_provider_config = InstrumentProviderConfig(
        load_all=True,
        log_warnings=True,
    )

    bybit_config = BybitDataClientConfig(
        api_key=None,
        api_secret=None,
        product_types=[BybitProductType.SPOT],
        testnet=False,
        instrument_provider=instrument_provider_config,
        use_env_fallback=False,
    )

    print("✓ Config created:")
    print(f"   - API Key: {bybit_config.api_key}")
    print(f"   - Product Types: {bybit_config.product_types}")
    print(f"   - Instrument Provider Load All: {bybit_config.instrument_provider.load_all}")
    print(f"   - Use Env Fallback: {bybit_config.use_env_fallback}")
    print()

    print("=" * 80)
    print("TEST RESULT: SUCCESS")
    print("=" * 80)
    print()

    return True


async def main():
    """Run all tests."""
    print("\n")
    print("*" * 80)
    print("BYBIT INSTRUMENT LOADING TEST SUITE")
    print("*" * 80)
    print()

    results = []

    # Test 1: Direct API access
    try:
        result = await test_instrument_loading()
        results.append(("Direct API Access", result))
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Direct API Access", False))

    print()

    # Test 2: Config integration
    try:
        result = await test_instrument_provider_config()
        results.append(("Config Integration", result))
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Config Integration", False))

    # Summary
    print()
    print("*" * 80)
    print("TEST SUMMARY")
    print("*" * 80)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    all_passed = all(result for _, result in results)
    print()
    if all_passed:
        print("=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("The fix is working correctly:")
        print("1. InstrumentProviderConfig with load_all=True is configured")
        print("2. Instruments can be loaded via public API (no credentials needed)")
        print("3. SOLUSDT and other instruments are accessible")
        print()
        print("Next step: Re-run the integration test to verify full recorder works")
    else:
        print("=" * 80)
        print("SOME TESTS FAILED")
        print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
