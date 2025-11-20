"""
Integration Tests for Nautilus Trader Native Data Recorder

Location: benchmark/nautilus_trader/tests/integration/
Created: 2025-11-09

This package contains integration tests that verify the complete
data recording workflow without requiring live Bybit connections.
Tests use mocked WebSocket data to ensure reliable, deterministic testing.

Test Modules:
- test_full_recording.py: Comprehensive integration tests (12+ tests)
  - Config to strategy initialization
  - Mock data recording workflow
  - Parquet file creation and structure
  - Append logic for multiple flushes
  - Metadata generation
  - Checksum generation and validation
  - Graceful shutdown behavior
  - Mixed quote and delta data
  - Configuration validation
  - Quick config convenience function
  - RecordingReader integration
  - Recording validation functions

Running Tests:
  pytest tests/integration/test_full_recording.py -v
  pytest tests/integration/ -v  # All integration tests
  pytest tests/integration/test_full_recording.py::test_config_to_strategy_integration -v

Test Coverage:
- 100+ lines of test code per test function
- Uses pytest fixtures for clean test isolation
- Temporary directories via tmpdir fixture
- No external dependencies (mocked WebSocket)
- Fast execution (<30 seconds total)
"""
