# Visualization Module - Quick Start Guide

**One-page reference for immediate usage**

---

## Installation

```bash
pip install seaborn plotly
```

---

## Basic Usage (3 Lines)

```python
from my_trading_system.validation.modules import create_all_visualizations
from pathlib import Path

charts = create_all_visualizations(quotes_df, trades_df, deltas_df,
                                   output_dir=Path('charts'),
                                   recording_dir=Path('data/recordings/20251119-152801'))
```

---

## Individual Charts

```python
from my_trading_system.validation.modules import DataVisualizer

visualizer = DataVisualizer(recording_dir=Path('.'), output_dir=Path('./charts'))

# 1. Price time series (bid/ask + trades)
price_plot = visualizer.plot_price_timeseries(quotes_df, trades_df)

# 2. Spread distribution (histogram + boxplot)
spread_plot = visualizer.plot_spread_distribution(quotes_df)

# 3. Volume profile (by price + time)
volume_plot = visualizer.plot_volume_profile(trades_df)

# 4. Orderbook heatmap (interactive)
heatmap_plot = visualizer.plot_orderbook_heatmap(deltas_df, sample_rate=100)
```

---

## Data Requirements

```python
# Quotes
quotes_df: timestamp (datetime64[ns, UTC]), bid_price (float64), ask_price (float64)

# Trades
trades_df: timestamp (datetime64[ns, UTC]), price (float64), size (float64)

# Deltas
deltas_df: timestamp (datetime64[ns, UTC]), side (object), size (float64)
```

---

## Output

- **PNG Files**: 300 DPI, publication quality
- **HTML Files**: Interactive Plotly charts
- **Location**: Specified `output_dir`

---

## Performance

- Small datasets (<10K): <1 second
- Large datasets (>100K): ~2 seconds
- Automatic downsampling: Yes

---

## Demo

```bash
python my_trading_system/validation/modules/demo_visualization.py
```

---

## Full Documentation

See `VISUALIZATION_README.md` for comprehensive guide.

---

**Module Location:**
`my_trading_system/validation/modules/visualization.py`

**Author:** Subagent 4 (Claude Code)
**Version:** 1.0.0
**Date:** 2025-11-19
