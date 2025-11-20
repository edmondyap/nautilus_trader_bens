# My Trading System

A modular, scalable algorithmic trading system built on [NautilusTrader](https://nautilustrader.io/).

## Overview

This project provides a structured framework for developing, backtesting, and deploying trading strategies. It supports multiple data sources including **L2 orderbook data**, price data, alternative data, and ML features. Built for research workflows using Jupyter notebooks and production deployment.

**Key Features:**
- **L2 Orderbook Support**: Native integration with NautilusTrader's orderbook handling for market making and high-frequency strategies
- **Modular Architecture**: Easy to add new data sources, strategies, and ML models
- **Notebook-First Development**: Rapid prototyping with production deployment path
- **Scalable Structure**: Grows naturally as your system expands

## Directory Structure

```
my_trading_system/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── notebooks/                         # Research & experimentation (Jupyter notebooks)
│   ├── data_exploration/             # Data analysis and exploration
│   ├── orderbook_analysis/           # L2 orderbook research
│   ├── microstructure/               # Market microstructure analysis
│   ├── strategies/                   # Strategy development notebooks
│   ├── ml_research/                  # ML model experimentation
│   ├── ml_training/                  # Production ML training pipelines
│   ├── backtests/                    # Backtest analysis notebooks
│   ├── live/                         # Live trading monitoring
│   ├── alternative_data/             # Alternative data research
│   └── templates/                    # Notebook templates to copy
│
├── strategies/                        # Production trading strategies
│   ├── orderbook/                    # L2 orderbook strategies (market making, etc.)
│   ├── microstructure/               # Microstructure strategies (flow toxicity, etc.)
│   ├── traditional/                  # Price-based strategies (EMA cross, etc.)
│   ├── ml/                           # Machine learning strategies
│   ├── alternative_data/             # News/sentiment-based strategies
│   ├── arbitrage/                    # Arbitrage strategies
│   └── execution/                    # Execution algorithms (TWAP, VWAP, etc.)
│
├── ml/                                # Machine learning components
│   ├── features/                     # Feature engineering modules
│   ├── models/                       # Model definitions
│   ├── training/                     # Training utilities
│   ├── inference/                    # Model serving/inference
│   └── utils/                        # ML utilities
│
├── alternative_data/                  # Alternative data infrastructure
│   ├── scrapers/                     # Data collection (news, social media, etc.)
│   ├── processors/                   # Data processing (sentiment, NLP, etc.)
│   ├── providers/                    # Real-time data providers
│   ├── storage/                      # Database/storage layer
│   └── utils/                        # Utilities
│
├── shared/                            # Shared utilities (used across notebooks & strategies)
│   ├── data/                         # Data loading utilities
│   ├── backtesting/                  # Backtesting helpers
│   ├── analysis/                     # Performance analysis
│   ├── plotting/                     # Visualization utilities
│   └── utils/                        # General utilities
│
├── data/                              # Data storage
│   ├── raw/                          # Raw data files (gitignored)
│   │   ├── orderbook/                # L2 orderbook data
│   │   ├── trades/                   # Trade tick data
│   │   └── bars/                     # Bar/candle data
│   ├── processed/                    # Processed data (gitignored)
│   │   ├── orderbook_features/       # Features from L2 data
│   │   └── bars/                     # Processed bar data
│   ├── features/                     # Engineered features (gitignored)
│   ├── alternative/                  # Alternative data (news, social, etc.)
│   │   └── news/
│   │       ├── raw/
│   │       └── processed/
│   └── catalog/                      # NautilusTrader data catalog (supports L2)
│
├── configs/                           # Configuration files
│   ├── strategies/                   # Strategy configurations (YAML/JSON)
│   ├── ml/                           # ML configurations
│   │   ├── training/                 # Training hyperparameters
│   │   └── inference/                # Inference configs
│   ├── alternative_data/             # Alternative data configs
│   │   ├── scrapers/                 # Scraper configs, API keys
│   │   └── processors/               # Processing configs
│   └── venues/                       # Exchange/venue configurations
│
├── scripts/                           # Automation scripts
│   ├── data/                         # Data download/processing scripts
│   ├── ml/                           # ML training/evaluation automation
│   ├── alternative_data/             # Alternative data collection scripts
│   └── backtests/                    # Automated backtesting
│
├── models/                            # Saved ML models (gitignored)
│   └── {model_name}/
│       └── v{version}_YYYYMMDD/
│
├── logs/                              # Log files (gitignored)
│   ├── backtest/
│   └── live/
│
├── tests/                             # Unit tests
│   ├── test_strategies/
│   ├── test_ml/
│   └── test_data/
│
└── experiments/                       # Experiment tracking (MLflow, W&B, etc.)
```

## Design Principles

### 1. Separation of Research and Production
- **Notebooks** (`notebooks/`): Fast iteration, experimentation, visualization
- **Python modules** (`strategies/`, `ml/`, etc.): Tested, reusable production code
- **Flow**: Research in notebooks → Extract to modules → Deploy to production

### 2. Modular Architecture
Each domain has a consistent structure:
```
{domain}/
├── collectors/    # or scrapers/     - Get data
├── processors/                       - Transform data
├── providers/                        - Serve data (real-time)
└── storage/                          - Persist data
```

### 3. Data Source Independence
Adding a new data source (blockchain data, economic indicators, etc.) follows the same pattern:
1. Create `{data_source}/` module
2. Add corresponding folders in `data/`, `configs/`, `scripts/`
3. Research in `notebooks/{data_source}/`
4. Use in strategies

### 4. Strategy Categorization
Strategies are organized by type, not by asset or timeframe:
- `orderbook/`: L2 orderbook-based (market making, imbalance)
- `microstructure/`: Market microstructure (order flow, toxicity)
- `traditional/`: Price/indicator-based
- `ml/`: Machine learning
- `alternative_data/`: News/sentiment
- `arbitrage/`: Cross-exchange, statistical
- `execution/`: Algorithms for order execution

### 5. Horizontal Scalability
New domains are added in parallel, not nested:
```
my_trading_system/
├── alternative_data/      # News, social media
├── blockchain_data/       # On-chain data (when added)
├── fundamental_data/      # Economic data (when added)
└── orderflow_data/        # Microstructure (when added)
```

## Working with L2 Orderbook Data

This system is designed with **L2 orderbook data as a primary data source**. NautilusTrader provides native orderbook handling.

### Orderbook Strategy Example

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import OrderBookDeltas

class MarketMakerStrategy(Strategy):
    def on_order_book_deltas(self, deltas: OrderBookDeltas):
        """Handle L2 orderbook updates"""
        order_book = self.cache.order_book(deltas.instrument_id)

        # Access orderbook state
        best_bid = order_book.best_bid_price()
        best_ask = order_book.best_ask_price()
        spread = best_ask - best_bid

        # Calculate imbalance
        bid_volume = sum(order_book.bids.volumes()[:10])
        ask_volume = sum(order_book.asks.volumes()[:10])
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

        # Your market making logic...
```

### Data Collection

```python
# NautilusTrader connects to exchanges and streams L2 data automatically
# See scripts/data/collect_orderbook_live.py for example

# Data is stored in data/catalog/ using NautilusTrader's ParquetDataCatalog
# Orderbook deltas are efficiently compressed and stored
```

### Orderbook Features for ML

Extract features from L2 data:
- Bid/ask imbalance at various depths
- Microprice (volume-weighted mid)
- Order flow toxicity
- Spread dynamics
- Depth imbalance

See [data/README.md](data/README.md) for detailed orderbook data patterns.

## Getting Started

### 1. Installation

```bash
# Install NautilusTrader
pip install nautilus-trader

# Install project dependencies
pip install -r requirements.txt
```

### 2. Basic Workflow

#### Research Phase (Notebooks)
```bash
# Start Jupyter
jupyter lab

# Open a notebook from templates/
# Experiment with strategies, data, models
```

#### Production Phase (Python modules)
```bash
# Extract working code from notebooks to modules
# Example: Copy strategy from notebook to strategies/traditional/my_strategy.py

# Run backtests
python scripts/backtests/run_backtest.py

# Deploy live (when ready)
python scripts/live/run_live.py
```

### 3. Directory-Specific READMEs

For detailed information about each component, see:
- [notebooks/README.md](notebooks/README.md) - Notebook organization and templates
- [strategies/README.md](strategies/README.md) - How to create and organize strategies
- [ml/README.md](ml/README.md) - Machine learning workflow
- [alternative_data/README.md](alternative_data/README.md) - Alternative data collection
- [shared/README.md](shared/README.md) - Reusable utilities
- [data/README.md](data/README.md) - Data organization
- [configs/README.md](configs/README.md) - Configuration management

## Scaling Guide

### Adding a New Data Source

Example: Adding blockchain data

```bash
# 1. Create module structure
mkdir -p blockchain_data/{collectors,processors,providers,storage}

# 2. Create corresponding data directory
mkdir -p data/blockchain/{raw,processed}

# 3. Create config directory
mkdir -p configs/blockchain_data

# 4. Create research notebooks
mkdir -p notebooks/blockchain_data

# 5. Create automation scripts
mkdir -p scripts/blockchain_data
```

### Adding a New Strategy Type

Example: Adding options strategies

```bash
# 1. Create strategy directory
mkdir -p strategies/options

# 2. Add research notebooks
# Create notebooks/strategies/options_research.ipynb

# 3. Add data storage (if needed)
mkdir -p data/options

# 4. Add configs
# Create configs/strategies/options_config.yaml
```

### Adding a New ML Model

```bash
# 1. Add model definition
# Create ml/models/new_model.py

# 2. Add features (if needed)
# Create ml/features/new_features.py

# 3. Research in notebook
# Create notebooks/ml_research/new_model_research.ipynb

# 4. Create model storage
mkdir -p models/new_model
```

## Best Practices

### For Notebooks
- Use descriptive names: `01_explore_btc_data.ipynb`, not `notebook1.ipynb`
- Keep notebooks focused on one topic
- Extract reusable code to `shared/` or domain modules
- Use templates from `notebooks/templates/` for consistency

### For Strategies
- Inherit from `nautilus_trader.trading.strategy.Strategy`
- Use configuration classes (inherit from `StrategyConfig`)
- Keep strategies environment-agnostic (same code for backtest/live)
- Add unit tests in `tests/test_strategies/`

### For Data
- Raw data goes in `data/raw/`
- Processed data goes in `data/processed/`
- Use `.gitignore` to exclude large data files from version control
- Use NautilusTrader's `ParquetDataCatalog` for efficient storage

### For Version Control
- Commit code (strategies, modules, scripts)
- Commit configs (YAML/JSON files)
- DON'T commit data files, logs, or saved models
- Use `nbstripout` to clean notebook outputs before committing

## Common Tasks

### Run a Backtest
```python
# In a notebook or script
from shared.backtesting import run_backtest
from strategies.traditional.ema_cross import EMACrossStrategy, EMACrossConfig

results = run_backtest(
    strategy_class=EMACrossStrategy,
    config=EMACrossConfig(...),
    data_path="data/catalog"
)
```

### Train an ML Model
```python
# In notebooks/ml_training/
from ml.models.direction_predictor import DirectionPredictor
from ml.features.technical import TechnicalFeatures

# Load data, create features, train model
model = DirectionPredictor()
model.fit(X_train, y_train)
model.save("models/direction_predictor/v1_20241119")
```

### Scrape News
```bash
# One-time scrape
python scripts/alternative_data/scrape_news_batch.py

# Continuous scraping (background)
python scripts/alternative_data/scrape_news_continuous.py &
```

## Resources

- [NautilusTrader Documentation](https://nautilustrader.io/)
- [NautilusTrader GitHub](https://github.com/nautechsystems/nautilus_trader)
- [NautilusTrader Examples](https://github.com/nautechsystems/nautilus_trader/tree/develop/examples)

## License

[Your License Here]
