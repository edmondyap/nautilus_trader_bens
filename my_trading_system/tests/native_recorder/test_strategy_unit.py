"""
Unit Tests for NativeDataRecorderStrategy

Tests strategy methods with mocks for data buffering, validation, and persistence.

Location: benchmark/nautilus_trader/tests/test_strategy_unit.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
from decimal import Decimal
from tempfile import TemporaryDirectory
import time
import json
from datetime import datetime

import pandas as pd

from nautilus_trader.model.data import QuoteTick, OrderBookDeltas
from nautilus_trader.model.identifiers import InstrumentId
from my_trading_system.native_recorder.strategy import (
    NativeDataRecorderConfig,
    NativeDataRecorderStrategy,
)


class TestNativeDataRecorderConfigValidation:
    """Tests for NativeDataRecorderConfig validation."""

    def test_config_valid_initialization(self):
        """Test valid config initialization."""
        config = NativeDataRecorderConfig(
            instrument_ids=["SOLUSDT-SPOT.BYBIT"],
            output_dir="data/test",
        )

        assert config.instrument_ids == ["SOLUSDT-SPOT.BYBIT"]
        assert config.output_dir == "data/test"
        assert config.flush_interval_seconds == 60
        assert config.record_quotes is True
        assert config.record_orderbook is True

    def test_config_with_all_parameters(self):
        """Test config with all parameters."""
        config = NativeDataRecorderConfig(
            instrument_ids=["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
            output_dir="data/custom",
            flush_interval_seconds=30,
            record_quotes=False,
            record_orderbook=True,
            orderbook_depth=100,
            connection_timeout_seconds=240,
            run_duration_seconds=600,
        )

        assert config.instrument_ids == ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        assert config.output_dir == "data/custom"
        assert config.flush_interval_seconds == 30
        assert config.record_quotes is False
        assert config.record_orderbook is True
        assert config.orderbook_depth == 100
        assert config.connection_timeout_seconds == 240
        assert config.run_duration_seconds == 600


class TestNativeDataRecorderStrategyInit:
    """Tests for strategy initialization."""

    def test_strategy_init_valid_config(self):
        """Test strategy initializes with valid config."""
        config = NativeDataRecorderConfig(
            instrument_ids=["SOLUSDT-SPOT.BYBIT"]
        )

        strategy = NativeDataRecorderStrategy(config)

        assert strategy.config == config
        assert strategy.quote_ticks_data == {}
        assert strategy.order_book_deltas_data == {}
        assert strategy.quote_count == 0
        assert strategy.delta_count == 0
        assert strategy.last_data_time == 0.0
        assert strategy.connection_warnings == 0
        assert strategy.order_books == {}

    def test_strategy_init_empty_instruments_raises_error(self):
        """Test strategy initialization fails with empty instruments."""
        config = NativeDataRecorderConfig(instrument_ids=[])

        with pytest.raises(ValueError, match="Must specify at least one instrument_id"):
            NativeDataRecorderStrategy(config)

    def test_strategy_init_multiple_instruments(self):
        """Test strategy initializes with multiple instruments."""
        instruments = ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        config = NativeDataRecorderConfig(instrument_ids=instruments)

        strategy = NativeDataRecorderStrategy(config)

        assert strategy.config.instrument_ids == instruments


class TestNativeDataRecorderStrategyValidation:
    """Tests for quote validation methods."""

    def test_validate_quote_valid(self):
        """Test valid quote passes validation."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        quote = Mock(spec=QuoteTick)
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("101.0")

        assert strategy._validate_quote(quote) is True

    def test_validate_quote_zero_bid_price(self):
        """Test quote with zero bid price fails validation."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        quote = Mock(spec=QuoteTick)
        quote.bid_price = Decimal("0")
        quote.ask_price = Decimal("101.0")

        assert strategy._validate_quote(quote) is False

    def test_validate_quote_negative_ask_price(self):
        """Test quote with negative ask price fails validation."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        quote = Mock(spec=QuoteTick)
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("-1.0")

        assert strategy._validate_quote(quote) is False

    def test_validate_quote_crossed_spread(self):
        """Test quote with crossed spread fails validation."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        quote = Mock(spec=QuoteTick)
        quote.bid_price = Decimal("101.0")
        quote.ask_price = Decimal("100.0")

        assert strategy._validate_quote(quote) is False

    def test_validate_quote_equal_bid_ask(self):
        """Test quote with bid=ask fails validation (crossed spread)."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        quote = Mock(spec=QuoteTick)
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("100.0")

        assert strategy._validate_quote(quote) is False


