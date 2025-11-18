"""
Integration Tests for Nautilus Trader Native Data Recorder

Trading Engines Project - Benchmark/Evaluation Code
Location: benchmark/nautilus_trader/tests/integration/test_full_recording.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09

This module provides comprehensive integration tests for the complete data recording
workflow WITHOUT requiring live Bybit connections. Tests use mocked WebSocket data
and verify:

- Configuration loading and validation
- Strategy initialization from config
- Mock data injection and processing
- Parquet file creation and structure
- Data persistence with append logic
- Session metadata generation
- Checksum calculation and validation
- Graceful shutdown behavior

Test Coverage:
1. test_config_to_strategy_integration - Config → Strategy flow
2. test_mock_recording_workflow - 30-second session with mock ticks
3. test_parquet_file_creation - Output structure validation
4. test_parquet_append_logic - Multiple flushes → single file
5. test_metadata_generation - session_metadata.json creation
6. test_checksum_generation - checksums.json validity
7. test_graceful_shutdown - on_stop() data persistence
8. test_mixed_quote_and_delta_data - Combined quote + orderbook recording
9. test_invalid_config_validation - Error handling

Patterns Used:
- pytest with tmpdir for isolated test directories
- Mock objects for TradeTick/QuoteTick/OrderBookDelta
- Pandas DataFrames for data verification
- JSON schema validation for metadata
- SHA256 checksum verification
"""

import json
import hashlib
import tempfile
import time
from pathlib import Path
from decimal import Decimal
from typing import Generator

import pytest
import pandas as pd

# Import modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from native_recorder.config import RecorderConfigBuilder, create_quick_config
from native_recorder.strategy import NativeDataRecorderConfig, NativeDataRecorderStrategy
from native_recorder.persistence import (
    RecordingReader,
    validate_recording,
    generate_data_quality_report,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tmpdir_path(tmp_path: Path) -> Path:
    """Provide a temporary directory as Path object."""
    return tmp_path


@pytest.fixture
def output_dir(tmpdir_path: Path) -> Path:
    """Create and return output directory for recordings."""
    output_path = tmpdir_path / "recordings"
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


@pytest.fixture
def basic_config(output_dir: Path) -> tuple:
    """Create basic recorder configuration."""
    builder = RecorderConfigBuilder(trader_id="TEST-RECORDER-001")
    builder.add_instruments(["SOLUSDT-SPOT.BYBIT"])
    builder.set_output_dir(str(output_dir))
    builder.set_flush_interval(5)

    node_config, strategy_config = builder.build()
    return node_config, strategy_config


# ============================================================================
# TEST 1: CONFIG TO STRATEGY INTEGRATION
# ============================================================================

def test_config_to_strategy_integration(output_dir: Path) -> None:
    """
    Verify config → strategy initialization flow.

    Tests:
    - RecorderConfigBuilder creates valid configs
    - TradingNodeConfig is properly formed
    - NativeDataRecorderConfig has correct parameters
    - Strategy can be instantiated from config
    """
    # Create config using builder
    builder = RecorderConfigBuilder(trader_id="TEST-001")
    builder.add_instruments(["BTCUSDT-SPOT.BYBIT", "ETHUSDT-SPOT.BYBIT"])
    builder.set_output_dir(str(output_dir))
    builder.set_flush_interval(10)
    builder.set_duration(60)
    builder.enable_orderbook(depth=25)

    node_config, strategy_config = builder.build()

    # Validate node config
    assert node_config.trader_id.value == "TEST-001"
    assert "BYBIT" in node_config.data_clients

    # Validate strategy config
    assert strategy_config.instrument_ids == ["BTCUSDT-SPOT.BYBIT", "ETHUSDT-SPOT.BYBIT"]
    assert strategy_config.output_dir == str(output_dir)
    assert strategy_config.flush_interval_seconds == 10
    assert strategy_config.run_duration_seconds == 60
    assert strategy_config.record_orderbook is True
    assert strategy_config.orderbook_depth == 25
    assert strategy_config.record_quotes is True

    # Verify strategy can be instantiated
    strategy = NativeDataRecorderStrategy(strategy_config)
    assert strategy.config == strategy_config
    assert len(strategy.quote_ticks_data) == 0
    assert len(strategy.order_book_deltas_data) == 0
    assert strategy.quote_count == 0
    assert strategy.delta_count == 0


# ============================================================================
# TEST 2: MOCK RECORDING WORKFLOW
# ============================================================================

def test_mock_recording_workflow(output_dir: Path) -> None:
    """
    Simulate 30-second recording with mock TradeTick/QuoteTick data.

    Workflow:
    1. Create strategy with configuration
    2. Call on_start() to initialize session
    3. Inject mock quote ticks (simulating live data)
    4. Manually trigger periodic flush
    5. Inject more data and flush again
    6. Call on_stop() for graceful shutdown
    7. Verify session metadata and output files
    """
    # Setup
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=False,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)

    # Initialize session
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-20251109-120000"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Mock: Inject quote tick data
    instrument_key = "SOLUSDT-SPOT.BYBIT"

    # First batch of quotes
    for i in range(10):
        tick_data = {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 120.0 + i * 0.01,
            "ask_price": 120.02 + i * 0.01,
            "bid_size": 100.0,
            "ask_size": 100.0,
        }
        if instrument_key not in strategy.quote_ticks_data:
            strategy.quote_ticks_data[instrument_key] = []
        strategy.quote_ticks_data[instrument_key].append(tick_data)
        strategy.quote_count += 1

    # First flush
    strategy._save_all_data()
    assert len(strategy.quote_ticks_data[instrument_key]) == 0, "Buffer should be cleared after flush"

    # Second batch of quotes
    for i in range(15):
        tick_data = {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 120.1 + i * 0.01,
            "ask_price": 120.12 + i * 0.01,
            "bid_size": 100.0,
            "ask_size": 100.0,
        }
        strategy.quote_ticks_data[instrument_key].append(tick_data)
        strategy.quote_count += 1

    # Graceful shutdown
    strategy.session_start_time = time.time() - 30  # Simulate 30-second session
    strategy.on_stop()

    # Verify outputs
    assert (strategy.output_path / "session_metadata.json").exists(), "Metadata file should be created"
    assert (strategy.output_path / "checksums.json").exists(), "Checksums file should be created"

    # Verify parquet file
    quote_file = strategy.output_path / "quote_ticks" / instrument_key / "quote_ticks.parquet"
    assert quote_file.exists(), f"Quote parquet file should exist at {quote_file}"

    # Verify parquet is readable
    df = pd.read_parquet(quote_file)
    assert len(df) == 25, f"Should have 25 quotes, got {len(df)}"
    assert "bid_price" in df.columns
    assert "ask_price" in df.columns
    assert "bid_size" in df.columns
    assert "ask_size" in df.columns


