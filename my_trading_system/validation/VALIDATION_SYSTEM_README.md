# Advanced Validation System

## Overview

The Advanced Validation System is a production-grade framework for comprehensive market data quality assessment in NautilusTrader recordings. It provides automated analysis, scoring, and reporting for recorded market data (quotes, trades, orderbook deltas).

### Key Features

- **Statistical Analysis**: Temporal gap detection, price outlier identification, bid-ask spread analysis, volume profiling
- **Integrity Validation**: Duplicate detection, missing value checks, cross-validation between data types
- **Orderbook Validation**: Structure verification, crossed book detection, depth consistency analysis
- **Quality Scoring**: 0-100 composite score with issue prioritization (critical, high, medium, low)
- **Visualizations**: Publication-quality charts (price evolution, spreads, volume, orderbook heatmaps)
- **HTML Reports**: Professional, self-contained validation reports with embedded charts
- **CLI Interface**: User-friendly command-line tool with progress indicators and detailed logging

### Architecture

```
Advanced Validation System
│
├── Statistical Analysis Module
│   ├── Gap Analysis (temporal discontinuities)
│   ├── Outlier Detection (Z-score, IQR methods)
│   ├── Spread Analysis (negative spreads, wide spreads)
│   └── Volume Profiling (trade size distribution, buy/sell imbalance)
│
├── Integrity Checks Module
│   ├── Duplicate Detection (exact, timestamp-based)
│   ├── Missing Value Checks (null, zero, negative values)
│   └── Cross-Validation (quote-trade alignment)
│
├── Orderbook Validation Module
│   ├── Price Level Ordering (bid descending, ask ascending)
│   ├── Crossed Book Detection (bid >= ask detection)
│   └── Depth Consistency (level count tracking)
│
├── Quality Scoring Engine
│   ├── Composite Score Calculation (0-100 scale)
│   ├── Issue Prioritization (critical → high → medium → low)
│   ├── Grade Assignment (A/B/C/D/F)
│   └── Recommendation Generation
│
├── Visualization Module
│   ├── Price Time Series (bid/ask + trades)
│   ├── Spread Distribution (histogram + box plot)
│   ├── Volume Profile (by price + time)
│   └── Orderbook Heatmap (interactive depth evolution)
│
├── HTML Report Generator
│   ├── Executive Summary (score badge, recommendations)
│   ├── Detailed Results Tables (all metrics)
│   └── Embedded Visualizations (base64 PNG, inline Plotly)
│
└── CLI Orchestrator
    ├── Data Loading (RecordingReader integration)
    ├── Pipeline Coordination (7-stage execution)
    ├── Progress Tracking (verbose mode)
    └── JSON Export (results.json)
```

---

## Quick Start

### Installation

The validation system uses standard NautilusTrader dependencies:

```bash
# Ensure you have the nautilus_trader environment activated
cd /Users/benjaminang/Desktop/nautilus_trader_bens

# All dependencies should already be installed:
# pandas, numpy, matplotlib, seaborn, plotly
```

### Basic Usage

```bash
# Navigate to validation directory
cd my_trading_system/validation

# Run validation on a recording
python advanced_validation.py /path/to/recordings/20251119-152837

# With verbose output
python advanced_validation.py /path/to/recordings/20251119-152837 --verbose

# Skip visualizations for speed
python advanced_validation.py /path/to/recordings/20251119-152837 --skip-visualizations

# Custom output directory
python advanced_validation.py /path/to/recordings/20251119-152837 \
    --output /path/to/reports/validation
```

### Expected Output

