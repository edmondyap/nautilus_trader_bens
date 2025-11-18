#!/usr/bin/env python3
"""
Validation script for TestSingleMakerStrategy implementation.

Checks that the implementation meets all requirements from the benchmark spec.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")


def print_check(passed: bool, description: str) -> bool:
    """Print a check result."""
    symbol = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
    print(f"{symbol} {description}")
    return passed


def validate_files() -> bool:
    """Validate that all required files exist."""
    print_header("File Structure Validation")

    base_path = Path(__file__).parent
    required_files = [
        "test_single_maker_strategy.py",
        "test_single_maker_config.yaml",
        "run_backtest.py",
        "README.md",
    ]

    all_passed = True
    for filename in required_files:
        file_path = base_path / filename
        passed = file_path.exists()
        all_passed = all_passed and print_check(passed, f"{filename} exists")

    return all_passed


def validate_imports() -> bool:
    """Validate that strategy can be imported."""
    print_header("Import Validation")

    all_passed = True

    try:
        from test_single_maker_strategy import (
            TestSingleMakerStrategy,
            TestSingleMakerStrategyConfig,
        )

        all_passed = all_passed and print_check(True, "Strategy imports successfully")
        all_passed = all_passed and print_check(True, "TestSingleMakerStrategy class found")
        all_passed = all_passed and print_check(
            True,
            "TestSingleMakerStrategyConfig class found",
        )
    except ImportError as e:
        all_passed = False
        print_check(False, f"Import failed: {e}")
        return all_passed

    return all_passed


def validate_config() -> bool:
    """Validate configuration parameters."""
    print_header("Configuration Validation")

    try:
        from test_single_maker_strategy import TestSingleMakerStrategyConfig
        from nautilus_trader.model.identifiers import InstrumentId

        all_passed = True

        # Create a test config with default values
        config = TestSingleMakerStrategyConfig(
            instrument_id=InstrumentId.from_str("SOLUSDT-LINEAR.BYBIT"),
        )

        # Check default values match spec
        checks = [
            (config.spread_bps == 10.0, "spread_bps default is 10.0"),
            (config.ma_window_minutes == 5, "ma_window_minutes default is 5"),
            (config.price_tolerance_bps == 15.0, "price_tolerance_bps default is 15.0"),
            (config.order_size_base == Decimal("1.0"), "order_size_base default is 1.0"),
            (config.max_long_position == Decimal("5.0"), "max_long_position default is 5.0"),
            (
                config.max_short_position == Decimal("5.0"),
                "max_short_position default is 5.0",
            ),
            (config.max_budget_quote == Decimal("5000.0"), "max_budget_quote default is 5000.0"),
            (config.book_type == "L2_MBP", "book_type default is L2_MBP"),
        ]

        for check, description in checks:
            all_passed = all_passed and print_check(check, description)

        return all_passed

    except Exception as e:
        print_check(False, f"Config validation failed: {e}")
        return False


def validate_strategy_methods() -> bool:
    """Validate that strategy has required methods."""
    print_header("Strategy Method Validation")

    try:
        from test_single_maker_strategy import TestSingleMakerStrategy

        all_passed = True

        required_methods = [
            "on_start",
            "on_stop",
            "on_reset",
            "on_order_book_deltas",
            "on_trade_tick",
            "on_event",
            "_process_market_update",
            "_place_bid_order",
            "_place_ask_order",
        ]

        for method_name in required_methods:
            has_method = hasattr(TestSingleMakerStrategy, method_name)
            all_passed = all_passed and print_check(
                has_method,
                f"Method '{method_name}' exists",
            )

        return all_passed

    except Exception as e:
        print_check(False, f"Method validation failed: {e}")
        return False


def validate_strategy_attributes() -> bool:
    """Validate that strategy has required attributes."""
    print_header("Strategy Attribute Validation")

    try:
        from test_single_maker_strategy import (
            TestSingleMakerStrategy,
            TestSingleMakerStrategyConfig,
        )
        from nautilus_trader.model.identifiers import InstrumentId

        all_passed = True

        # Create a test strategy instance
        config = TestSingleMakerStrategyConfig(
            instrument_id=InstrumentId.from_str("SOLUSDT-LINEAR.BYBIT"),
        )

        # Note: We can't fully instantiate without a proper trader/portfolio
        # Just check the __init__ sets up expected attributes
        expected_attrs = [
            "instrument",
            "book_type",
            "mid_price_history",
            "current_ma_mid",
            "active_bid_order",
            "active_ask_order",
            "last_bid_quote_mid",
            "last_ask_quote_mid",
            "position_base",
            "cash_balance_quote",
            "ma_window_ns",
        ]

        # Check attributes are mentioned in __init__
        import inspect

        init_source = inspect.getsource(TestSingleMakerStrategy.__init__)

        for attr in expected_attrs:
            has_attr = f"self.{attr}" in init_source
            all_passed = all_passed and print_check(
                has_attr,
                f"Attribute '{attr}' initialized",
            )

        return all_passed

    except Exception as e:
        print_check(False, f"Attribute validation failed: {e}")
        return False


def validate_spec_compliance() -> bool:
    """Validate compliance with benchmark specification."""
    print_header("Benchmark Spec Compliance")

    all_passed = True

    # Check that key logic patterns are present in the implementation
    try:
        import inspect

        from test_single_maker_strategy import TestSingleMakerStrategy

        strategy_source = inspect.getsource(TestSingleMakerStrategy)

        # Key patterns that should be in the implementation
        patterns = [
            ("mid-price calculation", "(best_bid + best_ask)"),
            ("MA calculation", "sum(price for _, price in"),
            ("BPS conversion", "/ 10000"),
            ("Position limit check", "max_long_position"),
            ("Budget check", "cash_balance"),
            ("Order placement", "order_factory.limit"),
            ("Order cancellation", "cancel_order"),
            ("Fill handling", "OrderFilled"),
        ]

        for description, pattern in patterns:
            has_pattern = pattern in strategy_source
            all_passed = all_passed and print_check(
                has_pattern,
                f"{description} implemented",
            )

    except Exception as e:
        print_check(False, f"Spec compliance check failed: {e}")
        return False

    return all_passed


def main() -> int:
    """Run all validation checks."""
    print(f"\n{BLUE}TestSingleMakerStrategy Implementation Validator{RESET}")
    print(f"{BLUE}Nautilus Trader Platform{RESET}")

    all_passed = True
    all_passed = all_passed and validate_files()
    all_passed = all_passed and validate_imports()
    all_passed = all_passed and validate_config()
    all_passed = all_passed and validate_strategy_methods()
    all_passed = all_passed and validate_strategy_attributes()
    all_passed = all_passed and validate_spec_compliance()

    # Print summary
    print_header("Validation Summary")

    if all_passed:
        print(f"{GREEN}✓ All validation checks passed!{RESET}")
        print(f"\n{GREEN}The implementation appears to meet all requirements.{RESET}")
        print(f"\n{YELLOW}Next steps:{RESET}")
        print("1. Record market data (run_6hr_recording.py)")
        print("2. Run backtest (python3 run_backtest.py)")
        print("3. Review results and compare with other platforms")
        return 0
    else:
        print(f"{RED}✗ Some validation checks failed.{RESET}")
        print(f"\n{YELLOW}Please review the errors above and fix the implementation.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