class TestNativeDataRecorderStrategyDataBuffering:
    """Tests for quote and delta buffering."""

    def test_store_quote_tick_new_instrument(self):
        """Test storing quote tick for new instrument."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        quote = Mock(spec=QuoteTick)
        quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
        quote.ts_event = 1699526400000000000  # nanoseconds
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("101.0")
        quote.bid_size = Decimal("1000.0")
        quote.ask_size = Decimal("1000.0")

        strategy._store_quote_tick(quote)

        assert "SOLUSDT-SPOT.BYBIT" in strategy.quote_ticks_data
        assert len(strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"]) == 1

        stored = strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"][0]
        assert stored["bid_price"] == 100.0
        assert stored["ask_price"] == 101.0
        assert stored["bid_size"] == 1000.0
        assert stored["ask_size"] == 1000.0

    def test_store_multiple_quote_ticks(self):
        """Test storing multiple quote ticks."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        for i in range(5):
            quote = Mock(spec=QuoteTick)
            quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
            quote.ts_event = 1699526400000000000 + i * 1000000000  # nanoseconds
            quote.bid_price = Decimal(f"{100.0 + i}")
            quote.ask_price = Decimal(f"{101.0 + i}")
            quote.bid_size = Decimal("1000.0")
            quote.ask_size = Decimal("1000.0")

            strategy._store_quote_tick(quote)

        assert len(strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"]) == 5

    def test_store_order_book_delta_new_instrument(self):
        """Test storing order book delta for new instrument."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        delta = Mock()
        delta.ts_event = 1699526400000000000  # nanoseconds
        delta.action = Mock(name="ADD")
        delta.order = Mock()
        delta.order.side = Mock(name="BUY")
        delta.order.price = Decimal("100.0")
        delta.order.size = Decimal("500.0")
        delta.order.order_id = "order_123"

        instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
        strategy._store_order_book_delta(delta, instrument_id)

        assert "SOLUSDT-SPOT.BYBIT" in strategy.order_book_deltas_data
        assert len(strategy.order_book_deltas_data["SOLUSDT-SPOT.BYBIT"]) == 1

        stored = strategy.order_book_deltas_data["SOLUSDT-SPOT.BYBIT"][0]
        assert stored["action"] == "ADD"
        assert stored["side"] == "BUY"
        assert stored["price"] == 100.0
        assert stored["size"] == 500.0
        assert stored["order_id"] == "order_123"

    def test_store_multiple_deltas(self):
        """Test storing multiple order book deltas."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")

        for i in range(10):
            delta = Mock()
            delta.ts_event = 1699526400000000000 + i * 1000000000
            delta.action = Mock(name="ADD" if i < 5 else "DELETE")
            delta.order = Mock()
            delta.order.side = Mock(name="BUY" if i % 2 == 0 else "SELL")
            delta.order.price = Decimal(f"{100.0 + i}")
            delta.order.size = Decimal("100.0")
            delta.order.order_id = f"order_{i}"

            strategy._store_order_book_delta(delta, instrument_id)

        assert len(strategy.order_book_deltas_data["SOLUSDT-SPOT.BYBIT"]) == 10

    def test_store_delta_multiple_instruments(self):
        """Test storing deltas for multiple instruments."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        for instrument_str in ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]:
            instrument_id = InstrumentId.from_str(instrument_str)

            delta = Mock()
            delta.ts_event = 1699526400000000000
            delta.action = Mock(name="ADD")
            delta.order = Mock()
            delta.order.side = Mock(name="BUY")
            delta.order.price = Decimal("100.0")
            delta.order.size = Decimal("500.0")
            delta.order.order_id = "order_123"

            strategy._store_order_book_delta(delta, instrument_id)

        assert len(strategy.order_book_deltas_data) == 2
        assert "SOLUSDT-SPOT.BYBIT" in strategy.order_book_deltas_data
        assert "BTCUSDT-SPOT.BYBIT" in strategy.order_book_deltas_data


class TestNativeDataRecorderStrategyCallbacks:
    """Tests for on_quote_tick and on_order_book_deltas callbacks."""

    def test_on_quote_tick_valid_quote(self):
        """Test on_quote_tick callback with valid quote."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        quote = Mock(spec=QuoteTick)
        quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
        quote.ts_event = 1699526400000000000
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("101.0")
        quote.bid_size = Decimal("1000.0")
        quote.ask_size = Decimal("1000.0")

        with patch.object(strategy, '_validate_quote', return_value=True):
            strategy.on_quote_tick(quote)

        assert strategy.quote_count == 1
        assert strategy.last_data_time > 0

    def test_on_quote_tick_invalid_quote(self):
        """Test on_quote_tick callback with invalid quote."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        quote = Mock(spec=QuoteTick)

        with patch.object(strategy, '_validate_quote', return_value=False):
            strategy.on_quote_tick(quote)

        assert strategy.quote_count == 0
        assert strategy.last_data_time == 0.0

    def test_on_quote_tick_increments_counter(self):
        """Test on_quote_tick increments quote counter."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        for i in range(5):
            quote = Mock(spec=QuoteTick)
            quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
            quote.ts_event = 1699526400000000000 + i * 1000000000
            quote.bid_price = Decimal("100.0")
            quote.ask_price = Decimal("101.0")
            quote.bid_size = Decimal("1000.0")
            quote.ask_size = Decimal("1000.0")

            with patch.object(strategy, '_validate_quote', return_value=True):
                strategy.on_quote_tick(quote)

        assert strategy.quote_count == 5

    def test_on_order_book_deltas(self):
        """Test on_order_book_deltas callback."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        # Create mock OrderBookDeltas
        instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")

        delta1 = Mock()
        delta1.ts_event = 1699526400000000000
        delta1.action = Mock(name="ADD")
        delta1.order = Mock()
        delta1.order.side = Mock(name="BUY")
        delta1.order.price = Decimal("100.0")
        delta1.order.size = Decimal("500.0")
        delta1.order.order_id = "order_1"

        delta2 = Mock()
        delta2.ts_event = 1699526400000000001
        delta2.action = Mock(name="ADD")
        delta2.order = Mock()
        delta2.order.side = Mock(name="SELL")
        delta2.order.price = Decimal("101.0")
        delta2.order.size = Decimal("500.0")
        delta2.order.order_id = "order_2"

        deltas = Mock(spec=OrderBookDeltas)
        deltas.instrument_id = instrument_id
        deltas.deltas = [delta1, delta2]

        strategy.on_order_book_deltas(deltas)

        assert strategy.delta_count == 2
        assert strategy.last_data_time > 0

    def test_on_order_book_deltas_multiple_calls(self):
        """Test multiple on_order_book_deltas calls."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")

        for batch in range(3):
            deltas_list = []
            for i in range(5):
                delta = Mock()
                delta.ts_event = 1699526400000000000 + batch * 10000000000 + i * 1000000000
                delta.action = Mock(name="ADD")
                delta.order = Mock()
                delta.order.side = Mock(name="BUY")
                delta.order.price = Decimal("100.0")
                delta.order.size = Decimal("100.0")
                delta.order.order_id = f"order_{batch}_{i}"
                deltas_list.append(delta)

            deltas = Mock(spec=OrderBookDeltas)
            deltas.instrument_id = instrument_id
            deltas.deltas = deltas_list

            strategy.on_order_book_deltas(deltas)

        assert strategy.delta_count == 15