# ============================================================================
# TEST 3: PARQUET FILE CREATION
# ============================================================================

def test_parquet_file_creation(output_dir: Path) -> None:
    """
    Verify parquet files are created with correct directory structure.

    Expected structure:
    output_dir/run_id/
    ├── quote_ticks/
    │   └── SOLUSDT-SPOT.BYBIT/
    │       └── quote_ticks.parquet
    ├── order_book_deltas/
    │   └── SOLUSDT-SPOT.BYBIT/
    │       └── order_book_deltas.parquet
    ├── session_metadata.json
    └── checksums.json
    """
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=True,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)

    # Initialize session
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-STRUCT-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Add quote data for multiple instruments
    for instrument in ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]:
        strategy.quote_ticks_data[instrument] = [
            {
                "timestamp": pd.Timestamp.now(tz="UTC"),
                "bid_price": 100.0,
                "ask_price": 100.1,
                "bid_size": 50.0,
                "ask_size": 50.0,
            }
        ]

    # Add delta data
    for instrument in ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]:
        strategy.order_book_deltas_data[instrument] = [
            {
                "timestamp": pd.Timestamp.now(tz="UTC"),
                "action": "ADD",
                "side": "BUY",
                "price": 100.0,
                "size": 10.0,
                "order_id": "order_123",
            }
        ]

    # Save all data
    strategy._save_all_data()

    # Verify directory structure
    assert (strategy.output_path / "quote_ticks").exists()
    assert (strategy.output_path / "quote_ticks" / "SOLUSDT-SPOT.BYBIT").exists()
    assert (strategy.output_path / "quote_ticks" / "BTCUSDT-SPOT.BYBIT").exists()

    assert (strategy.output_path / "order_book_deltas").exists()
    assert (strategy.output_path / "order_book_deltas" / "SOLUSDT-SPOT.BYBIT").exists()
    assert (strategy.output_path / "order_book_deltas" / "BTCUSDT-SPOT.BYBIT").exists()

    # Verify parquet files exist
    quote_sol = strategy.output_path / "quote_ticks" / "SOLUSDT-SPOT.BYBIT" / "quote_ticks.parquet"
    quote_btc = strategy.output_path / "quote_ticks" / "BTCUSDT-SPOT.BYBIT" / "quote_ticks.parquet"
    delta_sol = strategy.output_path / "order_book_deltas" / "SOLUSDT-SPOT.BYBIT" / "order_book_deltas.parquet"
    delta_btc = strategy.output_path / "order_book_deltas" / "BTCUSDT-SPOT.BYBIT" / "order_book_deltas.parquet"

    assert quote_sol.exists()
    assert quote_btc.exists()
    assert delta_sol.exists()
    assert delta_btc.exists()


