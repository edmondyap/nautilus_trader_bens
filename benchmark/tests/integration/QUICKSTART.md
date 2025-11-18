# Integration Tests - Quick Start Guide

**Location**: `benchmark/nautilus_trader/tests/integration/`

---

## File Structure

```
benchmark/nautilus_trader/tests/integration/
├── __init__.py                    # Package initialization
├── test_full_recording.py         # 920 lines, 12 comprehensive tests
├── TEST_SUMMARY.md                # Detailed test documentation
└── QUICKSTART.md                  # This file
```

---

## Prerequisites

Install pytest (if not already installed):

```bash
pip3 install pytest pandas
```

---

## Run All Tests

```bash
cd /Users/benjaminang/Desktop/Trading\ Engines/benchmark/nautilus_trader

# Basic run
python3 -m pytest tests/integration/test_full_recording.py -v

# With output
python3 -m pytest tests/integration/test_full_recording.py -v -s

# Verbose with full tracebacks
python3 -m pytest tests/integration/test_full_recording.py -vv --tb=short
```

---

## Run Specific Tests

**Configuration & Initialization**:
```bash
pytest tests/integration/test_full_recording.py::test_config_to_strategy_integration -v
pytest tests/integration/test_full_recording.py::test_create_quick_config -v
```

**Data Recording Workflow**:
```bash
pytest tests/integration/test_full_recording.py::test_mock_recording_workflow -v
pytest tests/integration/test_full_recording.py::test_mixed_quote_and_delta_data -v
```

**File Handling**:
```bash
pytest tests/integration/test_full_recording.py::test_parquet_file_creation -v
pytest tests/integration/test_full_recording.py::test_parquet_append_logic -v
```

**Metadata & Validation**:
```bash
pytest tests/integration/test_full_recording.py::test_metadata_generation -v
pytest tests/integration/test_full_recording.py::test_checksum_generation -v
pytest tests/integration/test_full_recording.py::test_graceful_shutdown -v
```

**Reader & Validation Functions**:
```bash
pytest tests/integration/test_full_recording.py::test_recording_reader_integration -v
pytest tests/integration/test_full_recording.py::test_validate_recording_function -v
```

**Error Handling**:
```bash
pytest tests/integration/test_full_recording.py::test_invalid_config_validation -v
```

---

## Test Summary

| # | Test Name | Purpose |
|---|-----------|---------|
| 1 | `test_config_to_strategy_integration` | Config → Strategy initialization |
| 2 | `test_mock_recording_workflow` | Full 30-second mock recording |
| 3 | `test_parquet_file_creation` | Directory structure validation |
| 4 | `test_parquet_append_logic` | Multiple flushes → single file |
| 5 | `test_metadata_generation` | session_metadata.json creation |
| 6 | `test_checksum_generation` | checksums.json with SHA256 |
| 7 | `test_graceful_shutdown` | on_stop() behavior |
| 8 | `test_mixed_quote_and_delta_data` | Quote + orderbook recording |
| 9 | `test_invalid_config_validation` | Error handling for bad configs |
| 10 | `test_create_quick_config` | Convenience function testing |
| 11 | `test_recording_reader_integration` | Reading recorded data |
| 12 | `test_validate_recording_function` | Recording validation report |

---

## Expected Output

When all tests pass, you should see:

```
tests/integration/test_full_recording.py::test_config_to_strategy_integration PASSED       [ 8%]
tests/integration/test_full_recording.py::test_mock_recording_workflow PASSED              [16%]
tests/integration/test_full_recording.py::test_parquet_file_creation PASSED                [25%]
tests/integration/test_full_recording.py::test_parquet_append_logic PASSED                 [33%]
tests/integration/test_full_recording.py::test_metadata_generation PASSED                  [41%]
tests/integration/test_full_recording.py::test_checksum_generation PASSED                  [50%]
tests/integration/test_full_recording.py::test_graceful_shutdown PASSED                    [58%]
tests/integration/test_full_recording.py::test_mixed_quote_and_delta_data PASSED           [66%]
tests/integration/test_full_recording.py::test_invalid_config_validation PASSED            [75%]
tests/integration/test_full_recording.py::test_create_quick_config PASSED                  [83%]
tests/integration/test_full_recording.py::test_recording_reader_integration PASSED         [91%]
tests/integration/test_full_recording.py::test_validate_recording_function PASSED          [100%]

========================= 12 passed in X.XXs =========================
```

---

## Key Features

✅ **No Live Connections** - All WebSocket data is mocked
✅ **Isolated Tests** - Each test gets clean tmpdir via pytest fixtures
✅ **Realistic Workflows** - Simulates actual recording patterns
✅ **Full Coverage** - Config → Persistence → Validation → Reading
✅ **Fast Execution** - All tests run in <30 seconds
✅ **Comprehensive** - 920 lines, 12 detailed tests, 100+ assertions

---

## Test Categories

### Configuration (2 tests)
- Config builder and validation
- Quick config convenience function
- Error detection for invalid inputs

### Recording Workflow (3 tests)
- Mock data injection and buffering
- Multi-instrument support
- Quote and delta data handling

### Persistence (4 tests)
- Parquet file creation and structure
- Append logic for multiple flushes
- Metadata generation with correct schema
- Checksum generation and validation

### Lifecycle (2 tests)
- Graceful shutdown behavior
- Final data persistence on stop

### Reading & Analysis (3 tests)
- RecordingReader integration
- Recording validation
- Metadata and statistics extraction

---

## Troubleshooting

### pytest not found
```bash
pip3 install pytest
```

### Import errors
Ensure you're running from the correct directory:
```bash
cd /Users/benjaminang/Desktop/Trading\ Engines/benchmark/nautilus_trader
```

### pandas not found
```bash
pip3 install pandas
```

### Slow test execution
Tests should complete in <30 seconds. If slower:
- Check system resources
- Run single test: `pytest tests/integration/test_full_recording.py::test_config_to_strategy_integration -v`

### Temporary directory issues
Tests use pytest's tmpdir fixture - ensure `/tmp` has write permissions:
```bash
touch /tmp/test_write_permission
```

---

## File Locations

| File | Purpose |
|------|---------|
| `test_full_recording.py` | Main test suite (920 lines) |
| `TEST_SUMMARY.md` | Detailed test documentation |
| `QUICKSTART.md` | This quick start guide |
| `__init__.py` | Package initialization |

---

## Next Steps

1. **Run the tests**:
   ```bash
   pytest tests/integration/test_full_recording.py -v
   ```

2. **Review test results** - All 12 should PASS

3. **Read TEST_SUMMARY.md** for detailed documentation

4. **Examine test code** - Each test is well-commented

5. **Add to CI/CD** - Run on every commit to catch regressions

---

## Contact & Support

For issues or questions about these tests:
- Review TEST_SUMMARY.md for detailed documentation
- Check test code comments in test_full_recording.py
- Run individual tests for debugging: `pytest -vv --tb=long`

---

**Created**: 2025-11-09
**Test Count**: 12
**Total Lines**: 920
**Status**: Ready for use