class TestNativeDataRecorderStrategyPersistence:
    """Tests for data persistence and metadata generation."""

    def test_save_session_metadata(self):
        """Test session metadata generation."""
        with TemporaryDirectory() as tmpdir:
            config = NativeDataRecorderConfig(
                instrument_ids=["SOLUSDT-SPOT.BYBIT"],
                output_dir=tmpdir
            )
            strategy = NativeDataRecorderStrategy(config)
            strategy.log = Mock()

            # Mock setup
            strategy.session_start_time = time.time() - 60  # 60 seconds ago
            strategy.run_id = "20251109-120000"
            strategy.output_path = Path(tmpdir) / strategy.run_id
            strategy.output_path.mkdir(parents=True, exist_ok=True)
            strategy.quote_count = 100
            strategy.delta_count = 50

            strategy._save_session_metadata()

            metadata_path = strategy.output_path / "session_metadata.json"
            assert metadata_path.exists()

            with open(metadata_path) as f:
                metadata = json.load(f)

            assert metadata["run_id"] == "20251109-120000"
            assert metadata["quote_count"] == 100
            assert metadata["delta_count"] == 50
            assert "duration_seconds" in metadata

    def test_generate_checksums(self):
        """Test checksum generation."""
        with TemporaryDirectory() as tmpdir:
            config = NativeDataRecorderConfig(
                instrument_ids=["SOLUSDT-SPOT.BYBIT"],
                output_dir=tmpdir
            )
            strategy = NativeDataRecorderStrategy(config)
            strategy.log = Mock()

            # Create test parquet files
            strategy.run_id = "20251109-120000"
            strategy.output_path = Path(tmpdir) / strategy.run_id
            strategy.output_path.mkdir(parents=True, exist_ok=True)

            # Create a dummy parquet file
            test_data = {
                "timestamp": pd.date_range("2025-11-09", periods=10, freq="1s", tz="UTC"),
                "value": range(10)
            }
            parquet_dir = strategy.output_path / "test"
            parquet_dir.mkdir(parents=True, exist_ok=True)
            parquet_file = parquet_dir / "test.parquet"
            pd.DataFrame(test_data).to_parquet(parquet_file, index=False)

            strategy._generate_checksums()

            checksum_path = strategy.output_path / "checksums.json"
            assert checksum_path.exists()

            with open(checksum_path) as f:
                checksums = json.load(f)

            assert len(checksums) > 0
            for rel_path, checksum_data in checksums.items():
                assert "sha256" in checksum_data
                assert len(checksum_data["sha256"]) == 64  # SHA256 hex


