#!/usr/bin/env python3
"""
Backtest Runner with On-the-Fly Data Conversion
Converts pandas parquet data to Nautilus objects during loading
"""

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
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.currencies import Currency
from nautilus_trader.model.data import BookOrder
from nautilus_trader.model.data import OrderBookDelta
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from test_single_maker_strategy import TestSingleMakerStrategy
from test_single_maker_strategy import TestSingleMakerStrategyConfig


def load_config(config_path: str = "test_single_maker_config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def convert_order_book_deltas(
    df: pd.DataFrame,
    instrument_id: InstrumentId,
) -> list[OrderBookDelta]:
    """
    Convert pandas DataFrame to Nautilus OrderBookDelta objects.

    DataFrame columns: action, order_id, price, side, size, timestamp
    """
    deltas = []

    print(f"Converting {len(df)} order book deltas...")

    for idx, row in df.iterrows():
        if idx % 100000 == 0:
            print(f"  Progress: {idx}/{len(df)} ({100*idx/len(df):.1f}%)")

        # Convert action string to BookAction enum
        action_str = row['action'].upper()
        if action_str == 'ADD':
            action = BookAction.ADD
        elif action_str == 'UPDATE':
            action = BookAction.UPDATE
        elif action_str == 'DELETE':
            action = BookAction.DELETE
        elif action_str == 'CLEAR':
            action = BookAction.CLEAR
        else:
            print(f"WARNING: Unknown action '{action_str}' at row {idx}, skipping")
            continue

        # Convert side string to OrderSide enum
        side_str = row['side'].upper()
        if side_str == 'BUY':
            side = OrderSide.BUY
        elif side_str == 'SELL':
            side = OrderSide.SELL
        else:
            # For CLEAR actions, side might be empty
            if action == BookAction.CLEAR:
                side = OrderSide.BUY  # Dummy value for CLEAR
            else:
                print(f"WARNING: Unknown side '{side_str}' at row {idx}, skipping")
                continue

        # Convert timestamp to nanoseconds
        ts_event = dt_to_unix_nanos(pd.Timestamp(row['timestamp']))
        ts_init = ts_event

        # Create BookOrder (required for non-CLEAR actions)
        if action != BookAction.CLEAR:
            # Format price with 3 decimals to match instrument precision
            price_str = f"{row['price']:.3f}"
            size_str = f"{row['size']:.1f}"

            order = BookOrder(
                side=side,
                price=Price.from_str(price_str),
                size=Quantity.from_str(size_str),
                order_id=int(row['order_id']),
            )
        else:
            # For CLEAR actions, order can be None or dummy
            order = BookOrder(
                side=OrderSide.BUY,
                price=Price.from_str("0"),
                size=Quantity.from_str("0"),
                order_id=0,
            )

        # Create OrderBookDelta
        delta = OrderBookDelta(
            instrument_id=instrument_id,
            action=action,
            order=order,
            flags=0,
            sequence=idx,
            ts_event=ts_event,
            ts_init=ts_init,
        )

        deltas.append(delta)

    print(f"Converted {len(deltas)} order book deltas successfully")
    return deltas


def convert_trade_ticks(
    df: pd.DataFrame,
    instrument_id: InstrumentId,
) -> list[TradeTick]:
    """
    Convert pandas DataFrame to Nautilus TradeTick objects.

    DataFrame columns: price, side, size, timestamp, trade_id
    """
    trades = []

    print(f"Converting {len(df)} trade ticks...")

    for idx, row in df.iterrows():
        if idx % 50000 == 0:
            print(f"  Progress: {idx}/{len(df)} ({100*idx/len(df):.1f}%)")

        # Convert side string to AggressorSide enum
        side_str = row['side'].upper()
        if side_str in ('BUY', 'BUYER'):
            aggressor_side = AggressorSide.BUYER
        elif side_str in ('SELL', 'SELLER'):
            aggressor_side = AggressorSide.SELLER
        else:
            print(f"WARNING: Unknown side '{side_str}' at row {idx}, skipping")
            continue

        # Convert timestamp to nanoseconds
        ts_event = dt_to_unix_nanos(pd.Timestamp(row['timestamp']))
        ts_init = ts_event

        # Format price and size with proper precision
        price_str = f"{row['price']:.3f}"
        size_str = f"{row['size']:.1f}"

        # Create TradeTick
        trade = TradeTick(
            instrument_id=instrument_id,
            price=Price.from_str(price_str),
            size=Quantity.from_str(size_str),
            aggressor_side=aggressor_side,
            trade_id=TradeId(str(row['trade_id'])),
            ts_event=ts_event,
            ts_init=ts_init,
        )

        trades.append(trade)

    print(f"Converted {len(trades)} trade ticks successfully")
    return trades


