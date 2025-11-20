# Shared Utilities

This directory contains reusable code used across notebooks, strategies, and scripts.

## Structure

```
shared/
├── data/           # Data loading utilities
├── backtesting/    # Backtesting helpers
├── analysis/       # Performance analysis
├── plotting/       # Visualization utilities
└── utils/          # General utilities
```

## Purpose

Code in `shared/` is:
- **Reusable** - Used in multiple places
- **Stable** - Well-tested, doesn't change often
- **Cross-cutting** - Not specific to one strategy or domain

## Components

### Data (`data/`)

Utilities for loading and managing data.

**Example modules:**
```python
# shared/data/loaders.py
def load_binance_data(symbol, start_date, end_date, timeframe='1m'):
    """Load data from Binance"""
    pass

def load_from_catalog(instrument_id, bar_type, catalog_path):
    """Load from NautilusTrader catalog"""
    pass

# shared/data/processors.py
def resample_bars(bars, new_timeframe):
    """Resample to different timeframe"""
    pass

def clean_data(df):
    """Remove outliers, fill gaps"""
    pass
```

**Usage:**
```python
# In notebooks or scripts
from shared.data.loaders import load_binance_data

df = load_binance_data('BTCUSDT', '2024-01-01', '2024-11-19')
```

### Backtesting (`backtesting/`)

Reusable backtesting utilities.

**Example modules:**
```python
# shared/backtesting/runner.py
class BacktestRunner:
    """Reusable backtest runner"""

    def __init__(self, catalog_path):
        self.catalog = ParquetDataCatalog(catalog_path)

    def run(self, strategy_class, config, instruments):
        """Run backtest"""
        engine = BacktestEngine()
        # Setup and run
        return BacktestResults(engine)

    def optimize(self, strategy_class, param_grid):
        """Parameter optimization"""
        pass

# shared/backtesting/results.py
class BacktestResults:
    """Wrapper for backtest results"""

    def __init__(self, engine):
        self.engine = engine

    def summary(self):
        """Return summary statistics"""
        pass

    def plot_equity(self):
        """Plot equity curve"""
        pass
```

**Usage:**
```python
# In notebooks
from shared.backtesting.runner import BacktestRunner

runner = BacktestRunner('data/catalog')
results = runner.run(MyStrategy, config, ['BTCUSDT'])
```

### Analysis (`analysis/`)

Performance and trade analysis.

**Example modules:**
```python
# shared/analysis/performance.py
def calculate_sharpe_ratio(returns):
    """Calculate Sharpe ratio"""
    pass

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    pass

def calculate_win_rate(trades):
    """Calculate win rate"""
    pass

# shared/analysis/trades.py
def analyze_trades(fills_report):
    """Analyze trade statistics"""
    return {
        'total_trades': len(fills_report),
        'win_rate': calculate_win_rate(fills_report),
        'avg_win': ...,
        'avg_loss': ...,
    }
```

**Usage:**
```python
from shared.analysis.performance import calculate_sharpe_ratio

sharpe = calculate_sharpe_ratio(returns)
```

### Plotting (`plotting/`)

Visualization utilities.

**Example modules:**
```python
# shared/plotting/charts.py
def plot_price_and_signals(df, buy_signals, sell_signals):
    """Plot price with entry/exit signals"""
    fig = go.Figure()
    # Add traces
    return fig

def plot_equity_curve(equity_series):
    """Plot equity curve with drawdowns"""
    pass

# shared/plotting/backtest.py
def plot_backtest_results(results):
    """Comprehensive backtest visualization"""
    # Equity curve, drawdown, returns distribution, etc.
    pass
```

**Usage:**
```python
from shared.plotting.charts import plot_equity_curve

fig = plot_equity_curve(equity)
fig.show()
```

### Utils (`utils/`)

General utilities.

**Example modules:**
```python
# shared/utils/logging_config.py
def setup_logging(log_level='INFO', log_file=None):
    """Configure logging"""
    pass

# shared/utils/helpers.py
def calculate_position_size(account_balance, risk_pct, stop_distance):
    """Calculate position size"""
    pass

def parse_timeframe(timeframe_str):
    """Parse timeframe string (1m, 5m, 1h, etc.)"""
    pass
```

