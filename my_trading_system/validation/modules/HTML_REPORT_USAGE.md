# HTML Report Generator - Usage Guide

## Overview

The `HTMLReportGenerator` class creates professional, self-contained HTML validation reports for market data quality assessment. The report includes all validation results, embedded visualizations, and professional styling.

## Features

- **Self-contained**: Single HTML file with no external dependencies
- **Embedded Visualizations**: PNG charts as base64, Plotly HTML as iframes
- **Color-coded Quality Indicators**: A=green, B=light-green, C=orange, D/F=red
- **Responsive Design**: Works on desktop, tablet, and print
- **Professional Styling**: Modern CSS with hover effects and gradients
- **File Size Optimized**: Typically <10MB with full charts

## Quick Start

```python
from pathlib import Path
from my_trading_system.validation.modules import HTMLReportGenerator

# Prepare validation results
validation_results = {
    'statistical': statistical_results,    # From StatisticalAnalyzer
    'integrity': integrity_results,        # From IntegrityChecker
    'orderbook': orderbook_results,        # From OrderbookValidator
    'quality_score': quality_score_results # From QualityScorer
}

# Prepare visualization paths
viz_paths = {
    'price_timeseries': Path('charts/price_timeseries.png'),
    'spread_distribution': Path('charts/spread_distribution.png'),
    'volume_profile': Path('charts/volume_profile.png'),
    'orderbook_heatmap': Path('charts/orderbook_heatmap.html')
}

# Generate report
generator = HTMLReportGenerator(
    validation_results=validation_results,
    viz_paths=viz_paths,
    recording_dir=Path('data/recordings/20251119-152837'),
    output_path=Path('reports/validation_report.html')
)

report_path = generator.generate_report()
print(f"Report generated: {report_path}")
```

## Full Validation Pipeline

Complete workflow integrating all validation modules:

```python
from pathlib import Path
import pandas as pd
from my_trading_system.validation.modules import (
    StatisticalAnalyzer,
    IntegrityChecker,
    OrderbookValidator,
    QualityScorer,
    DataVisualizer,
    HTMLReportGenerator
)

# Define paths
recording_dir = Path('data/recordings/20251119-152837')
output_dir = Path('validation_reports')
charts_dir = output_dir / 'charts'
output_dir.mkdir(parents=True, exist_ok=True)

# Load data
quotes_df = pd.read_parquet(recording_dir / 'quote_ticks.parquet')
trades_df = pd.read_parquet(recording_dir / 'trade_ticks.parquet')
deltas_df = pd.read_parquet(recording_dir / 'orderbook_deltas.parquet')

# Step 1: Statistical Analysis
print("Running statistical analysis...")
stat_analyzer = StatisticalAnalyzer(recording_dir)
gap_results = stat_analyzer.analyze_gaps(quotes_df, 'quotes')
outlier_results = stat_analyzer.detect_price_outliers(quotes_df)
spread_results = stat_analyzer.analyze_spreads(quotes_df)

statistical_results = {
    'gaps': gap_results,
    'outliers': outlier_results,
    'spreads': spread_results
}

# Step 2: Integrity Checks
print("Running integrity checks...")
integrity_checker = IntegrityChecker(recording_dir)
dup_results = integrity_checker.detect_duplicates(quotes_df, 'quotes')
missing_results = integrity_checker.check_missing_values(quotes_df, 'quotes')
cross_val_results = integrity_checker.cross_validate_data_types(quotes_df, trades_df)

integrity_results = {
    'duplicates': dup_results,
    'missing_values': missing_results,
    'cross_validation': cross_val_results
}

# Step 3: Orderbook Validation
print("Running orderbook validation...")
ob_validator = OrderbookValidator(recording_dir)
price_level_results = ob_validator.validate_price_levels(deltas_df, sample_rate=500)
crossed_results = ob_validator.detect_crossed_book(deltas_df, sample_rate=500)
depth_results = ob_validator.analyze_depth_consistency(deltas_df, expected_depth=50)

orderbook_results = {
    'price_levels': price_level_results,
    'crossed_books': crossed_results,
    'depth': depth_results
}

# Step 4: Quality Scoring
print("Calculating quality score...")
scorer = QualityScorer(statistical_results, integrity_results, orderbook_results)
score_result = scorer.calculate_score()
detailed_report = scorer.get_detailed_report()

quality_score_results = {
    'score': score_result['score'],
    'grade': score_result['grade'],
    'issues_found': score_result['issues_found'],
    'critical_issues': score_result['critical_issues'],
    'high_issues': score_result['high_issues'],
    'medium_issues': score_result['medium_issues'],
    'low_issues': score_result['low_issues'],
    'detailed_report': detailed_report
}

# Step 5: Generate Visualizations
print("Generating visualizations...")
visualizer = DataVisualizer(recording_dir, charts_dir)
price_plot = visualizer.plot_price_timeseries(quotes_df, trades_df)
spread_plot = visualizer.plot_spread_distribution(quotes_df)
volume_plot = visualizer.plot_volume_profile(trades_df)
heatmap_plot = visualizer.plot_orderbook_heatmap(deltas_df, sample_rate=100)

viz_paths = {
    'price_timeseries': Path(price_plot),
    'spread_distribution': Path(spread_plot),
    'volume_profile': Path(volume_plot),
    'orderbook_heatmap': Path(heatmap_plot)
}

# Step 6: Generate HTML Report
print("Generating HTML report...")
generator = HTMLReportGenerator(
    validation_results={
        'statistical': statistical_results,
        'integrity': integrity_results,
        'orderbook': orderbook_results,
        'quality_score': quality_score_results
    },
    viz_paths=viz_paths,
    recording_dir=recording_dir,
    output_path=output_dir / f'validation_report_{recording_dir.name}.html'
)

report_path = generator.generate_report()
print(f"\n✅ Validation complete!")
print(f"📄 Report: {report_path}")
print(f"📊 Score: {score_result['score']}/100 (Grade: {score_result['grade']})")
print(f"\nOpen in browser: file://{Path(report_path).absolute()}")
```

