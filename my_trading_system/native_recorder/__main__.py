"""
Native Data Recorder - Main Entry Point

My Trading System - Production Code
Location: my_trading_system/native_recorder/__main__.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09

Main entry point for running the native data recorder.

Usage:
    python -m my_trading_system.native_recorder --config path/to/config.yaml
    python -m my_trading_system.native_recorder --instruments SOLUSDT-SPOT.BYBIT --duration 300

Upstream: nautilus_trader/ (DO NOT MODIFY)
Custom: This module (production data recording tool)
"""

import argparse
import signal
import sys
from pathlib import Path

from nautilus_trader.adapters.bybit.factories import BybitLiveDataClientFactory
from nautilus_trader.live.node import TradingNode

from my_trading_system.native_recorder.config import (
    RecorderConfigBuilder,
    load_config_from_yaml,
)
from my_trading_system.native_recorder.strategy import (
    NativeDataRecorderStrategy,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Nautilus Trader Native Data Recorder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record using YAML config
  python -m my_trading_system.native_recorder --config configs/recording/bybit_spot_recording.yaml

  # Quick recording (default 5 minutes)
  python -m my_trading_system.native_recorder --instruments SOLUSDT-SPOT.BYBIT

  # Custom duration and multiple symbols
  python -m my_trading_system.native_recorder \\
    --instruments SOLUSDT-SPOT.BYBIT BTCUSDT-SPOT.BYBIT \\
    --duration 600 \\
    --output data/my_recording

  # With order book (L2 depth 50)
  python -m my_trading_system.native_recorder \\
    --instruments SOLUSDT-SPOT.BYBIT \\
    --with-orderbook \\
    --orderbook-depth 50
        """,
    )

    # Config file
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to YAML configuration file",
    )

    # Quick config arguments
    parser.add_argument(
        "--instruments",
        "-i",
        type=str,
        nargs="+",
        help="Instrument IDs to record (e.g., SOLUSDT-SPOT.BYBIT)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/recordings",
        help="Output directory (default: data/recordings)",
    )

    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=300,
        help="Recording duration in seconds (default: 300)",
    )

    parser.add_argument(
        "--with-orderbook",
        action="store_true",
        help="Record order book deltas (default: quotes only)",
    )

    parser.add_argument(
        "--orderbook-depth",
        type=int,
        default=50,
        help="Order book depth if --with-orderbook enabled (default: 50)",
    )

    parser.add_argument(
        "--flush-interval",
        type=int,
        default=60,
        help="Flush interval in seconds (default: 60)",
    )

    parser.add_argument(
        "--trader-id",
        type=str,
        default="DATA-RECORDER-001",
        help="Trader ID (default: DATA-RECORDER-001)",
    )

    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Load configuration
    if args.config:
        print(f"Loading configuration from: {args.config}")
        node_config, strategy_config = load_config_from_yaml(args.config)

    elif args.instruments:
        print(f"Creating quick configuration for {len(args.instruments)} instrument(s)")

        # Build config
        builder = RecorderConfigBuilder(trader_id=args.trader_id)
        builder.add_instruments(args.instruments)
        builder.set_output_dir(args.output)
        builder.set_duration(args.duration)
        builder.set_flush_interval(args.flush_interval)

        if args.with_orderbook:
            builder.enable_orderbook(depth=args.orderbook_depth)

        node_config, strategy_config = builder.build()

    else:
        parser.print_help()
        print("\nError: Must specify either --config or --instruments")
        sys.exit(1)

    # Create strategy
    strategy = NativeDataRecorderStrategy(config=strategy_config)

    # Create trading node
    print("Initializing TradingNode...")
    node = TradingNode(config=node_config)

    # Register data client factory
    node.add_data_client_factory("BYBIT", BybitLiveDataClientFactory)

    # Add strategy
    node.trader.add_strategy(strategy)

    # Build node
    print("Building TradingNode...")
    node.build()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\n\nReceived signal, stopping gracefully...")
        node.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run
    print("\n" + "=" * 80)
    print("STARTING DATA RECORDING SESSION")
    print("=" * 80)
    print(f"Instruments: {strategy_config.instrument_ids}")
    print(f"Output: {strategy_config.output_dir}")
    print(f"Duration: {strategy_config.run_duration_seconds}s" if strategy_config.run_duration_seconds else "Duration: Unlimited (Ctrl+C to stop)")
    print(f"Recording quotes: {strategy_config.record_quotes}")
    print(f"Recording orderbook: {strategy_config.record_orderbook}")
    if strategy_config.record_orderbook:
        print(f"Orderbook depth: {strategy_config.orderbook_depth}")
    print(f"Flush interval: {strategy_config.flush_interval_seconds}s")
    print("=" * 80)
    print("\nPress Ctrl+C to stop recording gracefully\n")

    try:
        node.run()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received, stopping...")
    finally:
        # Ensure cleanup
        if node.trader.is_running:
            node.stop()

    print("\n" + "=" * 80)
    print("RECORDING SESSION COMPLETE")
    print("=" * 80)
    print(f"Check output directory: {strategy_config.output_dir}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