## When to Add Code to Shared

### ✅ Add to shared/ when:
- Used in 3+ places
- General-purpose utility
- Well-tested and stable
- Not domain-specific

### ❌ Don't add to shared/ when:
- Only used in one place (keep it local)
- Experimental/changing frequently (keep in notebook)
- Domain-specific (put in domain module like `ml/`, `alternative_data/`)

## Example: Evolution of Shared Code

### Stage 1: Code in Notebook
```python
# notebooks/strategy_ema_cross.ipynb
# Cell: Load data
df = pd.read_parquet('data/BTCUSDT.parquet')
df = df[df['timestamp'] >= '2024-01-01']
df = df[df['timestamp'] <= '2024-11-19']
```

### Stage 2: Used in Multiple Notebooks
```python
# Copy-pasted in 3 notebooks - time to extract!
```

### Stage 3: Extract to Shared
```python
# shared/data/loaders.py
def load_data_range(file_path, start_date, end_date):
    df = pd.read_parquet(file_path)
    df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    return df

# Now all notebooks use:
from shared.data.loaders import load_data_range
df = load_data_range('data/BTCUSDT.parquet', '2024-01-01', '2024-11-19')
```

## Best Practices

### 1. Clear Function Names
```python
# Good: Descriptive
def calculate_position_size(balance, risk_pct, stop_distance):
    pass

# Bad: Vague
def calc(a, b, c):
    pass
```

### 2. Type Hints
```python
from typing import List, Dict
import pandas as pd

def load_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    pass
```

### 3. Documentation
```python
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate annualized Sharpe ratio.

    Args:
        returns: Series of returns
        risk_free_rate: Risk-free rate (default 0)

    Returns:
        Annualized Sharpe ratio
    """
    pass
```

### 4. Error Handling
```python
def load_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        raise ValueError(f"Failed to load data: {e}")
```

### 5. Unit Tests
```python
# tests/test_shared/test_data_loaders.py
def test_load_data_range():
    df = load_data_range('test_data.parquet', '2024-01-01', '2024-01-31')
    assert len(df) > 0
    assert df['timestamp'].min() >= pd.Timestamp('2024-01-01')
```

## Using Shared Utilities

### In Notebooks
```python
# notebooks/my_analysis.ipynb
import sys
sys.path.append('..')  # Go up one level

from shared.data.loaders import load_binance_data
from shared.plotting.charts import plot_equity_curve
from shared.analysis.performance import calculate_sharpe_ratio

# Use utilities
data = load_binance_data('BTCUSDT', '2024-01-01', '2024-11-19')
```

### In Strategies
```python
# strategies/traditional/my_strategy.py
from shared.utils.helpers import calculate_position_size

class MyStrategy(Strategy):
    def on_bar(self, bar):
        size = calculate_position_size(
            self.portfolio.balance(),
            risk_pct=0.01,
            stop_distance=100
        )
```

### In Scripts
```python
# scripts/backtests/run_backtest.py
from shared.backtesting.runner import BacktestRunner
from shared.analysis.performance import analyze_results

runner = BacktestRunner('data/catalog')
results = runner.run(MyStrategy, config)
stats = analyze_results(results)
```

## Common Shared Utilities to Create

### Data Loading
- Load from exchange APIs
- Load from CSV/Parquet
- Load from NautilusTrader catalog
- Resample to different timeframes
- Clean and validate data

### Backtesting
- Backtest runner wrapper
- Parameter optimization
- Walk-forward analysis
- Results wrapper

### Analysis
- Performance metrics (Sharpe, Sortino, Calmar)
- Drawdown analysis
- Trade analysis
- Risk metrics

### Plotting
- Price charts with signals
- Equity curves
- Drawdown plots
- Returns distributions
- Correlation matrices

### Utilities
- Logging setup
- Position sizing
- Risk calculations
- Date/time helpers

## Maintaining Shared Code

### Regular Review
- Remove unused functions
- Refactor when used in 5+ places
- Keep documentation updated

### Versioning
- Avoid breaking changes
- If breaking change needed, create new function

### Testing
- Add tests for all shared utilities
- Run tests before committing changes

## Resources

- Main README: [../README.md](../README.md)
- Testing Guide: [../tests/README.md](../tests/README.md)