## Report Structure

The generated HTML report contains the following sections:

### 1. Header
- Recording ID
- Generation timestamp
- Report version

### 2. Executive Summary
- Large color-coded score badge (A/B/C/D/F)
- Actionable recommendations
- Total issues count

### 3. Data Quality Score
- **Score Breakdown**: Starting score, deductions by category, final score
- **Issues by Priority**: Critical/high/medium/low with descriptions
- **Pass Criteria Check**: Overall pass/fail status

### 4. Statistical Analysis
- **Temporal Gap Analysis**: Large gaps, max/mean/median/std dev
- **Price Outlier Detection**: Z-score outliers, price jumps
- **Bid-Ask Spread Analysis**: Negative spreads, wide spreads, statistics

### 5. Integrity Checks
- **Duplicate Detection**: Exact duplicates, timestamp duplicates
- **Missing/Invalid Values**: Null, zero, negative values
- **Cross-Validation**: Trades outside spread

### 6. Orderbook Validation
- **Price Level Ordering**: Bid/ask ordering violations
- **Crossed Orderbook Detection**: Critical error detection
- **Depth Consistency**: Mean/min/max depth levels

### 7. Visualizations
- **Price Evolution**: Bid/ask prices with trades overlay
- **Spread Distribution**: Histogram and box plot
- **Volume Profile**: Volume by price and time
- **Orderbook Heatmap**: Interactive depth evolution (Plotly)

### 8. Footer
- System information
- Report version
- Author credits

## Customization

### Custom CSS Styling

Modify the color palette in `_get_css_styles()`:

```python
:root {
    --color-excellent: #2E7D32;   /* Dark green (A) */
    --color-good: #4CAF50;        /* Green (B) */
    --color-acceptable: #FFA726;  /* Orange (C) */
    --color-poor: #EF5350;        /* Red (D) */
    --color-fail: #C62828;        /* Dark red (F) */
    --color-primary: #1976D2;     /* Blue (primary) */
}
```

### Add Custom Sections

Extend the `_generate_html()` method:

```python
def _generate_html(self) -> str:
    # ... existing code ...
    custom_html = self._generate_custom_section()

    html = f"""<!DOCTYPE html>
    <html>
    ...
    {custom_html}
    ...
    </html>"""

    return html

def _generate_custom_section(self) -> str:
    return """
    <section class="custom">
        <h2>Custom Analysis</h2>
        <!-- Your custom content -->
    </section>
    """
```

### Modify Table Formatting

Override `_format_table()` method or create custom formatters:

```python
def _format_custom_table(self, data: Dict[str, Any]) -> str:
    html = """
    <table class="custom-table">
        <thead>
            <tr>
                <th>Custom Column 1</th>
                <th>Custom Column 2</th>
            </tr>
        </thead>
        <tbody>
    """

    for key, value in data.items():
        html += f"""
            <tr>
                <td>{key}</td>
                <td>{value}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html
```

## Best Practices

1. **Always run visualizations first**: Generate all charts before creating the report
2. **Check file sizes**: Ensure visualizations are optimized (<5MB each)
3. **Validate paths**: Verify all visualization files exist before generating report
4. **Use absolute paths**: Always use `Path` objects and `.absolute()` for file paths
5. **Test in browser**: Open generated HTML in Chrome/Firefox/Safari to verify rendering

## Troubleshooting

### Report file size too large (>10MB)

**Solution**: Downsample visualizations more aggressively

```python
# In DataVisualizer
visualizer.plot_orderbook_heatmap(deltas_df, sample_rate=500)  # Increase from 100
```

### Images not displaying

**Solution**: Verify image paths exist and are readable

```python
for key, path in viz_paths.items():
    if not Path(path).exists():
        print(f"Warning: {key} file not found at {path}")
```

### Plotly chart not interactive

**Solution**: Check iframe srcdoc attribute escaping

```python
# In _embed_plotly_chart()
plotly_html_escaped = plotly_html.replace('"', '&quot;').replace("'", '&#39;')
```

### CSS not applying

**Solution**: Verify CSS is embedded in `<style>` tag within `<head>`

```python
# Check _get_css_styles() returns valid CSS
css = self._get_css_styles()
print(len(css))  # Should be ~15KB
```

## Performance

- **Generation Time**: <10 seconds for full report
- **File Size**: 5-10MB with all visualizations
- **Memory Usage**: <500MB peak during generation
- **Browser Load Time**: <2 seconds in modern browsers

## Dependencies

- `base64`: Built-in (Python 3.x)
- `pathlib`: Built-in (Python 3.x)
- `datetime`: Built-in (Python 3.x)
- No external dependencies for report generation

## Version History

- **v1.0.0** (2025-11-19): Initial release
  - Self-contained HTML reports
  - Embedded PNG and Plotly visualizations
  - Professional styling with responsive design
  - Print support

## Support

For issues or questions:
1. Check the test suite: `test_html_report_integration.py`
2. Review module docstrings: `html_report.py`
3. Examine generated reports for troubleshooting

## Example Output

See `test_integration_report.html` for a complete example with all features demonstrated.
