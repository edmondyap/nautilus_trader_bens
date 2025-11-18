# Nautilus Trader Recording Validation Tools

Standalone CLI scripts for validating and comparing recorded trading data from the Native Data Recorder.

## Scripts

### 1. `validate_recording.py`

Validate a single recording directory to ensure data integrity and consistency.

**Usage:**
```bash
python validate_recording.py <path> [options]
```

**Examples:**
```bash
# Basic validation
python validate_recording.py /data/recordings/20251109-123456

# Verbose output with detailed checks
python validate_recording.py /data/recordings/20251109-123456 --verbose

# Save detailed report to JSON
python validate_recording.py /data/recordings/20251109-123456 --report report.json

# Verbose + JSON report
python validate_recording.py /data/recordings/20251109-123456 -v --report report.json
```

**Options:**
- `-v, --verbose`: Show detailed check results for each validation step
- `--report FILE`: Save detailed validation report to JSON file

**Validation Checks:**
1. **Metadata Exists** - Verifies `session_metadata.json` is present
2. **Checksums Exist** - Verifies `checksums.json` is present
3. **Checksums Match** - Validates SHA256 checksums for all parquet files
4. **Data Readable** - Ensures all parquet files can be read
5. **Timestamps Ordered** - Verifies timestamp columns are monotonically increasing
6. **Data Not Empty** - Checks that each dataset contains records

**Output:**
```
======================================================================
RECORDING VALIDATION REPORT
======================================================================

✅ OVERALL STATUS: VALID

Recording Statistics:
----------------------------------------------------------------------
  📂 Directory: /data/recordings/20251109-123456
  💾 Total Size: 45.67 MB
  📊 Data Types: quote_ticks, order_book_deltas
     - quote_ticks: 2 instrument(s)
     - order_book_deltas: 2 instrument(s)

======================================================================
✅ Validation passed! Recording is ready to use.
======================================================================
```

**Exit Codes:**
- `0` - Validation passed
- `1` - Validation failed with issues

---

### 2. `compare_recordings.py`

Compare two recording directories side-by-side (useful for comparing hybrid vs native recordings).

**Usage:**
```bash
python compare_recordings.py <dir1> <dir2> [options]
```

**Examples:**
```bash
# Basic comparison
python compare_recordings.py /data/hybrid /data/native

# Verbose output with instrument lists
python compare_recordings.py /data/hybrid /data/native --verbose

# Also validate both recordings
python compare_recordings.py /data/hybrid /data/native --validate

# Save comparison report to JSON
python compare_recordings.py /data/hybrid /data/native --report comparison.json

# Full verbose + validation + report
python compare_recordings.py /data/hybrid /data/native -v --validate --report comparison.json
```

**Options:**
- `-v, --verbose`: Show detailed statistics and instrument lists
- `--report FILE`: Save comparison report to JSON file
- `--validate`: Also validate both recordings before comparing

**Output:**
```
==============================================================================================
RECORDING COMPARISON REPORT
==============================================================================================

Recording Paths:
  Recording 1: /data/hybrid
  Recording 2: /data/native

Size Comparison:
-------------------------------
  Recording 1:    125.45 MB
  Recording 2:    120.32 MB
  Difference:       5.13 MB (+4.3%) [Rec1 larger]

Instrument Comparison:
-------------------------------

  quote_ticks:
    Recording 1: 2 instrument(s)
    Recording 2: 2 instrument(s)

  order_book_deltas:
    Recording 1: 2 instrument(s)
    Recording 2: 2 instrument(s)

==============================================================================================
```

**Exit Codes:**
- `0` - Comparison completed successfully
- `1` - Error during comparison

---

## Features

### validate_recording.py
- ✅ Uses `argparse` for CLI argument parsing
- ✅ Colorized output with emoji indicators (✅ = pass, ❌ = fail, ⚠️ = warning)
- ✅ Detailed validation checks with specific error messages
- ✅ Optional verbose mode for detailed results
- ✅ JSON report export capability
- ✅ Proper exit codes for scripting/automation
- ✅ File size statistics
- ✅ Data count statistics
- ✅ Time range analysis

### compare_recordings.py
- ✅ Uses `argparse` for CLI argument parsing
- ✅ Side-by-side size comparison with percentage differences
- ✅ Instrument count comparison by data type
- ✅ Optional verbose mode showing specific instruments
- ✅ Optional validation of both recordings
- ✅ JSON report export capability
- ✅ Formatted comparison tables
- ✅ Detailed statistics per recording
- ✅ Proper exit codes for scripting/automation

---

## Use Cases

### Single Recording Validation
```bash
# Quick check if a recording is valid
python validate_recording.py /data/recordings/20251109-123456

# Get detailed report for debugging
python validate_recording.py /data/recordings/20251109-123456 --verbose > validation.txt
```

### Recording Comparison (Hybrid vs Native)
```bash
# Compare recording sizes and content
python compare_recordings.py /data/recordings/hybrid /data/recordings/native

# Full comparison with validation
python compare_recordings.py /data/recordings/hybrid /data/recordings/native --validate --verbose
```

### Automated Workflows
```bash
# Save reports for tracking
python validate_recording.py /data/recordings/20251109-123456 --report validation_20251109.json

# Check if valid before processing
if python validate_recording.py /data/recordings/20251109-123456 > /dev/null; then
    echo "Recording is valid - proceeding with analysis"
    python process_data.py /data/recordings/20251109-123456
else
    echo "Recording validation failed - check logs"
fi
```

---

## Integration with persistence.py

These scripts call functions from `/benchmark/nautilus_trader/native_recorder/persistence.py`:

- `validate_recording(path)` - Full validation with all checks
- `compare_recordings(dir1, dir2)` - Recording comparison
- `RecordingReader(path)` - Load and read recording data

The scripts use direct module loading to avoid import circular dependencies.

---

## Exit Behavior

Both scripts:
- **Exit 0** on success
- **Exit 1** on failure or invalid arguments
- Print colorized output to stdout
- Print errors to stderr (with traceback in verbose mode)

This makes them suitable for use in scripts, CI/CD pipelines, and automated monitoring.

---

## Requirements

- Python 3.8+
- pandas (for reading parquet files)
- pathlib (standard library)
- json (standard library)
- argparse (standard library)
- hashlib (standard library)

---

**Created:** 2025-11-09  
**Part of:** Nautilus Trader Native Data Collection (Phase 5.3)
