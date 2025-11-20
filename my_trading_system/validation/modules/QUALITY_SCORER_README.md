# Quality Scoring Engine - Complete Documentation

## Overview

The **QualityScorer** is the Wave 2 component of the advanced validation system that aggregates results from Wave 1 validators and produces a comprehensive quality score (0-100) with actionable recommendations.

**Location:** `my_trading_system/validation/modules/quality_scorer.py`

**Author:** Benjamin Ang / Claude Code (Subagent 5)

**Created:** 2025-11-19

---

## Architecture

### Wave 1 Dependencies

QualityScorer depends on results from three Wave 1 validators:

1. **StatisticalAnalyzer**
   - Gap analysis (temporal discontinuities)
   - Outlier detection (price anomalies)
   - Spread analysis (bid-ask spreads)
   - Volume profiling

2. **IntegrityChecker**
   - Duplicate detection
   - Missing value validation
   - Cross-validation (quotes vs trades)

3. **OrderbookValidator**
   - Price level ordering
   - Crossed book detection
   - Depth consistency

### Quality Scoring Flow

```
Wave 1 Validators → QualityScorer → Score (0-100) + Grade (A-F)
                                  ↓
                    Issue Prioritization (Critical/High/Medium/Low)
                                  ↓
                    Actionable Recommendations
                                  ↓
                    Pass/Fail Criteria Validation
```

---

## Scoring Rubric

### Starting Point
- **100 points** (perfect score)

### Deductions

#### CRITICAL Issues (Automatic Fail or Major Deductions)

| Issue | Points Deducted | Impact |
|-------|----------------|---------|
| **Negative spreads** | -100 (FAIL) | Physically impossible - bid > ask |
| **Crossed orderbooks** | -15 pts | Best bid >= best ask violates market laws |

#### HIGH Priority Issues (Major Deductions)

| Issue | Points Deducted | Impact |
|-------|----------------|---------|
| **Price outliers** (>100) | -10 pts | Data quality issues, possible flash crashes |
| **Large gaps** (>10) | -10 pts | Missing data, connectivity problems |
| **Missing values** | -10 pts | Incomplete dataset |

#### MEDIUM Priority Issues (Moderate Deductions)

| Issue | Points Deducted | Impact |
|-------|----------------|---------|
| **Duplicates** | -5 pts | Data redundancy, volume calculation errors |
| **Cross-validation issues** (>15%) | -5 pts | Quote-trade timing misalignment |

#### LOW Priority Issues (Minor Deductions)

| Issue | Points Deducted | Impact |
|-------|----------------|---------|
| **Wide spreads** (>50) | -3 pts | Low liquidity periods |
| **Orderbook violations** | -2 pts | Minor reconstruction issues |

### Grade Assignment

| Score | Grade | Assessment |
|-------|-------|-----------|
| 90-100 | A | Excellent - Production ready |
| 80-89 | B | Good - Minor issues |
| 70-79 | C | Acceptable - Use with caution |
| 60-69 | D | Poor - Not recommended |
| 0-59 | F | Fail - Re-record required |

---

## Usage

### Basic Usage

```python
from my_trading_system.validation.modules import QualityScorer

# Collect Wave 1 results (from your validators)
statistical_results = {
    'gaps': {...},
    'outliers': {...},
    'spreads': {...},
    'volume': {...}
}

integrity_results = {
    'duplicates': {...},
    'missing_values': {...},
    'cross_validation': {...}
}

orderbook_results = {
    'price_levels': {...},
    'crossed_books': {...},
    'depth': {...}
}

# Initialize scorer
scorer = QualityScorer(
    statistical_results,
    integrity_results,
    orderbook_results
)

# Calculate score
result = scorer.calculate_score()
print(f"Quality Score: {result['score']}/100 ({result['grade']})")
print(f"Issues: {result['issues_found']}")
```

### Get Recommendations

```python
recommendations = scorer.generate_recommendations()
for rec in recommendations:
    print(rec)
```

### Check Minimum Standards

```python
standards = scorer.meets_minimum_standards()
if standards['passes']:
    print("Data meets minimum quality standards!")
else:
    print("Data FAILED minimum standards")
    for check, result in standards['details'].items():
        print(f"  {check}: {result}")
```

### Detailed Report

```python
report = scorer.get_detailed_report()

# Summary
print(report['summary'])

# Score breakdown
print(f"Starting: {report['score_breakdown']['starting_score']}")
for category, details in report['score_breakdown']['deductions'].items():
    print(f"  -{details['points_deducted']} pts: {details['description']}")
print(f"Final: {report['score_breakdown']['final_score']}")

# Issues by priority
for critical_issue in report['issues_by_priority']['critical']:
    print(f"CRITICAL: {critical_issue['description']}")
```

---

## API Reference

### Class: QualityScorer

#### Constructor

```python
QualityScorer(
    statistical_results: Dict[str, Any],
    integrity_results: Dict[str, Any],
    orderbook_results: Dict[str, Any]
)
```

**Parameters:**
- `statistical_results`: Results from StatisticalAnalyzer
- `integrity_results`: Results from IntegrityChecker
- `orderbook_results`: Results from OrderbookValidator

