# Notebooks

This directory contains Jupyter notebooks for research, experimentation, and analysis.

## Organization

```
notebooks/
├── data_exploration/      # Exploring and understanding data
├── strategies/            # Strategy development and testing
├── ml_research/          # ML model experimentation
├── ml_training/          # Production ML training pipelines
├── backtests/            # Backtest analysis and comparison
├── live/                 # Live trading monitoring
├── alternative_data/     # Alternative data research
└── templates/            # Notebook templates (copy these to start new work)
```

## Workflow

### 1. Start with a Template
```bash
# Copy template to start new work
cp templates/strategy_template.ipynb strategies/my_new_strategy.ipynb
```

### 2. Iterate Quickly
Notebooks are for:
- Fast experimentation
- Visual analysis
- Exploring ideas
- Prototyping strategies

### 3. Extract to Production
When code is stable:
- Move to Python modules (`strategies/`, `ml/`, `shared/`)
- Add unit tests
- Use in automated scripts

## Naming Conventions

Use descriptive names with prefixes:
```
01_explore_btc_data.ipynb          # Good: numbered, descriptive
02_test_ema_cross_idea.ipynb       # Good: clear purpose
strategy_ema_cross.ipynb            # Good: shows it's a strategy
notebook1.ipynb                     # Bad: not descriptive
test.ipynb                          # Bad: too vague
```

## Organization Tips

### By Date (for research)
```
notebooks/data_exploration/
├── 20241119_btc_volatility.ipynb
├── 20241120_eth_correlation.ipynb
└── 20241121_market_regime.ipynb
```

### By Topic (for strategies)
```
notebooks/strategies/
├── ema_cross_strategy.ipynb
├── bollinger_bands_strategy.ipynb
└── market_maker_strategy.ipynb
```

## Best Practices

### Keep Notebooks Focused
- One notebook = one topic/strategy/analysis
- If >500 lines, consider splitting or moving to modules

### Use Shared Code
```python
# Don't duplicate code across notebooks
import sys
sys.path.append('..')

from shared.data import load_binance_data
from shared.plotting import plot_equity_curve
```

### Document Your Thinking
```markdown
# Markdown cells to explain your reasoning
## Hypothesis
I think adding volume filter will improve win rate because...

## Results
The results show...
```

### Clean Outputs Before Committing
```bash
# Use nbstripout to clean outputs
pip install nbstripout
nbstripout notebook.ipynb

# Or install as git hook (recommended)
nbstripout --install
```

## Common Patterns

### Data Exploration Notebook
```python
# Cell 1: Imports
import pandas as pd
import plotly.graph_objects as go
from shared.data import load_binance_data

# Cell 2: Load data
df = load_binance_data("BTCUSDT", "2024-01-01", "2024-11-19")

# Cell 3: Basic stats
print(df.describe())

# Cell 4: Visualizations
df['close'].plot()

# Cell 5: Analysis
# Your analysis code...
```

### Strategy Development Notebook
```python
# Cell 1: Imports
from nautilus_trader.trading.strategy import Strategy
from shared.backtesting import run_backtest

# Cell 2: Strategy definition
class MyStrategy(Strategy):
    # Strategy code...
    pass

# Cell 3: Quick backtest
results = run_backtest(MyStrategy, config, data)

# Cell 4: Analysis
print(results.stats)
results.plot_equity()

# Cell 5: Parameter testing
# Try different parameters...
```

### ML Research Notebook
```python
# Cell 1: Imports
from sklearn.ensemble import RandomForestClassifier
from ml.features.technical import TechnicalFeatures

# Cell 2: Load and prepare data
# ...

# Cell 3: Feature engineering
features = TechnicalFeatures.create_features(df)

# Cell 4: Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Cell 5: Evaluate
# Metrics, plots...

# Cell 6: If good → move to ml/models/
```

## Template Notebooks

The `templates/` directory contains starter notebooks:
- `strategy_template.ipynb` - For developing new strategies
- `backtest_template.ipynb` - For backtesting
- `data_exploration_template.ipynb` - For exploring data
- `ml_research_template.ipynb` - For ML experimentation

Copy and modify these to get started quickly.

## Archiving

Move old/completed notebooks to an archive:
```bash
mkdir -p archive/2024-11
mv old_experiment.ipynb archive/2024-11/
```

## Converting Notebooks to Scripts

When ready for production:
```bash
# Convert notebook to Python script
jupyter nbconvert --to script my_strategy.ipynb

# Move to appropriate module
mv my_strategy.py ../strategies/traditional/
```