```
================================================================================
ADVANCED DATA VALIDATION
================================================================================
Recording: data/recordings/20251119-152837
Output: data/recordings/20251119-152837/validation
Timestamp: 2025-11-19 15:30:45
Sample Rate: 1000
================================================================================

[1/7] Loading data...
    Loaded quotes: 560,356 records (42.7 MB)
    Loaded trades: 0 records (0.0 MB)
    Loaded deltas: 4,013,933 records (306.3 MB)
    Total: 4.6M records in 8.3s

[2/7] Running statistical analysis...
    Gap analysis: 2.15s
    Outlier detection: 1.83s
    Spread analysis: 1.92s
    Statistical analysis complete: 5.90s

[3/7] Running integrity checks...
    Duplicate detection: 1.45s
    Missing value check: 0.98s
    Integrity checks complete: 2.43s

[4/7] Validating orderbook structure...
    Crossed book detection: 45.2s (4014 snapshots)
    Orderbook validation complete: 45.2s

[5/7] Generating visualizations...
    Price time series: 8.2s
    Spread distribution: 3.4s
    Orderbook heatmap: 5.1s
    Visualizations complete: 16.7s

[6/7] Calculating quality score...
    Score: 95/100 (Grade: A)
    Issues found: 0 (Critical: 0, High: 0, Medium: 0, Low: 0)
    Quality scoring complete: 0.1s

[7/7] Generating reports...
    JSON results: data/recordings/20251119-152837/validation/results.json
    Reports complete: 0.2s

================================================================================
VALIDATION COMPLETE
================================================================================

Quality Score: 95/100 (Grade: A)
Issues Found: 0
  Critical: 0
  High: 0
  Medium: 0
  Low: 0

Execution Time: 78.8s

Recommendations:
  - EXCELLENT: High-quality data suitable for production use.

Recommendation: APPROVED - Excellent quality
================================================================================
```

---

## Module Documentation

### Statistical Analysis Module

**File**: `modules/statistical_analysis.py`

**Purpose**: Detect anomalies, gaps, and quality issues in time-series market data.

**Key Features**:
- **Gap Analysis**: Identifies temporal discontinuities (connection drops, market closures)
  - Configurable threshold (default: 1000ms for quotes, 100ms for deltas)
  - Returns: mean/median/max intervals, large gap count, gap locations

- **Outlier Detection**: Z-score and IQR methods for price anomalies
  - Z-score threshold (default: 3.0 standard deviations)
  - IQR-based outlier detection (1.5 * IQR from quartiles)
  - Price jump detection (>5% successive changes)

- **Spread Analysis**: Bid-ask spread quality assessment
  - **CRITICAL**: Negative spread detection (physically impossible)
  - Wide spread identification (>50 bps)
  - Temporal evolution tracking (hourly statistics)

- **Volume Profiling**: Trade size distribution and patterns
  - Total volume, mean/median trade size
  - Buy/sell imbalance (if side data available)
  - Temporal volume distribution (15-minute buckets)

**Usage Example**:
```python
from pathlib import Path
from modules.statistical_analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(Path("data/recordings/20251119-152837"))

# Analyze quotes
quotes_df = pd.read_parquet("quotes.parquet")
gap_results = analyzer.analyze_gaps(quotes_df, "quotes", max_expected_gap_ms=1000)
spread_results = analyzer.analyze_spreads(quotes_df)
outlier_results = analyzer.detect_price_outliers(quotes_df, z_threshold=3.0)

print(f"Large gaps: {gap_results['num_large_gaps']}")
print(f"Negative spreads: {spread_results['negative_spreads_count']}")  # Must be 0!
print(f"Price outliers: {outlier_results['z_outliers_count']}")
```

---

### Integrity Checks Module

**File**: `modules/integrity_checks.py`

**Purpose**: Validate data completeness, uniqueness, and consistency.

**Key Features**:
- **Duplicate Detection**:
  - Exact duplicates (all columns match)
  - Timestamp duplicates (same timestamp, different data)
  - Trade ID duplicates (for trades only)

- **Missing Value Checks**:
  - Null/NaN detection in any column
  - Invalid prices (zero or negative)
  - Invalid sizes (zero or negative)

- **Cross-Validation**:
  - Quote-trade temporal alignment
  - Trade prices within bid-ask spread verification
  - Uses `merge_asof` for efficient temporal joins

**Usage Example**:
```python
from modules.integrity_checks import IntegrityChecker

checker = IntegrityChecker(Path("data/recordings/20251119-152837"))

# Check for duplicates
dup_results = checker.detect_duplicates(quotes_df, "quotes")
print(f"Exact duplicates: {dup_results['exact_duplicates_count']}")

# Check missing values
missing_results = checker.check_missing_values(quotes_df, "quotes")
print(f"Invalid records: {missing_results['total_invalid_count']}")

# Cross-validate quotes and trades
cross_results = checker.cross_validate_data_types(quotes_df, trades_df)
print(f"Trades outside spread: {cross_results['trades_outside_spread_percentage']:.2f}%")
```

---

### Orderbook Validation Module

**File**: `modules/orderbook_validation.py`

