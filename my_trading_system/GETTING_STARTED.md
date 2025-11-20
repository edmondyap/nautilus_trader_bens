# Getting Started

Quick start guide for setting up and using this trading system.

## Prerequisites

- Python 3.10 or higher
- Git
- 8GB+ RAM (for backtesting with large datasets)

## Installation

### 1. Clone or Set Up Repository

```bash
# If using git
cd my_trading_system
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install NautilusTrader and other dependencies
pip install -r requirements.txt

# Verify installation
python -c "import nautilus_trader; print(nautilus_trader.__version__)"
```

### 4. Configure API Keys (Optional)

If using alternative data or live trading:

```bash
# Copy API keys template
cp configs/alternative_data/scrapers/api_keys.yaml.example \
   configs/alternative_data/scrapers/api_keys.yaml

# Edit with your actual keys
nano configs/alternative_data/scrapers/api_keys.yaml
```

## Quick Start

### Option 1: Start with Jupyter Notebooks (Recommended)

```bash
# Start Jupyter Lab
jupyter lab

# Navigate to notebooks/ and open a template
# Try: notebooks/templates/strategy_template.ipynb
```

### Option 2: Python Scripts

Create a simple backtest:

```python
# scripts/quickstart.py
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.model.data import BarType

# Your strategy here...
```

## Your First Strategy

### 1. Research in Notebook

```bash
# Open Jupyter
jupyter lab

# Create new notebook from template
cp notebooks/templates/strategy_template.ipynb \
   notebooks/strategies/my_first_strategy.ipynb
```

### 2. Develop Strategy

In the notebook:
```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig

class MyFirstStrategyConfig(StrategyConfig, frozen=True):
    instrument_id: str
    bar_type: str
    trade_size: float

class MyFirstStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        # Your initialization

    def on_start(self):
        # Subscribe to data
        pass

    def on_bar(self, bar):
        # Your trading logic
        pass
```

### 3. Quick Backtest

```python
from nautilus_trader.backtest.engine import BacktestEngine

engine = BacktestEngine()
# Add data, instruments, strategy
# Run backtest
```

### 4. Extract to Production (When Ready)

```bash
# Move stable strategy to module
# Edit strategies/traditional/my_first_strategy.py
```

## Directory Overview

- **`notebooks/`** - Your main workspace for research
- **`strategies/`** - Production strategy code
- **`data/`** - All data files (price, news, features)
- **`configs/`** - Configuration files
- **`shared/`** - Reusable utilities
- **`ml/`** - Machine learning components
- **`alternative_data/`** - News/sentiment/social data

## Common Tasks

### Download Data

```python
# In a notebook or script
import pandas as pd

# Example: Download from Binance
# (You'll need to implement this or use an API)
```

### Run a Backtest

```python
# In a notebook
from shared.backtesting import run_backtest  # You'll create this
from strategies.traditional.ema_cross import EMACrossStrategy

results = run_backtest(EMACrossStrategy, config, data_path)
results.summary()
```

### Train ML Model

```python
# In notebooks/ml_training/
from ml.models.direction_predictor import DirectionPredictor

model = DirectionPredictor()
model.fit(X_train, y_train)
model.save('models/direction_predictor/v1')
```

### Scrape News

```bash
# Run scraper script
python scripts/alternative_data/scrape_news.py
```

## Learning Path

### Week 1: Fundamentals
1. Read [NautilusTrader documentation](https://nautilustrader.io/)
2. Explore example notebooks in `notebooks/templates/`
3. Run a simple backtest with example data

### Week 2: Your First Strategy
1. Develop simple strategy in notebook
2. Backtest on historical data
3. Analyze results

### Week 3: Advanced Features
1. Add ML predictions (optional)
2. Integrate alternative data (optional)
3. Optimize parameters

### Week 4: Production
1. Extract strategy to Python module
2. Add unit tests
3. Paper trading with live data

## Resources

### Documentation
- [Main README](README.md) - Full system overview
- [Notebooks README](notebooks/README.md) - Notebook organization
- [Strategies README](strategies/README.md) - Strategy development
- [ML README](ml/README.md) - Machine learning workflow
- [Data README](data/README.md) - Data management

### NautilusTrader Resources
- [Official Documentation](https://nautilustrader.io/)
- [GitHub Repository](https://github.com/nautechsystems/nautilus_trader)
- [Examples](https://github.com/nautechsystems/nautilus_trader/tree/develop/examples)

### External Learning
- [QuantStart](https://www.quantstart.com/) - Algorithmic trading tutorials
- [Investopedia](https://www.investopedia.com/) - Trading concepts

## Troubleshooting

### Import Errors

```python
# In notebooks, add project root to path
import sys
sys.path.append('..')

from shared.data.loaders import load_data
```

### Data Not Found

```bash
# Check data directory structure
ls -la data/

# Verify .gitkeep files exist (directories tracked)
find data -name .gitkeep
```

### Notebook Kernel Issues

```bash
# Install kernel
python -m ipykernel install --user --name=trading-env

# Select kernel in Jupyter: Kernel -> Change Kernel -> trading-env
```

## Getting Help

1. Check READMEs in each directory
2. Review NautilusTrader documentation
3. Look at example notebooks in `notebooks/templates/`
4. Check NautilusTrader GitHub issues/discussions

## Next Steps

1. ✅ Set up environment (you're here!)
2. Explore `notebooks/templates/`
3. Read `strategies/README.md`
4. Try a simple backtest
5. Build your first strategy

Happy trading! 🚀