class TestNativeDataRecorderStrategyHealthCheck:
    """Tests for connection health checking."""

    def test_check_connection_health_no_data(self):
        """Test health check when no data received yet."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        # No data received yet
        strategy.last_data_time = 0.0

        strategy._check_connection_health()

        # Should not log warning if no data yet
        strategy.log.warning.assert_not_called()

    def test_check_connection_health_data_flowing(self):
        """Test health check when data is flowing."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        # Recent data
        strategy.last_data_time = time.time() - 10  # 10 seconds ago
        strategy.connection_timeout_seconds = 120

        strategy._check_connection_health()

        # Should not warn
        strategy.log.warning.assert_not_called()

    def test_check_connection_health_timeout(self):
        """Test health check when data timeout."""
        config = NativeDataRecorderConfig(
            instrument_ids=["SOLUSDT-SPOT.BYBIT"],
            connection_timeout_seconds=30
        )
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        # Data from 60 seconds ago (timeout is 30)
        strategy.last_data_time = time.time() - 60
        strategy.quote_count = 100
        strategy.delta_count = 50
        strategy.connection_warnings = 0

        strategy._check_connection_health()

        # Should warn
        strategy.log.warning.assert_called_once()
        assert strategy.connection_warnings == 1

    def test_check_connection_health_warning_limit(self):
        """Test health check respects warning limit."""
        config = NativeDataRecorderConfig(
            instrument_ids=["SOLUSDT-SPOT.BYBIT"],
            connection_timeout_seconds=30
        )
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        strategy.last_data_time = time.time() - 60
        strategy.quote_count = 100
        strategy.delta_count = 50

        # Already warned 3 times
        strategy.connection_warnings = 3

        strategy._check_connection_health()

        # Should not warn beyond limit
        strategy.log.warning.assert_not_called()

    def test_check_connection_health_recovery(self):
        """Test health check on data recovery."""
        config = NativeDataRecorderConfig(
            instrument_ids=["SOLUSDT-SPOT.BYBIT"],
            connection_timeout_seconds=30
        )
        strategy = NativeDataRecorderStrategy(config)
        strategy.log = Mock()

        # Data flowing now
        strategy.last_data_time = time.time() - 5
        strategy.connection_warnings = 2  # Had previous warnings

        strategy._check_connection_health()

        # Should log recovery
        strategy.log.info.assert_called()
        assert strategy.connection_warnings == 0