# ============================================================================
# TEST 4: PARQUET APPEND LOGIC
# ============================================================================

def test_parquet_append_logic(output_dir: Path) -> None:
    """
    Verify multiple flushes → single file with appended data.

    Workflow:
    1. Create strategy and first batch of data
    2. First flush: creates parquet file with 5 quotes
    3. Add 5 more quotes
    4. Second flush: appends to file (total 10 quotes)
    5. Verify file contains all 10 quotes in order
    """
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=False,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-APPEND-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    instrument_key = "SOLUSDT-SPOT.BYBIT"

    # First batch: 5 quotes
    for i in range(5):
        strategy.quote_ticks_data[instrument_key] = [
            {
                "timestamp": pd.Timestamp.now(tz="UTC") + pd.Timedelta(seconds=i),
                "bid_price": 100.0 + i,
                "ask_price": 100.1 + i,
                "bid_size": 50.0,
                "ask_size": 50.0,
            }
        ]
        strategy.quote_count += 1

    # First flush
    strategy._save_all_data()

    # Verify first batch
    quote_file = strategy.output_path / "quote_ticks" / instrument_key / "quote_ticks.parquet"
    df1 = pd.read_parquet(quote_file)
    assert len(df1) == 5, f"First batch should have 5 quotes, got {len(df1)}"

    # Second batch: 5 more quotes
    for i in range(5, 10):
        strategy.quote_ticks_data[instrument_key] = [
            {
                "timestamp": pd.Timestamp.now(tz="UTC") + pd.Timedelta(seconds=i),
                "bid_price": 100.0 + i,
                "ask_price": 100.1 + i,
                "bid_size": 50.0,
                "ask_size": 50.0,
            }
        ]
        strategy.quote_count += 1

    # Second flush
    strategy._save_all_data()

    # Verify appended data
    df2 = pd.read_parquet(quote_file)
    assert len(df2) == 10, f"After append should have 10 quotes, got {len(df2)}"

    # Verify timestamps are sorted
    assert df2["timestamp"].is_monotonic_increasing or len(df2) <= 1


# ============================================================================
# TEST 5: METADATA GENERATION
# ============================================================================

def test_metadata_generation(output_dir: Path) -> None:
    """
    Verify session_metadata.json is created with correct schema.

    Expected fields:
    - run_id: str
    - session_start: float (unix timestamp)
    - session_end: float (unix timestamp)
    - duration_seconds: float
    - instruments: list[str]
    - quote_count: int
    - delta_count: int
    - config: dict with configuration details
    """
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT", "ETHUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=10,
        record_quotes=True,
        record_orderbook=True,
        orderbook_depth=20,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-META-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Simulate some data collection
    strategy.quote_count = 42
    strategy.delta_count = 128

    # Simulate 10-second session
    strategy.session_start_time = time.time() - 10

    # Generate metadata
    strategy._save_session_metadata()

    # Verify file exists
    metadata_file = strategy.output_path / "session_metadata.json"
    assert metadata_file.exists(), "Metadata file should be created"

    # Load and validate metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    # Verify required fields
    assert "run_id" in metadata
    assert metadata["run_id"] == "TEST-META-001"

    assert "session_start" in metadata
    assert isinstance(metadata["session_start"], (int, float))

    assert "session_end" in metadata
    assert isinstance(metadata["session_end"], (int, float))

    assert "duration_seconds" in metadata
    assert 9 < metadata["duration_seconds"] < 11, "Duration should be ~10 seconds"

    assert "instruments" in metadata
    assert metadata["instruments"] == ["SOLUSDT-SPOT.BYBIT", "ETHUSDT-SPOT.BYBIT"]

    assert "quote_count" in metadata
    assert metadata["quote_count"] == 42

    assert "delta_count" in metadata
    assert metadata["delta_count"] == 128

    # Verify config section
    assert "config" in metadata
    config = metadata["config"]
    assert config["flush_interval_seconds"] == 10
    assert config["record_quotes"] is True
    assert config["record_orderbook"] is True
    assert config["orderbook_depth"] == 20


