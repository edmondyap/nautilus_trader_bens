"""
Unit Tests for RecorderConfigBuilder and Configuration Loading

Tests configuration builder, validation logic, YAML loading, and quick config helper.

Location: benchmark/nautilus_trader/tests/test_config.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from nautilus_trader.config import TradingNodeConfig
from my_trading_system.native_recorder.config import (
    RecorderConfigBuilder,
    load_config_from_yaml,
    create_quick_config,
)
from my_trading_system.native_recorder.strategy import NativeDataRecorderConfig


class TestRecorderConfigBuilder:
    """Tests for RecorderConfigBuilder fluent API and validation."""

    def test_builder_initialization(self):
        """Test builder initializes with default values."""
        builder = RecorderConfigBuilder(trader_id="TEST-001")

        assert builder.trader_id.value == "TEST-001"
        assert builder.instruments == []
        assert builder.output_dir == "data/recordings"
        assert builder.flush_interval == 60
        assert builder.record_quotes is True
        assert builder.record_orderbook is False
        assert builder.orderbook_depth == 50
        assert builder.connection_timeout == 120
        assert builder.run_duration is None

    def test_add_single_instrument(self):
        """Test adding a single instrument."""
        builder = RecorderConfigBuilder()
        result = builder.add_instrument("SOLUSDT-SPOT.BYBIT")

        # Test fluent interface
        assert result is builder
        assert "SOLUSDT-SPOT.BYBIT" in builder.instruments
        assert len(builder.instruments) == 1

    def test_add_duplicate_instrument_not_added_twice(self):
        """Test that duplicate instruments are not added twice."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")

        assert len(builder.instruments) == 1

    def test_add_multiple_instruments(self):
        """Test adding multiple instruments at once."""
        builder = RecorderConfigBuilder()
        instruments = ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT", "ETHUSDT-SPOT.BYBIT"]
        result = builder.add_instruments(instruments)

        assert result is builder
        assert len(builder.instruments) == 3
        assert all(inst in builder.instruments for inst in instruments)

    def test_set_output_dir_with_string(self):
        """Test setting output directory with string."""
        builder = RecorderConfigBuilder()
        result = builder.set_output_dir("./custom/data/path")

        assert result is builder
        assert builder.output_dir == "./custom/data/path"

    def test_set_output_dir_with_path(self):
        """Test setting output directory with Path object."""
        builder = RecorderConfigBuilder()
        path = Path("./custom/data/path")
        result = builder.set_output_dir(path)

        assert result is builder
        assert builder.output_dir == str(path)

    def test_set_flush_interval(self):
        """Test setting flush interval."""
        builder = RecorderConfigBuilder()
        result = builder.set_flush_interval(120)

        assert result is builder
        assert builder.flush_interval == 120

    def test_enable_orderbook(self):
        """Test enabling order book recording."""
        builder = RecorderConfigBuilder()
        result = builder.enable_orderbook(depth=100)

        assert result is builder
        assert builder.record_orderbook is True
        assert builder.orderbook_depth == 100

    def test_disable_quotes(self):
        """Test disabling quote recording."""
        builder = RecorderConfigBuilder()
        result = builder.disable_quotes()

        assert result is builder
        assert builder.record_quotes is False

    def test_set_duration(self):
        """Test setting run duration."""
        builder = RecorderConfigBuilder()
        result = builder.set_duration(300)

        assert result is builder
        assert builder.run_duration == 300

    def test_set_bybit_credentials(self):
        """Test setting Bybit API credentials."""
        builder = RecorderConfigBuilder()
        result = builder.set_bybit_credentials(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )

        assert result is builder
        assert builder.api_key == "test_key"
        assert builder.api_secret == "test_secret"
        assert builder.testnet is True

    def test_fluent_interface_chaining(self):
        """Test fluent interface chaining multiple methods."""
        builder = RecorderConfigBuilder("TRADER-001")
        result = (
            builder
            .add_instruments(["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"])
            .set_output_dir("./output")
            .set_flush_interval(30)
            .enable_orderbook(depth=100)
            .set_duration(600)
        )

        assert result is builder
        assert builder.instruments == ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        assert builder.output_dir == "./output"
        assert builder.flush_interval == 30
        assert builder.record_orderbook is True
        assert builder.orderbook_depth == 100
        assert builder.run_duration == 600