#### Methods

##### calculate_score() -> Dict[str, Any]

Calculates composite quality score.

**Returns:**
```python
{
    'score': int,              # 0-100
    'grade': str,              # A/B/C/D/F
    'issues_found': int,       # Total issues
    'critical_issues': int,    # Critical count
    'high_issues': int,        # High priority count
    'medium_issues': int,      # Medium priority count
    'low_issues': int          # Low priority count
}
```

##### prioritize_issues() -> Dict[str, List[Dict]]

Categorizes issues by priority level.

**Returns:**
```python
{
    'critical': [
        {
            'category': str,
            'description': str,
            'impact': str,
            'count': int
        },
        ...
    ],
    'high': [...],
    'medium': [...],
    'low': [...]
}
```

##### generate_recommendations() -> List[str]

Generates actionable recommendations.

**Returns:**
```python
[
    "EXCELLENT: High-quality data suitable for production use.",
    "Note: 1 medium-priority issue(s) detected - may impact accuracy but not critical",
    ...
]
```

##### meets_minimum_standards() -> Dict[str, Any]

Checks if data meets minimum quality standards.

**Returns:**
```python
{
    'passes': bool,                    # Overall pass/fail
    'score_check': bool,              # Score >= 70
    'critical_issues_check': bool,    # No critical issues
    'negative_spreads_check': bool,   # No negative spreads
    'crossed_books_check': bool,      # No crossed books
    'details': {                      # Detailed check results
        'score': str,
        'critical_issues': str,
        'negative_spreads': str,
        'crossed_books': str
    }
}
```

##### get_detailed_report() -> Dict[str, Any]

Generates comprehensive quality report.

**Returns:**
```python
{
    'score_breakdown': {
        'starting_score': int,
        'deductions': {
            'category_name': {
                'priority': str,
                'category': str,
                'description': str,
                'points_deducted': int
            },
            ...
        },
        'final_score': int
    },
    'issues_by_priority': {
        'critical': [...],
        'high': [...],
        'medium': [...],
        'low': [...]
    },
    'recommendations': [...],
    'pass_criteria': {
        'passes': bool,
        ...
    },
    'summary': str
}
```

---

## Pass/Fail Criteria

### Default Configuration

```python
PASS_CRITERIA = {
    'min_score': 70,                  # Minimum acceptable score
    'max_critical_issues': 0,         # Zero tolerance for critical issues
    'max_negative_spreads': 0,        # Zero tolerance for negative spreads
    'max_crossed_books': 0,           # Zero tolerance for crossed books
    'min_trade_count': 1000,          # Minimum trades required
    'max_missing_percentage': 1.0,    # Max 1% missing data
}
```

### Modification

```python
from my_trading_system.validation.modules import PASS_CRITERIA

# Modify criteria (if needed)
PASS_CRITERIA['min_score'] = 75  # Raise bar to 75
```

---

## Example Scenarios

### Scenario 1: Excellent Quality (Score: 100/100, Grade: A)

**Characteristics:**
- No negative spreads
- No crossed orderbooks
- Minimal outliers (<100)
- Few temporal gaps (<10)
- No missing values
- No duplicates
- Good quote-trade alignment (<15%)
- Normal spreads

**Decision:** APPROVED FOR PRODUCTION

---

### Scenario 2: Critical Failure (Score: 0/100, Grade: F)

**Characteristics:**
- **15 negative spreads detected** (CRITICAL)

**Decision:** REJECTED - Complete re-record required

**Recommendation:**
```
CRITICAL: Data contains physically impossible values. Complete re-record required.
Fix Required: Negative spreads detected: 15 - Check data source configuration
```

---

### Scenario 3: Multiple Issues (Score: 55/100, Grade: F)

**Characteristics:**
- 250 price outliers (High: -10 pts)
- 50 large gaps (High: -10 pts)
- 100 missing values (High: -10 pts)
- 500 duplicates (Medium: -5 pts)
- 18% trades outside spread (Medium: -5 pts)
- 200 wide spreads (Low: -3 pts)
- 8 orderbook violations (Low: -2 pts)

**Total Deduction:** -45 pts

**Decision:** NOT RECOMMENDED - Re-recording suggested

---

## Integration with Workflow

### Complete Validation Pipeline