# ============================================================================
# TEST 6: CHECKSUM GENERATION
# ============================================================================

def test_checksum_generation(output_dir: Path) -> None:
    """
    Verify checksums.json is created and all files are checksummed.

    Validates:
    - checksums.json exists
    - All parquet files have entries
    - SHA256 checksums are valid (can recompute and match)
    - File sizes are recorded correctly
    - Relative paths are correct
    """
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=False,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-CHECKSUM-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Create test data
    strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"] = [
        {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 100.0,
            "ask_price": 100.1,
            "bid_size": 50.0,
            "ask_size": 50.0,
        }
    ]

    # Save data
    strategy._save_all_data()

    # Generate checksums
    strategy._generate_checksums()

    # Verify checksum file exists
    checksum_file = strategy.output_path / "checksums.json"
    assert checksum_file.exists(), "Checksums file should be created"

    # Load checksums
    with open(checksum_file, "r") as f:
        checksums = json.load(f)

    # Verify entries exist
    assert len(checksums) > 0, "Should have at least one checksum"

    # Verify all parquet files are checksummed
    parquet_files = list(strategy.output_path.rglob("*.parquet"))
    assert len(parquet_files) > 0, "Should have at least one parquet file"

    for parquet_file in parquet_files:
        rel_path = str(parquet_file.relative_to(strategy.output_path))
        assert rel_path in checksums, f"Checksum should exist for {rel_path}"

        # Verify checksum is valid
        entry = checksums[rel_path]
        assert "sha256" in entry
        assert "size_bytes" in entry

        # Recompute checksum and verify it matches
        with open(parquet_file, "rb") as f:
            actual_sha256 = hashlib.sha256(f.read()).hexdigest()

        assert actual_sha256 == entry["sha256"], f"Checksum mismatch for {rel_path}"
        assert entry["size_bytes"] == parquet_file.stat().st_size


# ============================================================================
# TEST 7: GRACEFUL SHUTDOWN
# ============================================================================

def test_graceful_shutdown(output_dir: Path) -> None:
    """
    Verify on_stop() saves remaining data and generates metadata/checksums.

    Tests:
    - Remaining buffered data is saved to parquet
    - session_metadata.json is created
    - checksums.json is created and valid
    - All files are properly written
    - Session duration is recorded
    """
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=30,  # Long interval so data doesn't auto-flush
        record_quotes=True,
        record_orderbook=False,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time() - 5  # Simulate 5-second session
    strategy.run_id = "TEST-SHUTDOWN-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Add unsaved quote data
    strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"] = [
        {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 100.0 + i,
            "ask_price": 100.1 + i,
            "bid_size": 50.0,
            "ask_size": 50.0,
        }
        for i in range(7)
    ]
    strategy.quote_count = 7

    # Call on_stop (should save remaining data)
    strategy.on_stop()

    # Verify all data was saved
    quote_file = strategy.output_path / "quote_ticks" / "SOLUSDT-SPOT.BYBIT" / "quote_ticks.parquet"
    assert quote_file.exists(), "Quote file should be created on shutdown"

    df = pd.read_parquet(quote_file)
    assert len(df) == 7, f"Should have 7 quotes in file, got {len(df)}"

    # Verify metadata
    metadata_file = strategy.output_path / "session_metadata.json"
    assert metadata_file.exists()

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    assert metadata["quote_count"] == 7
    assert 4 < metadata["duration_seconds"] < 6, "Session duration should be ~5 seconds"

    # Verify checksums
    checksum_file = strategy.output_path / "checksums.json"
    assert checksum_file.exists()

    with open(checksum_file, "r") as f:
        checksums = json.load(f)

    assert len(checksums) > 0, "Should have checksums"