class TestRecorderConfigBuilderValidation:
    """Tests for configuration validation logic."""

    def test_validate_no_instruments_raises_error(self):
        """Test validation fails when no instruments specified."""
        builder = RecorderConfigBuilder()

        with pytest.raises(ValueError, match="Must specify at least one instrument"):
            builder.validate()

    def test_validate_invalid_instrument_format(self):
        """Test validation fails for invalid instrument format."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT")  # Missing .BYBIT

        with pytest.raises(ValueError, match="Invalid instrument ID"):
            builder.validate()

    def test_validate_invalid_flush_interval(self):
        """Test validation fails for non-positive flush interval."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")
        builder.flush_interval = 0

        with pytest.raises(ValueError, match="flush_interval must be > 0"):
            builder.validate()

    def test_validate_invalid_orderbook_depth(self):
        """Test validation fails for non-positive orderbook depth."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")
        builder.orderbook_depth = -1

        with pytest.raises(ValueError, match="orderbook_depth must be > 0"):
            builder.validate()

    def test_validate_invalid_run_duration(self):
        """Test validation fails for non-positive run duration."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")
        builder.run_duration = -5

        with pytest.raises(ValueError, match="run_duration must be > 0 or None"):
            builder.validate()

    def test_validate_valid_config_passes(self):
        """Test validation passes for valid configuration."""
        builder = RecorderConfigBuilder()
        builder.add_instruments(["SOLUSDT-SPOT.BYBIT"])
        builder.set_flush_interval(60)
        builder.set_duration(300)

        # Should not raise
        builder.validate()

    def test_validate_none_duration_is_valid(self):
        """Test that None duration (run forever) is valid."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")
        builder.run_duration = None

        # Should not raise
        builder.validate()


class TestRecorderConfigBuilderBuild:
    """Tests for building TradingNodeConfig and NativeDataRecorderConfig."""

    def test_build_returns_tuple_of_configs(self):
        """Test build returns correct tuple."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")

        node_config, strategy_config = builder.build()

        assert isinstance(node_config, TradingNodeConfig)
        assert isinstance(strategy_config, NativeDataRecorderConfig)

    def test_build_strategy_config_has_correct_values(self):
        """Test strategy config has correct values from builder."""
        builder = RecorderConfigBuilder()
        builder.add_instruments(["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"])
        builder.set_output_dir("./data")
        builder.set_flush_interval(45)
        builder.enable_orderbook(depth=25)
        builder.disable_quotes()
        builder.set_duration(600)

        node_config, strategy_config = builder.build()

        assert strategy_config.instrument_ids == ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        assert strategy_config.output_dir == "./data"
        assert strategy_config.flush_interval_seconds == 45
        assert strategy_config.record_orderbook is True
        assert strategy_config.orderbook_depth == 25
        assert strategy_config.record_quotes is False
        assert strategy_config.run_duration_seconds == 600

    def test_build_node_config_has_trader_id(self):
        """Test node config has trader ID."""
        builder = RecorderConfigBuilder(trader_id="CUSTOM-TRADER")
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")

        node_config, strategy_config = builder.build()

        assert node_config.trader_id.value == "CUSTOM-TRADER"

    def test_build_validates_before_building(self):
        """Test that build validates configuration."""
        builder = RecorderConfigBuilder()
        # Don't add instruments

        with pytest.raises(ValueError, match="Must specify at least one instrument"):
            builder.build()

    def test_build_with_bybit_credentials(self):
        """Test build includes Bybit credentials."""
        builder = RecorderConfigBuilder()
        builder.add_instrument("SOLUSDT-SPOT.BYBIT")
        builder.set_bybit_credentials("key123", "secret456", testnet=True)

        node_config, strategy_config = builder.build()

        # Verify Bybit config exists in data_clients
        assert "BYBIT" in node_config.data_clients


class TestLoadConfigFromYaml:
    """Tests for loading configuration from YAML files."""

    def test_load_config_from_yaml_valid_file(self):
        """Test loading configuration from valid YAML file."""
        yaml_content = {
            "trader_id": "YAML-TRADER-001",
            "strategy": {
                "instruments": ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
                "output_dir": "data/yaml_recordings",
                "flush_interval_seconds": 45,
                "record_quotes": True,
                "record_orderbook": True,
                "orderbook_depth": 25,
                "run_duration_seconds": 300,
            },
            "bybit": {
                "api_key": "test_key",
                "api_secret": "test_secret",
                "testnet": True,
            }
        }

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            node_config, strategy_config = load_config_from_yaml(yaml_path)

            assert strategy_config.instrument_ids == ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
            assert strategy_config.output_dir == "data/yaml_recordings"
            assert strategy_config.flush_interval_seconds == 45
            assert strategy_config.record_quotes is True
            assert strategy_config.record_orderbook is True
            assert strategy_config.orderbook_depth == 25
            assert strategy_config.run_duration_seconds == 300

    def test_load_config_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_config_from_yaml("/nonexistent/path/config.yaml")

    def test_load_config_default_values(self):
        """Test YAML loading uses default values for missing keys."""
        yaml_content = {
            "strategy": {
                "instruments": ["SOLUSDT-SPOT.BYBIT"],
            }
        }

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            node_config, strategy_config = load_config_from_yaml(yaml_path)

            assert strategy_config.flush_interval_seconds == 60  # default
            assert strategy_config.record_quotes is True  # default
            assert strategy_config.record_orderbook is False  # default

    def test_load_config_with_path_object(self):
        """Test loading with Path object instead of string."""
        yaml_content = {
            "strategy": {
                "instruments": ["SOLUSDT-SPOT.BYBIT"],
            }
        }

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            # Use Path object
            node_config, strategy_config = load_config_from_yaml(yaml_path)

            assert strategy_config.instrument_ids == ["SOLUSDT-SPOT.BYBIT"]

    def test_load_config_disables_quotes(self):
        """Test YAML loading can disable quote recording."""
        yaml_content = {
            "strategy": {
                "instruments": ["SOLUSDT-SPOT.BYBIT"],
                "record_quotes": False,
            }
        }

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            node_config, strategy_config = load_config_from_yaml(yaml_path)

            assert strategy_config.record_quotes is False

    def test_load_config_enables_orderbook(self):
        """Test YAML loading can enable orderbook recording."""
        yaml_content = {
            "strategy": {
                "instruments": ["SOLUSDT-SPOT.BYBIT"],
                "record_orderbook": True,
                "orderbook_depth": 100,
            }
        }

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            node_config, strategy_config = load_config_from_yaml(yaml_path)

            assert strategy_config.record_orderbook is True
            assert strategy_config.orderbook_depth == 100


