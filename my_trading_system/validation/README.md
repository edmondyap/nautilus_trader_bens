# Advanced Data Validation System

Production-grade validation system for market data recordings from NautilusTrader.

## Quick Start

```bash
# Basic validation
python3 advanced_validation.py data/recordings/20251119-152837

# Verbose mode with visualizations
python3 advanced_validation.py data/recordings/20251119-152837 --verbose

# Fast mode (skip visualizations, higher sample rate)
python3 advanced_validation.py data/recordings/20251119-152837 \
    --skip-visualizations \
    --sample-rate 10000
```

## Features

### Complete Validation Pipeline

1. **Statistical Analysis**
   - Temporal gap detection (connectivity issues)
   - Price outlier detection (Z-score + IQR methods)
   - Bid-ask spread analysis
   - Trade volume profiling

2. **Integrity Checks**
   - Duplicate detection (exact and timestamp-based)
   - Missing/invalid value detection
   - Cross-validation between quotes and trades

3. **Orderbook Validation**
   - Crossed orderbook detection (critical data errors)
   - Price level ordering validation
   - Depth consistency analysis

4. **Quality Scoring**
   - Composite score (0-100)
   - Issue prioritization (Critical, High, Medium, Low)
   - Actionable recommendations
   - Pass/fail criteria validation

5. **Visualizations**
   - Price time series with trades
   - Spread distribution (histogram + box plot)
   - Volume profile (by price and time)
   - Interactive orderbook heatmap (HTML)

## Usage

### Command-Line Options

```bash
python3 advanced_validation.py [-h] [--output OUTPUT] [--skip-visualizations]
                              [--verbose] [--sample-rate SAMPLE_RATE]
                              recording_dir
```

**Arguments:**
- `recording_dir` - Path to recording directory (required)

**Options:**
- `--output OUTPUT, -o OUTPUT` - Custom output directory (default: `recording_dir/validation`)
- `--skip-visualizations` - Skip chart generation for speed
- `--verbose, -v` - Enable detailed progress output
- `--sample-rate SAMPLE_RATE` - Orderbook sampling rate (default: 1000)

### Exit Codes

- **0**: Validation passed (score >= 70)
- **1**: Validation failed (score < 70) or runtime error
- **2**: Invalid input (missing files, bad arguments)
- **130**: Interrupted by user (Ctrl+C)

## Examples

### Example 1: Quick Validation

```bash
python3 advanced_validation.py data/recordings/20251119-152837
```

Output:
```
================================================================================
ADVANCED DATA VALIDATION
================================================================================
Recording: data/recordings/20251119-152837
Output: data/recordings/20251119-152837/validation
Timestamp: 2025-11-19 23:21:23
Sample Rate: 1000
================================================================================

[1/7] Loading data...
[2/7] Running statistical analysis...
[3/7] Running integrity checks...
[4/7] Validating orderbook structure...
[5/7] Generating visualizations...
[6/7] Calculating quality score...
[7/7] Generating reports...

================================================================================
VALIDATION COMPLETE
================================================================================

Quality Score: 75/100 (Grade: C)
Issues Found: 2
  Critical: 1
  High: 1
  Medium: 0
  Low: 0

Execution Time: 225.4s

Recommendations:
  - ACCEPTABLE: Data usable with caveats. Monitor backtest behavior closely.
  - Fix Required: Crossed orderbooks detected: 8 - Verify orderbook reconstruction logic
  - Review: Large temporal gaps: 1032 - Check network stability during recording

Recommendation: APPROVED - Acceptable quality with caveats
================================================================================
```

### Example 2: Fast Mode (Skip Visualizations)

```bash
python3 advanced_validation.py data/recordings/20251119-152837 \
    --skip-visualizations \
    --sample-rate 10000
```

Benefits:
- 3-5x faster execution
- Lower memory usage
- Suitable for automated CI/CD pipelines

### Example 3: Verbose Mode (Detailed Progress)

```bash
python3 advanced_validation.py data/recordings/20251119-152837 --verbose
```

Shows detailed progress:
```
[1/7] Loading data...
    Loading instrument: SOLUSDT-SPOT.BYBIT
    Loaded quotes: 560,356 records (21.4 MB)
    Loaded trades: 70,242 records (2.1 MB)
    Loaded deltas: 4,013,933 records (535.3 MB)
    Total: 4.6M records in 0.2s

[2/7] Running statistical analysis...
    Gap analysis: 0.03s
    Outlier detection: 0.03s
    Spread analysis: 0.05s
    Statistical analysis complete: 0.11s
...
```

### Example 4: Custom Output Directory

```bash
python3 advanced_validation.py data/recordings/20251119-152837 \
    --output reports/my_validation \
    --verbose
```

Creates output directory at `reports/my_validation/` instead of default.

## Output Files

All outputs saved to `<recording_dir>/validation/` (or custom `--output` path):

### 1. results.json

Comprehensive validation results in JSON format:

```json
{
  "recording_dir": "/path/to/recording",
  "validation_timestamp": "2025-11-19T23:21:01.166055",
  "data_summary": {
    "quotes_count": 560356,
    "trades_count": 70242,
    "deltas_count": 4013933,
    "total_records": 4644531
  },
  "statistical_results": {
    "gaps": {...},
    "outliers": {...},
    "spreads": {...},
    "volume": {...}
  },
  "integrity_results": {
    "duplicates": {...},
    "missing_values": {...},
    "cross_validation": {...}
  },
  "orderbook_results": {
    "crossed_books": {...}
  },
  "quality_score": {
    "score": 75,
    "grade": "C",
    "issues_found": 2,
    "critical_issues": 1,
    "high_issues": 1,
    "medium_issues": 0,
    "low_issues": 0
  },
  "execution_time": 225.4
}
```

### 2. Visualizations (PNG)

- `price_timeseries.png` - Bid/ask prices with trade overlay + spread evolution
- `spread_distribution.png` - Histogram and box plot of spread distribution
- `volume_profile.png` - Volume by price level and time buckets

### 3. Interactive Charts (HTML)

- `orderbook_heatmap.html` - Interactive Plotly chart of orderbook depth evolution

## Quality Scoring

### Scoring Rubric

Starting at 100 (perfect), points deducted for issues:

| Issue | Priority | Deduction |
|-------|----------|-----------|
| Negative spreads | CRITICAL | Automatic FAIL (score = 0) |
| Crossed orderbooks | CRITICAL | -15 pts |
| Price outliers >100 | HIGH | -10 pts |
| Large gaps >10 | HIGH | -10 pts |
| Missing values | HIGH | -10 pts |
| Duplicates | MEDIUM | -5 pts |
| Trades outside spread >15% | MEDIUM | -5 pts |
| Wide spreads >50 | LOW | -3 pts |

### Grade Assignment

- **A (90-100)**: Excellent - Ready for production
- **B (80-89)**: Good - Minor issues only
- **C (70-79)**: Acceptable - Usable with caveats
- **D (60-69)**: Poor - Re-recording recommended
- **F (0-59)**: Fail - Critical errors, unusable

## Performance

Typical execution times for 6-hour recording (560K quotes, 70K trades, 4M deltas):

| Mode | Sample Rate | Visualizations | Time |
|------|-------------|----------------|------|
| **Fast** | 10000 | Skip | ~2-3 min |
| **Normal** | 1000 | Enabled | ~5-8 min |
| **Thorough** | 500 | Enabled | ~10-15 min |

Memory usage: ~600 MB peak

## Module Architecture

```
validation/
├── advanced_validation.py          # Main CLI orchestrator
├── modules/
│   ├── statistical_analysis.py    # Gap/outlier/spread analysis
│   ├── integrity_checks.py         # Duplicates/missing/cross-validation
│   ├── orderbook_validation.py     # Orderbook structure validation
│   ├── visualization.py            # Chart generation
│   └── quality_scorer.py           # Scoring engine
└── README.md                       # This file
```

## Troubleshooting

### Issue: Validation is too slow

**Solution**: Increase sample rate and skip visualizations:
```bash
python3 advanced_validation.py recording_dir \
    --skip-visualizations \
    --sample-rate 10000
```

### Issue: Out of memory error

**Solution**:
1. Use higher sample rate (10000+)
2. Skip visualizations
3. Process smaller time windows

### Issue: Module import errors

**Solution**: Run from validation directory:
```bash
cd my_trading_system/validation
python3 advanced_validation.py /path/to/recording
```

### Issue: No trade data found

**Expected behavior** - Some recordings only have quotes and deltas. Validation continues with available data.

## Integration Examples

### CI/CD Pipeline

```bash
#!/bin/bash
# validate_recording.sh

RECORDING_DIR=$1

# Run fast validation
python3 advanced_validation.py "$RECORDING_DIR" \
    --skip-visualizations \
    --sample-rate 10000

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Validation passed - data quality acceptable"
    exit 0
else
    echo "❌ Validation failed - quality below threshold"
    exit 1
fi
```

### Python Script

```python
import subprocess
import sys

def validate_recording(recording_dir):
    """Validate recording and return quality score."""
    result = subprocess.run(
        [
            'python3',
            'advanced_validation.py',
            str(recording_dir),
            '--skip-visualizations',
            '--sample-rate', '10000'
        ],
        capture_output=True,
        text=True,
        cwd='my_trading_system/validation'
    )

    return result.returncode == 0

# Usage
if validate_recording('data/recordings/20251119-152837'):
    print("Recording is valid!")
else:
    print("Recording has quality issues")
```

## Developer Notes

### Adding New Validation Checks

1. Add check logic to appropriate module (statistical_analysis, integrity_checks, etc.)
2. Update QualityScorer in `modules/quality_scorer.py` to include new check
3. Update scoring rubric as needed
4. Test with real data

### Customizing Scoring Thresholds

Edit `modules/quality_scorer.py`:

```python
# Pass/fail criteria
PASS_CRITERIA = {
    'min_score': 70,  # Minimum acceptable score
    'max_critical_issues': 0,
    'max_negative_spreads': 0,
    'max_crossed_books': 0,
}
```

## Support

For issues or questions:
1. Check this README
2. Review module docstrings
3. Run with `--verbose` for detailed output
4. Check `results.json` for detailed diagnostics

## License

Part of NautilusTrader benchmark/evaluation suite.