```python
from pathlib import Path
import pandas as pd
from my_trading_system.validation.modules import (
    StatisticalAnalyzer,
    IntegrityChecker,
    OrderbookValidator,
    QualityScorer
)

# Setup
recording_dir = Path("data/recordings/20251119-152837")
instrument = "SOLUSDT-SPOT.BYBIT"

# Wave 1: Run validators
analyzer = StatisticalAnalyzer(recording_dir)
checker = IntegrityChecker(recording_dir)
validator = OrderbookValidator(recording_dir)

# Load data
quotes_df = pd.read_parquet(f"{recording_dir}/quote_ticks/{instrument}/quote_ticks.parquet")
trades_df = pd.read_parquet(f"{recording_dir}/trade_ticks/{instrument}/trade_ticks.parquet")
deltas_df = pd.read_parquet(f"{recording_dir}/order_book_deltas/{instrument}/order_book_deltas.parquet")

# Collect results
statistical_results = {
    'gaps': analyzer.analyze_gaps(quotes_df, "quotes"),
    'outliers': analyzer.detect_price_outliers(quotes_df),
    'spreads': analyzer.analyze_spreads(quotes_df),
    'volume': analyzer.analyze_volume(trades_df)
}

integrity_results = {
    'duplicates': checker.detect_duplicates(quotes_df, "quotes"),
    'missing_values': checker.check_missing_values(quotes_df, "quotes"),
    'cross_validation': checker.cross_validate_data_types(quotes_df, trades_df)
}

orderbook_results = {
    'price_levels': validator.validate_price_levels(deltas_df, sample_rate=1000),
    'crossed_books': validator.detect_crossed_book(deltas_df, sample_rate=500),
    'depth': validator.analyze_depth_consistency(deltas_df, expected_depth=50)
}

# Wave 2: Calculate quality score
scorer = QualityScorer(
    statistical_results,
    integrity_results,
    orderbook_results
)

score_result = scorer.calculate_score()

# Decision making
if score_result['score'] >= 90:
    print("APPROVED FOR PRODUCTION")
elif score_result['score'] >= 70:
    print("APPROVED WITH CAUTION")
else:
    print("REJECTED - Re-record recommended")

# Save report
report = scorer.get_detailed_report()
with open(f"{recording_dir}/quality_report.txt", "w") as f:
    f.write(report['summary'])
    f.write("\n\nRecommendations:\n")
    for rec in report['recommendations']:
        f.write(f"- {rec}\n")
```

---

## Testing

### Run Built-in Tests

```bash
python3 my_trading_system/validation/modules/quality_scorer.py
```

**Output:**
```
================================================================================
QUALITY SCORING ENGINE - TEST SUITE
================================================================================

Test 1: Excellent Quality Data
--------------------------------------------------------------------------------
Score: 100/100 (Grade: A)
Issues: 0 (Critical: 0, High: 0, Medium: 0, Low: 0)

Recommendations:
  - EXCELLENT: High-quality data suitable for production use.

Minimum Standards:
  Passes: True

... [more test cases]
```

### Run Example Workflow

```bash
PYTHONPATH=/Users/benjaminang/Desktop/nautilus_trader_bens python3 \
  my_trading_system/validation/examples/quality_scoring_example.py
```

---

## Best Practices

### 1. Always Check Critical Issues First

```python
result = scorer.calculate_score()

if result['critical_issues'] > 0:
    print("STOP: Critical issues detected!")
    issues = scorer.prioritize_issues()
    for issue in issues['critical']:
        print(f"  {issue['description']}")
    # Don't proceed with this data
    return
```

### 2. Use Minimum Standards Check

```python
standards = scorer.meets_minimum_standards()

if not standards['passes']:
    print("Data failed minimum standards:")
    for check, result in standards['details'].items():
        if not standards[f"{check}_check"]:
            print(f"  FAILED: {check}")
```

### 3. Generate Reports for Review

```python
report = scorer.get_detailed_report()

# Save to file for manual review
with open("quality_report.txt", "w") as f:
    f.write(f"Quality Report\n")
    f.write(f"=" * 80 + "\n\n")
    f.write(f"Summary:\n{report['summary']}\n\n")
    f.write(f"Score: {report['score_breakdown']['final_score']}/100\n\n")
    f.write(f"Recommendations:\n")
    for rec in report['recommendations']:
        f.write(f"  - {rec}\n")
```

### 4. Customize Thresholds If Needed

```python
# For high-frequency data, adjust outlier threshold
if statistical_results['outliers']['z_outliers_count'] > 200:
    # This might be normal for HFT data
    # Consider filtering before scoring
    pass
```

---

## Troubleshooting

### Issue: Score is 0 but no negative spreads

**Diagnosis:** Check if negative spreads exist in statistical results

```python
print(statistical_results['spreads']['negative_spreads_count'])
```

### Issue: Score seems too low

**Diagnosis:** Review score breakdown

```python
report = scorer.get_detailed_report()
for category, details in report['score_breakdown']['deductions'].items():
    print(f"{details['description']}: -{details['points_deducted']} pts")
```

### Issue: Want different thresholds

**Solution:** Modify detection thresholds in Wave 1 validators, or adjust PASS_CRITERIA

---

## Performance

- **Execution Time:** <1 second for aggregation
- **Memory Usage:** Minimal (only stores issue metadata)
- **Scalability:** Handles results from millions of records

---

## Future Enhancements

Potential improvements for future versions:

1. **Weighted Scoring:** Allow custom weights for different issue types
2. **Configurable Thresholds:** User-defined severity thresholds
3. **Historical Comparison:** Compare quality scores across recordings
4. **Export Formats:** JSON, CSV, HTML report generation
5. **Integration Tests:** Automated testing with real data

---

## Support

For issues or questions:
1. Check Wave 1 validator outputs are correctly formatted
2. Review scoring rubric documentation
3. Run built-in tests to verify installation
4. Check examples for usage patterns

---

**End of Documentation**