**Purpose**: Validate orderbook structure and detect market microstructure anomalies.

**Key Features**:
- **Price Level Ordering**:
  - Bids must be in descending order (best bid = highest price)
  - Asks must be in ascending order (best ask = lowest price)
  - Violations indicate data corruption

- **Crossed Book Detection**:
  - Detects when best_bid >= best_ask
  - **CRITICAL ERROR**: Impossible in real markets (arbitrage)
  - Indicates data corruption or timing issues

- **Depth Consistency**:
  - Tracks number of price levels over time
  - Identifies liquidity degradation
  - Expected depth: 50 levels (configurable)

**Algorithm**: Reconstructs orderbook snapshots from delta streams:
1. Collect all deltas up to timestamp T
2. For each price level, keep only most recent action
3. Filter out DELETE actions (levels no longer exist)
4. Split into bids (BUY) and asks (SELL)
5. Sort bids descending, asks ascending
6. Validate ordering and spread

**Performance**: Uses sampling to handle large datasets:
- Sample every Nth delta (default: 1000)
- Provides statistical significance without full processing
- Reduces 4M deltas to ~4K validation checkpoints

**Usage Example**:
```python
from modules.orderbook_validation import OrderbookValidator

validator = OrderbookValidator(Path("data/recordings/20251119-152837"))

# Detect crossed orderbooks
crossed_results = validator.detect_crossed_book(deltas_df, sample_rate=500)
if crossed_results['crossed_books_detected'] > 0:
    print("CRITICAL: Crossed orderbooks detected!")
    print(f"Count: {crossed_results['crossed_books_detected']}")
    print(f"Max violation: {crossed_results['max_cross_amount']}")
```

---

### Quality Scoring Engine

**File**: `modules/quality_scorer.py`

**Purpose**: Aggregate validation results into actionable quality score.

**Scoring Rubric**:
- Start at 100 (perfect)
- Deduct points for issues:
  - **Negative spreads**: Automatic FAIL (score = 0)
  - **Crossed orderbooks**: -15 pts (CRITICAL)
  - **Price outliers >100**: -10 pts (High)
  - **Large gaps >10**: -10 pts (High)
  - **Missing values**: -10 pts (High)
  - **Duplicates**: -5 pts (Medium)
  - **Trades outside spread >15%**: -5 pts (Medium)
  - **Wide spreads >50**: -3 pts (Low)

**Grade Assignment**:
- **A (90-100)**: Excellent - Production ready
- **B (80-89)**: Good - Minor issues, acceptable
- **C (70-79)**: Acceptable - Use with caveats
- **D (60-69)**: Poor - Re-recording recommended
- **F (0-59)**: Fail - Critical errors, unusable

**Pass/Fail Criteria**:
- Minimum score: 70
- No critical issues
- No negative spreads
- No crossed orderbooks

**Usage Example**:
```python
from modules.quality_scorer import QualityScorer

scorer = QualityScorer(
    statistical_results=statistical_results,
    integrity_results=integrity_results,
    orderbook_results=orderbook_results
)

# Calculate score
result = scorer.calculate_score()
print(f"Score: {result['score']}/100 (Grade: {result['grade']})")

# Get recommendations
recommendations = scorer.generate_recommendations()
for rec in recommendations:
    print(f"- {rec}")

# Check pass criteria
standards = scorer.meets_minimum_standards()
if not standards['passes']:
    print("Data does not meet minimum quality standards!")
```

---

### Visualization Module

**File**: `modules/visualization.py`

**Purpose**: Generate publication-quality charts for data analysis.

**Charts Generated**:
1. **Price Time Series** (`price_timeseries.png`):
   - Dual subplot: bid/ask prices + bid-ask spread
   - Trade scatter overlay
   - Summary statistics
   - 300 DPI PNG output

2. **Spread Distribution** (`spread_distribution.png`):
   - Histogram of spread values
   - Box plot for outlier detection
   - Quartile statistics

3. **Volume Profile** (`volume_profile.png`):
   - Volume by price level (horizontal bars)
   - Volume over time (15-minute buckets)
   - Buy/sell breakdown (if available)

4. **Orderbook Heatmap** (`orderbook_heatmap.html`):
   - Interactive Plotly chart
   - Bid/ask depth evolution
   - Depth imbalance tracking
   - Zoom, pan, hover tooltips