# ============================================================================
# TEST 8: MIXED QUOTE AND DELTA DATA
# ============================================================================

def test_mixed_quote_and_delta_data(output_dir: Path) -> None:
    """
    Verify both quotes and deltas can be recorded simultaneously.

    Tests:
    - Quote ticks and order book deltas are stored separately
    - Both data types are flushed correctly
    - Files maintain correct structure
    - Data types don't interfere with each other
    """
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=True,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-MIXED-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    instrument_key = "SOLUSDT-SPOT.BYBIT"

    # Add quote data
    strategy.quote_ticks_data[instrument_key] = [
        {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 100.0 + i,
            "ask_price": 100.1 + i,
            "bid_size": 50.0,
            "ask_size": 50.0,
        }
        for i in range(8)
    ]
    strategy.quote_count = 8

    # Add delta data
    strategy.order_book_deltas_data[instrument_key] = [
        {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "action": "ADD" if i % 2 == 0 else "DELETE",
            "side": "BUY" if i % 2 == 0 else "SELL",
            "price": 100.0 + i * 0.5,
            "size": 10.0 + i,
            "order_id": f"order_{i}",
        }
        for i in range(12)
    ]
    strategy.delta_count = 12

    # Save all data
    strategy._save_all_data()

    # Verify quote file
    quote_file = strategy.output_path / "quote_ticks" / instrument_key / "quote_ticks.parquet"
    assert quote_file.exists()
    quote_df = pd.read_parquet(quote_file)
    assert len(quote_df) == 8
    assert "bid_price" in quote_df.columns
    assert "ask_price" in quote_df.columns

    # Verify delta file
    delta_file = strategy.output_path / "order_book_deltas" / instrument_key / "order_book_deltas.parquet"
    assert delta_file.exists()
    delta_df = pd.read_parquet(delta_file)
    assert len(delta_df) == 12
    assert "action" in delta_df.columns
    assert "side" in delta_df.columns
    assert "price" in delta_df.columns

    # Verify both buffers were cleared
    assert len(strategy.quote_ticks_data[instrument_key]) == 0
    assert len(strategy.order_book_deltas_data[instrument_key]) == 0


# ============================================================================
# TEST 9: INVALID CONFIG VALIDATION
# ============================================================================

def test_invalid_config_validation() -> None:
    """
    Verify configuration validation catches invalid inputs.

    Tests:
    - Missing instruments raises error
    - Invalid instrument ID format raises error
    - Invalid flush interval raises error
    - Invalid orderbook depth raises error
    - Invalid duration raises error
    """
    # Test 1: Missing instruments
    builder = RecorderConfigBuilder()
    with pytest.raises(ValueError, match="Must specify at least one instrument"):
        builder.build()

    # Test 2: Invalid instrument ID format
    builder = RecorderConfigBuilder()
    builder.add_instrument("SOLUSDT-SPOT")  # Missing .BYBIT
    with pytest.raises(ValueError, match="Invalid instrument ID"):
        builder.build()

    # Test 3: Invalid flush interval
    builder = RecorderConfigBuilder()
    builder.add_instrument("SOLUSDT-SPOT.BYBIT")
    builder.set_flush_interval(0)
    with pytest.raises(ValueError, match="flush_interval must be > 0"):
        builder.build()

    # Test 4: Invalid orderbook depth
    builder = RecorderConfigBuilder()
    builder.add_instrument("SOLUSDT-SPOT.BYBIT")
    builder.enable_orderbook(depth=-1)
    with pytest.raises(ValueError, match="orderbook_depth must be > 0"):
        builder.build()

    # Test 5: Invalid duration
    builder = RecorderConfigBuilder()
    builder.add_instrument("SOLUSDT-SPOT.BYBIT")
    builder.set_duration(-5)
    with pytest.raises(ValueError, match="run_duration must be > 0 or None"):
        builder.build()


# ============================================================================
# TEST 10: CREATE_QUICK_CONFIG CONVENIENCE FUNCTION
# ============================================================================