class TestNativeDataRecorderStrategyIntegration:
    """Integration tests for strategy components."""

    def test_full_quote_to_storage_workflow(self):
        """Test full workflow: validate -> store -> buffer."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        quote = Mock(spec=QuoteTick)
        quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
        quote.ts_event = 1699526400000000000
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("101.0")
        quote.bid_size = Decimal("1000.0")
        quote.ask_size = Decimal("1000.0")

        # Call on_quote_tick
        strategy.on_quote_tick(quote)

        # Verify: quote stored
        assert strategy.quote_count == 1
        assert "SOLUSDT-SPOT.BYBIT" in strategy.quote_ticks_data
        assert len(strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"]) == 1

    def test_multiple_instruments_workflow(self):
        """Test workflow with multiple instruments."""
        instruments = ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        config = NativeDataRecorderConfig(instrument_ids=instruments)
        strategy = NativeDataRecorderStrategy(config)

        # Store quotes for both instruments
        for inst_str in instruments:
            quote = Mock(spec=QuoteTick)
            quote.instrument_id = InstrumentId.from_str(inst_str)
            quote.ts_event = 1699526400000000000
            quote.bid_price = Decimal("100.0")
            quote.ask_price = Decimal("101.0")
            quote.bid_size = Decimal("1000.0")
            quote.ask_size = Decimal("1000.0")

            strategy.on_quote_tick(quote)

        assert strategy.quote_count == 2
        assert len(strategy.quote_ticks_data) == 2

    def test_timestamp_handling(self):
        """Test proper timestamp conversion from nanoseconds."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        # Nanoseconds timestamp
        ts_ns = 1699526400000000000
        quote = Mock(spec=QuoteTick)
        quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
        quote.ts_event = ts_ns
        quote.bid_price = Decimal("100.0")
        quote.ask_price = Decimal("101.0")
        quote.bid_size = Decimal("1000.0")
        quote.ask_size = Decimal("1000.0")

        strategy._store_quote_tick(quote)

        stored = strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"][0]
        assert isinstance(stored["timestamp"], pd.Timestamp)
        assert stored["timestamp"].tz.zone == "UTC"


class TestDataRecorderConfigValues:
    """Tests for configuration value handling."""

    def test_decimal_to_float_conversion(self):
        """Test Decimal values are converted to float."""
        config = NativeDataRecorderConfig(instrument_ids=["SOLUSDT-SPOT.BYBIT"])
        strategy = NativeDataRecorderStrategy(config)

        quote = Mock(spec=QuoteTick)
        quote.instrument_id = InstrumentId.from_str("SOLUSDT-SPOT.BYBIT")
        quote.ts_event = 1699526400000000000
        quote.bid_price = Decimal("100.123456789")
        quote.ask_price = Decimal("101.987654321")
        quote.bid_size = Decimal("1234.56789")
        quote.ask_size = Decimal("9876.54321")

        strategy._store_quote_tick(quote)

        stored = strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"][0]
        assert isinstance(stored["bid_price"], float)
        assert isinstance(stored["ask_price"], float)
        assert isinstance(stored["bid_size"], float)
        assert isinstance(stored["ask_size"], float)
        assert stored["bid_price"] == pytest.approx(100.123456789, rel=1e-9)
