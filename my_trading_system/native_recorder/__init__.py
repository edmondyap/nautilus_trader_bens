"""
Native Data Recorder - Production Data Collection Module

My Trading System - Production Code
Location: my_trading_system/native_recorder/__init__.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09

This module provides a native (85%+) data recording implementation for Nautilus Trader
using the Strategy framework, BybitDataClient, and direct parquet persistence.

Architecture:
- ✅ NATIVE: Nautilus Strategy, BybitDataClient, data models
- ❌ CUSTOM: pandas buffering, session metadata, SHA256 checksums

Upstream: nautilus_trader/ (DO NOT MODIFY)
Custom: This module (production data recording tool)
"""

from my_trading_system.native_recorder.config import (
    RecorderConfigBuilder,
    create_quick_config,
    load_config_from_yaml,
)
from my_trading_system.native_recorder.persistence import (
    RecordingReader,
    compare_recordings,
    generate_data_quality_report,
    load_recording,
    validate_recording,
)
from my_trading_system.native_recorder.strategy import (
    NativeDataRecorderConfig,
    NativeDataRecorderStrategy,
)

__all__ = [
    # Strategy
    "NativeDataRecorderStrategy",
    "NativeDataRecorderConfig",
    # Config
    "RecorderConfigBuilder",
    "load_config_from_yaml",
    "create_quick_config",
    # Persistence
    "RecordingReader",
    "validate_recording",
    "generate_data_quality_report",
    "load_recording",
    "compare_recordings",
]

__version__ = "1.0.0"