**Performance**:
- Auto-downsampling for large datasets
- Quotes: Max 10K points plotted
- Orderbook: Configurable sample rate

**Usage Example**:
```python
from modules.visualization import DataVisualizer

visualizer = DataVisualizer(
    recording_dir=Path("data/recordings/20251119-152837"),
    output_dir=Path("validation/charts")
)

# Generate all charts
price_path = visualizer.plot_price_timeseries(quotes_df, trades_df)
spread_path = visualizer.plot_spread_distribution(quotes_df)
volume_path = visualizer.plot_volume_profile(trades_df)
heatmap_path = visualizer.plot_orderbook_heatmap(deltas_df, sample_rate=100)

print(f"Charts saved to: {visualizer.output_dir}")
```

---

### HTML Report Generator

**File**: `modules/html_report.py`

**Purpose**: Create professional, self-contained HTML validation reports.

**Report Structure**:
1. **Header**: Recording ID, timestamp, metadata
2. **Executive Summary**: Score badge, grade, recommendations
3. **Quality Score**: Breakdown by category, issues by priority
4. **Statistical Analysis**: Gaps, outliers, spreads
5. **Integrity Checks**: Duplicates, missing values, cross-validation
6. **Orderbook Validation**: Crossed books, depth, price levels
7. **Visualizations**: Embedded PNG (base64) and interactive Plotly
8. **Footer**: System info, report version

**Features**:
- Single HTML file (no external dependencies)
- All images embedded as base64 data URLs
- Plotly charts embedded as iframes
- Color-coded quality indicators
- Responsive design (desktop, tablet, print)
- Professional styling with CSS
- Printable format (@media print)

**Usage Example**:
```python
from modules.html_report import HTMLReportGenerator

generator = HTMLReportGenerator(
    validation_results={
        'statistical': statistical_results,
        'integrity': integrity_results,
        'orderbook': orderbook_results,
        'quality_score': quality_score_results
    },
    viz_paths={
        'price_timeseries': Path('charts/price_timeseries.png'),
        'spread_distribution': Path('charts/spread_distribution.png'),
        'volume_profile': Path('charts/volume_profile.png'),
        'orderbook_heatmap': Path('charts/orderbook_heatmap.html')
    },
    recording_dir=Path('data/recordings/20251119-152837'),
    output_path=Path('reports/validation_report.html')
)

report_path = generator.generate_report()
print(f"Report generated: {report_path}")
```

---

## Usage Examples

### Example 1: Basic Validation

```bash
cd my_trading_system/validation
python advanced_validation.py ../../data/recordings/20251119-152837
```

This runs the complete validation pipeline and saves results to:
- `data/recordings/20251119-152837/validation/results.json`
- `data/recordings/20251119-152837/validation/*.png` (charts)
- `data/recordings/20251119-152837/validation/*.html` (interactive charts)

### Example 2: Fast Validation (CI/CD)

```bash
python advanced_validation.py ../../data/recordings/20251119-152837 \
    --skip-visualizations \
    --sample-rate 10000

# Check exit code
if [ $? -eq 0 ]; then
    echo "Data quality acceptable"
else
    echo "Data quality below threshold"
fi
```

Use `--skip-visualizations` to skip chart generation (saves ~15-20 seconds).
Use higher `--sample-rate` for faster orderbook validation (less thorough).

### Example 3: Custom Output Directory

```bash
python advanced_validation.py ../../data/recordings/20251119-152837 \
    --output ../../reports/validation_$(date +%Y%m%d) \
    --verbose
```

### Example 4: Python API Usage

```python
from pathlib import Path
from validation.advanced_validation import AdvancedDataValidator

# Initialize validator
validator = AdvancedDataValidator(
    recording_dir=Path("data/recordings/20251119-152837"),
    verbose=True,
    sample_rate=1000
)

# Run validation
results = validator.run_all_validations(skip_visualizations=False)

# Access results
score = results['quality_score']['score']
grade = results['quality_score']['grade']
negative_spreads = results['statistical_results']['spreads']['negative_spreads_count']
crossed_books = results['orderbook_results']['crossed_books']['crossed_books_detected']

# Make decisions
if negative_spreads > 0:
    print("CRITICAL: Negative spreads detected - re-record required!")
    exit(1)
elif score < 70:
    print("WARNING: Quality below threshold - review recommended")
    exit(1)
else:
    print("PASS: Data quality acceptable")
    exit(0)
```

