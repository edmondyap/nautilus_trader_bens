"""
Configuration Management - Nautilus Trader Data Recorder

Trading Engines Project - Benchmark/Evaluation Code
Location: benchmark/nautilus_trader/native_recorder/config.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09

Builds TradingNodeConfig for the native data recorder using Nautilus configuration classes.

Architecture:
- ✅ NATIVE: Uses TradingNodeConfig, BybitDataClientConfig (Nautilus classes)
- ❌ CUSTOM: Builder pattern for easy configuration
- ❌ CUSTOM: Validation logic for our use case

Upstream: nautilus_trader/ (DO NOT MODIFY)
Custom: This file (benchmark/evaluation code)
"""

from pathlib import Path
from typing import Any

from nautilus_trader.core.nautilus_pyo3 import BybitProductType
from nautilus_trader.adapters.bybit.config import BybitDataClientConfig
from nautilus_trader.config import InstrumentProviderConfig, TradingNodeConfig
from nautilus_trader.model.identifiers import TraderId

from .strategy import NativeDataRecorderConfig, NativeDataRecorderStrategy


class RecorderConfigBuilder:
    """
    Builder for TradingNode configuration.

    Simplifies creating TradingNodeConfig for data recording use case.

    Examples
    --------
    >>> builder = RecorderConfigBuilder(trader_id="RECORDER-001")
    >>> builder.add_instruments(["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"])
    >>> builder.set_output_dir("./data/recordings")
    >>> builder.set_duration(300)  # 5 minutes
    >>> node_config = builder.build()
    """

    def __init__(self, trader_id: str = "DATA-RECORDER-001"):
        self.trader_id = TraderId(trader_id)
        self.instruments: list[str] = []
        self.output_dir: str = "data/recordings"
        self.flush_interval: int = 60
        self.record_quotes: bool = True  # Now works in public-only mode (with use_env_fallback=False)
        self.record_trades: bool = True  # Works in public-only mode
        self.record_orderbook: bool = False  # Disabled by default (can be enabled with enable_orderbook())
        self.orderbook_depth: int = 50
        self.connection_timeout: int = 120
        self.run_duration: int | None = None

        # Bybit config
        self.api_key: str | None = None
        self.api_secret: str | None = None
        self.testnet: bool = False
        self._use_env_fallback: bool = True

    def add_instrument(self, instrument_id: str) -> "RecorderConfigBuilder":
        """Add an instrument to record."""
        if instrument_id not in self.instruments:
            self.instruments.append(instrument_id)
        return self

    def add_instruments(self, instrument_ids: list[str]) -> "RecorderConfigBuilder":
        """Add multiple instruments to record."""
        for instrument_id in instrument_ids:
            self.add_instrument(instrument_id)
        return self

    def set_output_dir(self, output_dir: str | Path) -> "RecorderConfigBuilder":
        """Set output directory for parquet files."""
        self.output_dir = str(output_dir)
        return self

    def set_flush_interval(self, seconds: int) -> "RecorderConfigBuilder":
        """Set flush interval (seconds)."""
        self.flush_interval = seconds
        return self

    def enable_orderbook(self, depth: int = 50) -> "RecorderConfigBuilder":
        """Enable order book delta recording."""
        self.record_orderbook = True
        self.orderbook_depth = depth
        return self

    def disable_quotes(self) -> "RecorderConfigBuilder":
        """Disable quote tick recording."""
        self.record_quotes = False
        return self

    def set_duration(self, seconds: int) -> "RecorderConfigBuilder":
        """Set session duration (auto-stop after N seconds)."""
        self.run_duration = seconds
        return self

    def set_bybit_credentials(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ) -> "RecorderConfigBuilder":
        """Set Bybit API credentials (not required for public data)."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        return self

    def enable_public_only_mode(self) -> "RecorderConfigBuilder":
        """
        Disable environment variable fallback for credentials.

        Forces public-only mode even if BYBIT_API_KEY env vars exist.
        This prevents accidental credential usage for data recording.

        Returns
        -------
        RecorderConfigBuilder
            The builder instance for method chaining.

        """
        self._use_env_fallback = False
        # Leave api_key and api_secret as None, but set use_env_fallback=False
        # This will result in Rust client having credential=None
        # Fee rate lookup will fail with MissingCredentials (handled gracefully)
        return self

    def validate(self) -> None:
        """
        Validate configuration.

        Raises
        ------
        ValueError
            If configuration is invalid
        """
        if not self.instruments:
            raise ValueError("Must specify at least one instrument")

        # Validate instrument format
        for inst in self.instruments:
            if ".BYBIT" not in inst:
                raise ValueError(
                    f"Invalid instrument ID: {inst} (must include .BYBIT venue)"
                )

        if self.flush_interval <= 0:
            raise ValueError(
                f"flush_interval must be > 0, got {self.flush_interval}"
            )

        if self.orderbook_depth <= 0:
            raise ValueError(
                f"orderbook_depth must be > 0, got {self.orderbook_depth}"
            )

        if self.run_duration is not None and self.run_duration <= 0:
            raise ValueError(
                f"run_duration must be > 0 or None, got {self.run_duration}"
            )

    def build(self) -> tuple[TradingNodeConfig, NativeDataRecorderConfig]:
        """
        Build TradingNodeConfig and StrategyConfig.

        Returns
        -------
        tuple[TradingNodeConfig, NativeDataRecorderConfig]
            (node_config, strategy_config) ready for TradingNode initialization

        Raises
        ------
        ValueError
            If configuration is invalid
        """
        # Validate first
        self.validate()

        # Create strategy config
        strategy_config = NativeDataRecorderConfig(
            instrument_ids=self.instruments,
            output_dir=self.output_dir,
            flush_interval_seconds=self.flush_interval,
            record_quotes=self.record_quotes,
            record_trades=self.record_trades,
            record_orderbook=self.record_orderbook,
            orderbook_depth=self.orderbook_depth,
            connection_timeout_seconds=self.connection_timeout,
            run_duration_seconds=self.run_duration,
        )

        # Create instrument provider config to enable instrument loading
        # This is CRITICAL: without this, the instrument provider won't load instruments
        # and we'll get "No loading configured" warning
        instrument_provider_config = InstrumentProviderConfig(
            load_all=True,  # Load all SPOT instruments via public API
            log_warnings=True,
        )

        # Create Bybit data client config
        bybit_config = BybitDataClientConfig(
            api_key=self.api_key,
            api_secret=self.api_secret,
            product_types=[BybitProductType.SPOT, BybitProductType.LINEAR, BybitProductType.INVERSE],  # All product types for benchmark
            testnet=self.testnet,
            instrument_provider=instrument_provider_config,
            use_env_fallback=self._use_env_fallback,  # FIX: Actually pass the parameter (was missing)
            # Note: When use_env_fallback=False, forces public-only mode even if env vars exist
            # Fee rate lookup will fail gracefully with MissingCredentials error
        )

        # Create trading node config
        node_config = TradingNodeConfig(
            trader_id=self.trader_id,
            data_clients={
                "BYBIT": bybit_config,
            },
            timeout_connection=30.0,
            timeout_reconciliation=10.0,
            timeout_portfolio=10.0,
            timeout_disconnection=10.0,
        )

        return node_config, strategy_config


def load_config_from_yaml(
    yaml_path: str | Path
) -> tuple[TradingNodeConfig, NativeDataRecorderConfig]:
    """
    Load configuration from YAML file.

    Parameters
    ----------
    yaml_path : str | Path
        Path to YAML configuration file

    Returns
    -------
    tuple[TradingNodeConfig, NativeDataRecorderConfig]
        (node_config, strategy_config) ready for use

    Raises
    ------
    FileNotFoundError
        If YAML file does not exist
    ValueError
        If configuration is invalid

    Examples
    --------
    >>> node_config, strategy_config = load_config_from_yaml(
    ...     "config_templates/bybit_spot_recording.yaml"
    ... )
    """
    import yaml

    yaml_path = Path(yaml_path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"Config file not found: {yaml_path}")

    with open(yaml_path, "r") as f:
        config_dict = yaml.safe_load(f)

    builder = RecorderConfigBuilder(
        trader_id=config_dict.get("trader_id", "DATA-RECORDER-001")
    )

    # Strategy config
    strategy = config_dict.get("strategy", {})
    builder.add_instruments(strategy.get("instruments", []))
    builder.set_output_dir(strategy.get("output_dir", "data/recordings"))
    builder.set_flush_interval(strategy.get("flush_interval_seconds", 60))

    if not strategy.get("record_quotes", True):
        builder.disable_quotes()

    if strategy.get("record_orderbook", False):
        builder.enable_orderbook(depth=strategy.get("orderbook_depth", 50))

    duration = strategy.get("run_duration_seconds")
    if duration:
        builder.set_duration(duration)

    # Bybit config
    bybit = config_dict.get("bybit", {})
    if bybit.get("api_key") and bybit.get("api_secret"):
        builder.set_bybit_credentials(
            api_key=bybit["api_key"],
            api_secret=bybit["api_secret"],
            testnet=bybit.get("testnet", False)
        )

    return builder.build()


def create_quick_config(
    instruments: list[str],
    output_dir: str = "data/recordings",
    duration_seconds: int | None = None,
    with_orderbook: bool = False,
) -> tuple[TradingNodeConfig, NativeDataRecorderConfig]:
    """
    Quick configuration builder for common use cases.

    Parameters
    ----------
    instruments : list[str]
        Instrument IDs (e.g., ["SOLUSDT-SPOT.BYBIT"])
    output_dir : str, default="data/recordings"
        Output directory
    duration_seconds : int | None, default=None
        Auto-stop duration (None = run forever)
    with_orderbook : bool, default=False
        Record order book deltas

    Returns
    -------
    tuple[TradingNodeConfig, NativeDataRecorderConfig]
        (node_config, strategy_config) ready for use

    Raises
    ------
    ValueError
        If configuration is invalid

    Examples
    --------
    >>> # Record SOLUSDT for 5 minutes
    >>> node_cfg, strat_cfg = create_quick_config(
    ...     ["SOLUSDT-SPOT.BYBIT"],
    ...     duration_seconds=300
    ... )

    >>> # Record multiple symbols with orderbook
    >>> node_cfg, strat_cfg = create_quick_config(
    ...     ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
    ...     with_orderbook=True
    ... )
    """
    builder = RecorderConfigBuilder()
    builder.add_instruments(instruments)
    builder.set_output_dir(output_dir)

    if duration_seconds:
        builder.set_duration(duration_seconds)

    if with_orderbook:
        builder.enable_orderbook()

    return builder.build()
