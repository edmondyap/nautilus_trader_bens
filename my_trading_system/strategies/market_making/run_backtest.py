#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
#  Backtest Runner for TestSingleMakerStrategy
#  Part of Quant Trading Platform Benchmark
# -------------------------------------------------------------------------------------------------

import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import Currency
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# Import the strategy
from simple_market_maker import TestSingleMakerStrategy
from simple_market_maker import TestSingleMakerStrategyConfig


def load_config(config_path: str = "test_single_maker_config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_backtest(config_path: str = "test_single_maker_config.yaml") -> None:
    """
    Run backtest for TestSingleMakerStrategy using recorded data.

    Parameters
    ----------
    config_path : str
        Path to the configuration YAML file.

    """
    # Load configuration
    config = load_config(config_path)
    strategy_config = config["strategy"]
    backtest_config = config["backtest"]
    fill_model_config = config.get("fill_model", {})

    print("=" * 80)
    print("TestSingleMakerStrategy Backtest")
    print("=" * 80)
    print(f"Instrument: {strategy_config['instrument_id']}")
    print(f"Spread: {strategy_config['spread_bps']} bps")
    print(f"MA Window: {strategy_config['ma_window_minutes']} minutes")
    print(f"Price Tolerance: {strategy_config['price_tolerance_bps']} bps")
    print(f"Order Size: {strategy_config['order_size_base']} (base)")
    print(f"Max Long Position: {strategy_config['max_long_position']}")
    print(f"Max Short Position: {strategy_config['max_short_position']}")
    print(f"Max Budget: {strategy_config['max_budget_quote']} (quote)")
    print("=" * 80)

    # Configure backtest engine
    engine_config = BacktestEngineConfig(
        trader_id=TraderId("BACKTESTER-001"),
    )

    # Build the backtest engine
    engine = BacktestEngine(config=engine_config)

    # Create fill model
    fill_model = FillModel(
        prob_fill_on_limit=fill_model_config.get("prob_fill_on_limit", 1.0),
        prob_fill_on_stop=fill_model_config.get("prob_fill_on_stop", 0.95),
        prob_slippage=fill_model_config.get("prob_slippage", 0.0),
        random_seed=fill_model_config.get("random_seed", 42),
    )

    # Set up venue
    venue = Venue(backtest_config["venue"])
    account_type = AccountType[backtest_config.get("account_type", "MARGIN")]
    oms_type = OmsType[backtest_config.get("oms_type", "NETTING")]

    # Parse starting balances
    starting_balances = []
    for currency_code, amount in backtest_config["starting_balances"].items():
        currency = Currency.from_str(currency_code)
        starting_balances.append(Money(amount, currency))

    # Add venue to engine
    engine.add_venue(
        venue=venue,
        oms_type=oms_type,
        account_type=account_type,
        base_currency=None,  # Multi-currency account
        starting_balances=starting_balances,
        fill_model=fill_model,
        book_type=BookType.L2_MBP,
    )

    # Load data from catalog
    data_path = Path(backtest_config["data_path"]).expanduser()
    if not data_path.exists():
        print(f"ERROR: Data path does not exist: {data_path}")
        print("Please run the data recorder first to collect market data.")
        sys.exit(1)

    print(f"\nLoading data from: {data_path}")

    try:
        # Initialize catalog
        catalog = ParquetDataCatalog(str(data_path))

        # Get instrument from config
        instrument_id_str = strategy_config["instrument_id"]

        # Load instrument
        instruments = catalog.instruments()
        if not instruments:
            print("ERROR: No instruments found in catalog")
            sys.exit(1)

        instrument = instruments[0]  # Use first instrument
        print(f"Loaded instrument: {instrument.id}")
        engine.add_instrument(instrument)

        # Load order book deltas
        print("Loading order book deltas...")
        deltas = catalog.order_book_deltas(instrument_ids=[str(instrument.id)])
        if deltas:
            print(f"Loaded {len(deltas)} order book deltas")
            engine.add_data(deltas)
        else:
            print("WARNING: No order book deltas found")

        # Load trades
        print("Loading trades...")
        trades = catalog.trade_ticks(instrument_ids=[str(instrument.id)])
        if trades:
            print(f"Loaded {len(trades)} trades")
            engine.add_data(trades)
        else:
            print("WARNING: No trades found")

    except Exception as e:
        print(f"ERROR loading data: {e}")
        print("\nPlease ensure you have recorded data using:")
        print("  python benchmark/nautilus_trader/native_recorder/run_6hr_recording.py")
        sys.exit(1)

    # Configure strategy
    strategy_cfg = TestSingleMakerStrategyConfig(
        instrument_id=instrument.id,
        spread_bps=strategy_config["spread_bps"],
        ma_window_minutes=strategy_config["ma_window_minutes"],
        price_tolerance_bps=strategy_config["price_tolerance_bps"],
        order_size_base=Decimal(str(strategy_config["order_size_base"])),
        max_long_position=Decimal(str(strategy_config["max_long_position"])),
        max_short_position=Decimal(str(strategy_config["max_short_position"])),
        max_budget_quote=Decimal(str(strategy_config["max_budget_quote"])),
        book_type=strategy_config.get("book_type", "L2_MBP"),
    )

    # Instantiate strategy
    strategy = TestSingleMakerStrategy(config=strategy_cfg)
    engine.add_strategy(strategy=strategy)

    print("\nStarting backtest...")
    print("=" * 80)

    # Run the backtest
    start_time = time.time()

    # Parse start/end times if specified
    start_dt = None
    end_dt = None
    if "start_time" in backtest_config:
        start_dt = datetime.fromisoformat(backtest_config["start_time"].replace("Z", "+00:00"))
    if "end_time" in backtest_config:
        end_dt = datetime.fromisoformat(backtest_config["end_time"].replace("Z", "+00:00"))

    engine.run(start=start_dt, end=end_dt)

    elapsed_time = time.time() - start_time

    print("=" * 80)
    print(f"Backtest completed in {elapsed_time:.2f} seconds")
    print("=" * 80)

    # Generate reports
    print("\n" + "=" * 80)
    print("ACCOUNT REPORT")
    print("=" * 80)
    with pd.option_context(
        "display.max_rows",
        100,
        "display.max_columns",
        None,
        "display.width",
        300,
    ):
        print(engine.trader.generate_account_report(venue))

    print("\n" + "=" * 80)
    print("ORDER FILLS REPORT")
    print("=" * 80)
    with pd.option_context(
        "display.max_rows",
        100,
        "display.max_columns",
        None,
        "display.width",
        300,
    ):
        print(engine.trader.generate_order_fills_report())

    print("\n" + "=" * 80)
    print("POSITIONS REPORT")
    print("=" * 80)
    with pd.option_context(
        "display.max_rows",
        100,
        "display.max_columns",
        None,
        "display.width",
        300,
    ):
        print(engine.trader.generate_positions_report())

    # Performance metrics
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)

    account = engine.trader.generate_account_report(venue)
    if not account.empty:
        print(f"Starting Balance: {account.iloc[0]['balance_total']}")
        print(f"Ending Balance: {account.iloc[-1]['balance_total']}")
        pnl = float(account.iloc[-1]["balance_total"]) - float(account.iloc[0]["balance_total"])
        print(f"Total PnL: {pnl:.2f}")
        print(f"PnL %: {pnl / float(account.iloc[0]['balance_total']) * 100:.2f}%")

    fills = engine.trader.generate_order_fills_report()
    if not fills.empty:
        print(f"Total Fills: {len(fills)}")
        print(f"Buy Fills: {len(fills[fills['order_side'] == 'BUY'])}")
        print(f"Sell Fills: {len(fills[fills['order_side'] == 'SELL'])}")

    print("=" * 80)

    # Cleanup
    engine.dispose()


if __name__ == "__main__":
    # Check if config path provided as argument
    config_path = sys.argv[1] if len(sys.argv) > 1 else "test_single_maker_config.yaml"

    try:
        run_backtest(config_path)
    except KeyboardInterrupt:
        print("\n\nBacktest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