---

## Interpretation Guide

### Understanding Quality Scores

**Score Ranges**:
- **90-100 (A)**: Excellent data quality. Suitable for production trading.
- **80-89 (B)**: Good quality with minor issues. Acceptable for backtesting.
- **70-79 (C)**: Acceptable quality with caveats. Monitor backtest behavior.
- **60-69 (D)**: Poor quality. Re-recording strongly recommended.
- **0-59 (F)**: Failed validation. Critical errors present. Do not use.

### What Each Check Means

**Negative Spreads** (CRITICAL):
- **What**: Ask price < bid price
- **Why critical**: Physically impossible in real markets (instant arbitrage)
- **Cause**: Data corruption, system bug, clock skew
- **Action**: IMMEDIATE re-record required

**Crossed Orderbooks** (CRITICAL):
- **What**: Best bid >= best ask
- **Why critical**: Violates market laws (arbitrage opportunity)
- **Cause**: Exchange system malfunction, data timing issues
- **Action**: Re-record recommended, verify exchange status

**Price Outliers** (HIGH):
- **What**: Prices >3 standard deviations from mean
- **Why important**: May indicate flash crashes, bad ticks, or data corruption
- **Cause**: Exchange errors, liquidity events, data feed issues
- **Action**: Review outlier timestamps, consider filtering extreme values

**Large Gaps** (HIGH):
- **What**: Time intervals >threshold between successive updates
- **Why important**: Missing data during gaps affects backtest accuracy
- **Cause**: Network issues, exchange downtime, system overload
- **Action**: Check network logs, verify recording uptime

**Missing Values** (HIGH):
- **What**: Null, zero, or negative prices/sizes
- **Why important**: Incomplete dataset, calculations may fail
- **Cause**: Data feed issues, parsing errors, system bugs
- **Action**: Investigate data source, consider re-recording

**Duplicates** (MEDIUM):
- **What**: Identical records (same timestamp + data)
- **Why moderate**: Inflates volume, may skew statistics
- **Cause**: Data feed duplication, replay bugs
- **Action**: Deduplicate data, investigate feed configuration

**Trades Outside Spread** (MEDIUM):
- **What**: Trade prices outside bid-ask spread
- **Why moderate**: Indicates quote-trade timing misalignment
- **Cause**: Network latency, clock skew, delayed updates
- **Action**: Acceptable if <15%, verify system clocks

**Wide Spreads** (LOW):
- **What**: Spreads >50 basis points
- **Why low priority**: Expected during low liquidity periods
- **Cause**: Market conditions (off-hours, low volume)
- **Action**: Document liquidity conditions, adjust strategy expectations

### When to Re-Record Data

**MUST re-record**:
- Negative spreads detected (any count)
- Score < 60 (Grade F)
- Multiple critical issues

**SHOULD re-record**:
- Crossed orderbooks detected (>5 instances)
- Score 60-69 (Grade D)
- High issue count (>5 high-priority)

**ACCEPTABLE to use**:
- Score >= 70 (Grade C or better)
- No critical issues
- Minor/medium issues only

---

## Troubleshooting

### Common Errors

**Error: Recording directory not found**
```
ERROR: Recording directory not found: /path/to/recordings/xyz
```
**Solution**: Verify path exists and is correct. Use absolute paths.

**Error: No instruments found**
```
ERROR: No instruments found in /path/to/recordings/xyz
```
**Solution**: Recording may be empty or corrupted. Check recording process completed successfully.

**Error: Memory error during loading**
```
MemoryError: Unable to allocate array
```
**Solution**:
- Increase system memory
- Use higher `--sample-rate` to reduce memory usage
- Use `--skip-visualizations` to save memory

**Error: Visualization module import failure**
```
ModuleNotFoundError: No module named 'plotly'
```
**Solution**: Install missing dependency: `pip install plotly`

### Performance Optimization

**Slow validation (>10 minutes)**:
- Use `--skip-visualizations` (saves 15-20 seconds)
- Increase `--sample-rate` to 5000 or 10000 (reduces orderbook validation time)
- Run on machine with SSD for faster I/O

**Large output files**:
- Visualizations disabled: ~1MB JSON
- With visualizations: ~10-15MB (embedded images)
- HTML reports: ~5-20MB (base64 images + Plotly)