def run_backtest(config_path: str = "test_single_maker_config.yaml") -> None:
    """
    Run backtest with on-the-fly data conversion.
    """
    # Load configuration
    config = load_config(config_path)
    strategy_config = config["strategy"]
    backtest_config = config["backtest"]
    fill_model_config = config.get("fill_model", {})

    print("=" * 80)
    print("TestSingleMakerStrategy Backtest (with Data Conversion)")
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
        base_currency=None,
        starting_balances=starting_balances,
        fill_model=fill_model,
        book_type=BookType.L2_MBP,
    )

    # Load data from parquet files
    data_path = Path(backtest_config["data_path"]).expanduser()
    if not data_path.exists():
        print(f"ERROR: Data path does not exist: {data_path}")
        sys.exit(1)

    print(f"\nLoading data from: {data_path}")

    # Get instrument ID from config
    instrument_id_str = strategy_config["instrument_id"]
    instrument_id = InstrumentId.from_str(instrument_id_str)

    # Load instrument from catalog (this still works)
    try:
        catalog = ParquetDataCatalog(str(data_path))
        instruments = catalog.instruments()
        if not instruments:
            print("ERROR: No instruments found in catalog")
            sys.exit(1)

        instrument = None
        for inst in instruments:
            if str(inst.id) == instrument_id_str:
                instrument = inst
                break

        if instrument is None:
            print(f"ERROR: Instrument {instrument_id_str} not found in catalog")
            print(f"Available instruments: {[str(i.id) for i in instruments]}")
            sys.exit(1)

        print(f"Loaded instrument: {instrument.id}")
        engine.add_instrument(instrument)

    except Exception as e:
        print(f"ERROR loading instrument: {e}")
        sys.exit(1)

    # Load and convert order book deltas from pandas parquet
    deltas_path = data_path / "order_book_deltas" / instrument_id_str / "order_book_deltas.parquet"
    if deltas_path.exists():
        print(f"\nLoading order book deltas from: {deltas_path}")
        df_deltas = pd.read_parquet(deltas_path)
        print(f"Loaded {len(df_deltas)} rows from parquet")

        # Convert to Nautilus objects
        deltas = convert_order_book_deltas(df_deltas, instrument_id)

        if deltas:
            print(f"Adding {len(deltas)} order book deltas to engine...")
            engine.add_data(deltas)
        else:
            print("WARNING: No order book deltas converted")
    else:
        print(f"WARNING: Order book deltas file not found: {deltas_path}")

    # Load and convert trade ticks from pandas parquet
    trades_path = data_path / "trade_ticks" / instrument_id_str / "trade_ticks.parquet"
    if trades_path.exists():
        print(f"\nLoading trade ticks from: {trades_path}")
        df_trades = pd.read_parquet(trades_path)
        print(f"Loaded {len(df_trades)} rows from parquet")

        # Convert to Nautilus objects
        trades = convert_trade_ticks(df_trades, instrument_id)

        if trades:
            print(f"Adding {len(trades)} trade ticks to engine...")
            engine.add_data(trades)
        else:
            print("WARNING: No trade ticks converted")
    else:
        print(f"WARNING: Trade ticks file not found: {trades_path}")

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
        "display.max_rows", 100,
        "display.max_columns", None,
        "display.width", 300,
    ):
        print(engine.trader.generate_account_report(venue))

    print("\n" + "=" * 80)
    print("ORDER FILLS REPORT")
    print("=" * 80)
    with pd.option_context(
        "display.max_rows", 100,
        "display.max_columns", None,
        "display.width", 300,
    ):
        print(engine.trader.generate_order_fills_report())

    print("\n" + "=" * 80)
    print("POSITIONS REPORT")
    print("=" * 80)
    with pd.option_context(
        "display.max_rows", 100,
        "display.max_columns", None,
        "display.width", 300,
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

    # Save reports to files
    output_dir = Path("backtest_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not account.empty:
        account_file = output_dir / f"account_report_{timestamp}.csv"
        account.to_csv(account_file)
        print(f"\nAccount report saved to: {account_file}")

    if not fills.empty:
        fills_file = output_dir / f"fills_report_{timestamp}.csv"
        fills.to_csv(fills_file)
        print(f"Fills report saved to: {fills_file}")

    positions = engine.trader.generate_positions_report()
    if not positions.empty:
        positions_file = output_dir / f"positions_report_{timestamp}.csv"
        positions.to_csv(positions_file)
        print(f"Positions report saved to: {positions_file}")

    # Cleanup
    engine.dispose()


if __name__ == "__main__":
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