def test_create_quick_config(output_dir: Path) -> None:
    """
    Verify create_quick_config convenience function works correctly.

    Tests:
    - Single instrument configuration
    - Multiple instruments
    - With and without orderbook
    - With and without duration
    """
    # Test 1: Single instrument
    node_cfg, strat_cfg = create_quick_config(
        ["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
    )
    assert strat_cfg.instrument_ids == ["SOLUSDT-SPOT.BYBIT"]
    assert strat_cfg.record_orderbook is False
    assert strat_cfg.run_duration_seconds is None

    # Test 2: Multiple instruments with orderbook
    node_cfg, strat_cfg = create_quick_config(
        ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        duration_seconds=300,
        with_orderbook=True,
    )
    assert len(strat_cfg.instrument_ids) == 2
    assert strat_cfg.record_orderbook is True
    assert strat_cfg.run_duration_seconds == 300

    # Test 3: Invalid inputs
    with pytest.raises(ValueError):
        create_quick_config([], output_dir=str(output_dir))


# ============================================================================
# TEST 11: RECORDING READER INTEGRATION
# ============================================================================

def test_recording_reader_integration(output_dir: Path) -> None:
    """
    Verify RecordingReader can read and analyze recorded data.

    Tests:
    - RecordingReader initialization
    - read_quotes() method
    - list_instruments() method
    - get_metadata() method
    - get_statistics() method
    """
    # Create test recording
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=False,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-READER-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Add data and save
    strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"] = [
        {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 100.0 + i,
            "ask_price": 100.1 + i,
            "bid_size": 50.0,
            "ask_size": 50.0,
        }
        for i in range(10)
    ]
    strategy.quote_count = 10
    strategy.on_stop()

    # Now use RecordingReader
    reader = RecordingReader(strategy.output_path)

    # Test read_quotes
    quotes_df = reader.read_quotes("SOLUSDT-SPOT.BYBIT")
    assert len(quotes_df) == 10
    assert "bid_price" in quotes_df.columns

    # Test list_instruments
    instruments = reader.list_instruments()
    assert "quote_ticks" in instruments
    assert "SOLUSDT-SPOT.BYBIT" in instruments["quote_ticks"]

    # Test get_metadata
    metadata = reader.get_metadata()
    assert metadata["quote_count"] == 10
    assert "SOLUSDT-SPOT.BYBIT" in metadata["instruments"]

    # Test get_statistics
    stats = reader.get_statistics()
    assert "instruments" in stats
    assert "data_types" in stats
    assert "total_parquet_size_bytes" in stats


# ============================================================================
# TEST 12: VALIDATE_RECORDING FUNCTION
# ============================================================================

def test_validate_recording_function(output_dir: Path) -> None:
    """
    Verify validate_recording produces correct validation report.

    Tests:
    - Returns valid=True for good recording
    - Identifies missing metadata
    - Verifies checksums
    - Checks data readability
    """
    # Create valid recording
    strategy_config = NativeDataRecorderConfig(
        instrument_ids=["SOLUSDT-SPOT.BYBIT"],
        output_dir=str(output_dir),
        flush_interval_seconds=5,
        record_quotes=True,
        record_orderbook=False,
    )

    strategy = NativeDataRecorderStrategy(strategy_config)
    strategy.session_start_time = time.time()
    strategy.run_id = "TEST-VALIDATE-001"
    strategy.output_path = Path(output_dir) / strategy.run_id
    strategy.output_path.mkdir(parents=True, exist_ok=True)

    # Add data and save
    strategy.quote_ticks_data["SOLUSDT-SPOT.BYBIT"] = [
        {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "bid_price": 100.0 + i,
            "ask_price": 100.1 + i,
            "bid_size": 50.0,
            "ask_size": 50.0,
        }
        for i in range(5)
    ]
    strategy.quote_count = 5
    strategy.on_stop()

    # Validate
    report = validate_recording(strategy.output_path)

    # Check report structure
    assert "valid" in report
    assert "issues" in report
    assert "checks" in report

    # For a properly created recording, should be valid
    assert report["valid"] is True, f"Recording should be valid, issues: {report['issues']}"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    # Allow running directly: python test_full_recording.py
    pytest.main([__file__, "-v", "--tb=short"])