class TestCreateQuickConfig:
    """Tests for create_quick_config helper function."""

    def test_quick_config_basic(self):
        """Test basic quick config creation."""
        node_config, strategy_config = create_quick_config(
            ["SOLUSDT-SPOT.BYBIT"]
        )

        assert isinstance(node_config, TradingNodeConfig)
        assert isinstance(strategy_config, NativeDataRecorderConfig)
        assert strategy_config.instrument_ids == ["SOLUSDT-SPOT.BYBIT"]

    def test_quick_config_multiple_instruments(self):
        """Test quick config with multiple instruments."""
        instruments = ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        node_config, strategy_config = create_quick_config(instruments)

        assert strategy_config.instrument_ids == instruments

    def test_quick_config_custom_output_dir(self):
        """Test quick config with custom output directory."""
        node_config, strategy_config = create_quick_config(
            ["SOLUSDT-SPOT.BYBIT"],
            output_dir="./custom_output"
        )

        assert strategy_config.output_dir == "./custom_output"

    def test_quick_config_with_duration(self):
        """Test quick config with duration."""
        node_config, strategy_config = create_quick_config(
            ["SOLUSDT-SPOT.BYBIT"],
            duration_seconds=600
        )

        assert strategy_config.run_duration_seconds == 600

    def test_quick_config_with_orderbook(self):
        """Test quick config with orderbook enabled."""
        node_config, strategy_config = create_quick_config(
            ["SOLUSDT-SPOT.BYBIT"],
            with_orderbook=True
        )

        assert strategy_config.record_orderbook is True

    def test_quick_config_all_options(self):
        """Test quick config with all options."""
        instruments = ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]
        node_config, strategy_config = create_quick_config(
            instruments=instruments,
            output_dir="./test_data",
            duration_seconds=300,
            with_orderbook=True
        )

        assert strategy_config.instrument_ids == instruments
        assert strategy_config.output_dir == "./test_data"
        assert strategy_config.run_duration_seconds == 300
        assert strategy_config.record_orderbook is True

    def test_quick_config_validates(self):
        """Test quick config validates configuration."""
        # Empty instruments should fail
        with pytest.raises(ValueError):
            create_quick_config([])

    def test_quick_config_invalid_instrument_format(self):
        """Test quick config fails with invalid instrument format."""
        with pytest.raises(ValueError, match="Invalid instrument ID"):
            create_quick_config(["SOLUSDT"])  # Missing .BYBIT


class TestConfigIntegration:
    """Integration tests for configuration components."""

    def test_builder_and_quick_config_produce_same_result(self):
        """Test builder and quick_config produce equivalent configs."""
        instruments = ["SOLUSDT-SPOT.BYBIT"]
        output_dir = "./test"

        # Using builder
        builder = RecorderConfigBuilder()
        builder.add_instruments(instruments)
        builder.set_output_dir(output_dir)
        node1, strat1 = builder.build()

        # Using quick config
        node2, strat2 = create_quick_config(instruments, output_dir=output_dir)

        assert strat1.instrument_ids == strat2.instrument_ids
        assert strat1.output_dir == strat2.output_dir
        assert strat1.record_quotes == strat2.record_quotes
        assert strat1.record_orderbook == strat2.record_orderbook

    def test_yaml_and_builder_equivalence(self):
        """Test YAML and builder produce equivalent configs."""
        instruments = ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"]

        yaml_content = {
            "strategy": {
                "instruments": instruments,
                "output_dir": "data/test",
                "flush_interval_seconds": 90,
            }
        }

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            # Load from YAML
            node1, strat1 = load_config_from_yaml(yaml_path)

            # Build with builder
            builder = RecorderConfigBuilder()
            builder.add_instruments(instruments)
            builder.set_output_dir("data/test")
            builder.set_flush_interval(90)
            node2, strat2 = builder.build()

            assert strat1.instrument_ids == strat2.instrument_ids
            assert strat1.output_dir == strat2.output_dir
            assert strat1.flush_interval_seconds == strat2.flush_interval_seconds