**Memory usage**:
- Typical dataset (4M deltas): ~2-3GB RAM
- Large datasets (>10M deltas): ~5-8GB RAM
- Use sampling for very large datasets

### Known Limitations

**Orderbook Reconstruction**:
- Sampling may miss transient issues
- Lower sample rates = less thorough validation
- Full reconstruction is prohibitively expensive (>30 minutes)

**Cross-Validation**:
- Requires both quotes and trades
- Timing tolerance (default: 1 second) may be too loose for HFT
- Does not handle fragmented liquidity (multiple venues)

**Visualization**:
- Auto-downsampling may miss detail in large datasets
- Plotly charts can be large (>5MB) for interactive features
- Print support limited for interactive charts

---

## Development

### Contributing Guidelines

**Adding New Validation Checks**:

1. **Extend appropriate module**:
   - Statistical issues → `statistical_analysis.py`
   - Data integrity issues → `integrity_checks.py`
   - Orderbook issues → `orderbook_validation.py`

2. **Follow module patterns**:
   ```python
   def check_new_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
       """
       Check for new validation criteria.

       Parameters
       ----------
       df : pd.DataFrame
           Input data

       Returns
       -------
       dict
           Validation results with keys:
           - metric_count: int
           - metric_details: list[dict]
           - metric_percentage: float
       """
       # Implement validation logic
       return results
   ```

3. **Update QualityScorer**:
   - Add deduction logic to `quality_scorer.py`
   - Define priority level (critical/high/medium/low)
   - Set point deduction value

4. **Add visualization** (if needed):
   - Create plot method in `visualization.py`
   - Follow naming convention: `plot_<metric_name>`
   - Return path to saved file

5. **Test thoroughly**:
   - Add unit tests
   - Test with real data
   - Verify scoring impact

### Extending the System

**Custom Scoring Rubric**:

Edit `modules/quality_scorer.py`:
```python
# Modify PASS_CRITERIA at top of file
PASS_CRITERIA = {
    'min_score': 75,  # Raise minimum score
    'max_critical_issues': 0,
    'max_negative_spreads': 0,
    'max_crossed_books': 0,
    'min_trade_count': 5000,  # Require more trades
    'max_missing_percentage': 0.5,  # Stricter missing value threshold
}

# Modify deduction logic in QualityScorer class
def _check_large_gaps(self):
    """Check for large temporal gaps (HIGH priority)."""
    gap_results = self.statistical_results.get('gaps', {})
    large_gaps = gap_results.get('num_large_gaps', 0)

    # More strict: deduct for any gaps >5
    if large_gaps > 5:  # Changed from 10
        self.score -= 15  # Increased from 10
        self.issues.append(Issue(...))
```

**Custom Output Formats**:

Add new report generator:
```python
# modules/pdf_report.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class PDFReportGenerator:
    def generate_report(self) -> str:
        """Generate PDF report."""
        # Implement PDF generation
        pass
```

**Integration with CI/CD**:

```yaml
# .github/workflows/validate-data.yml
name: Validate Recording

on:
  push:
    paths:
      - 'data/recordings/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pandas numpy matplotlib plotly

      - name: Run validation
        run: |
          python my_trading_system/validation/advanced_validation.py \
            data/recordings/latest \
            --skip-visualizations \
            --sample-rate 5000

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: validation-results
          path: data/recordings/latest/validation/results.json
```

---

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, Windows
- **Python**: 3.10+
- **RAM**: 4GB
- **Storage**: 1GB for validation outputs
- **CPU**: 2 cores

### Recommended Specifications
- **RAM**: 8GB+
- **Storage**: SSD for fast I/O
- **CPU**: 4+ cores for parallel processing

### Dependencies
- `pandas >= 1.5.0`
- `numpy >= 1.23.0`
- `matplotlib >= 3.6.0`
- `seaborn >= 0.12.0`
- `plotly >= 5.11.0`

All dependencies are included in NautilusTrader environment.

---

## Version History

### v1.0.0 (2025-11-19)
- Initial release
- 7 validation modules
- CLI interface
- HTML report generation
- Quality scoring engine
- Comprehensive documentation

**Created by**: Benjamin Ang / Claude Code (Anthropic)
**Project**: Trading Engines - NautilusTrader Advanced Validation
**License**: MIT

---

## Support & Contact

For issues, questions, or contributions, please contact the development team or create an issue in the project repository.

**Documentation Last Updated**: 2025-11-19
