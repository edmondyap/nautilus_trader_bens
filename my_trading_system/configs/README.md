# Configs

This directory contains configuration files for strategies, ML models, data sources, and venues.

## Structure

```
configs/
├── strategies/              # Strategy configurations
│   ├── ema_cross_btc.yaml
│   ├── bollinger_eth.yaml
│   └── ml_direction_btc.yaml
├── ml/                      # ML configurations
│   ├── training/           # Training hyperparameters
│   │   ├── direction_model.yaml
│   │   └── volatility_model.yaml
│   └── inference/          # Inference configs
│       └── direction_model.yaml
├── alternative_data/        # Alternative data configs
│   ├── scrapers/           # Scraper configs
│   │   ├── news_sources.yaml
│   │   └── api_keys.yaml  # GITIGNORED!
│   └── processors/
│       └── sentiment_config.yaml
└── venues/                  # Exchange/venue configs
    ├── binance.yaml
    └── bybit.yaml
```

## Purpose

Configuration files separate settings from code, making it easy to:
- Run same strategy with different parameters
- Switch between instruments/exchanges
- Manage different environments (backtest/live)
- Version control settings without changing code

## Format

Use YAML for readability:

```yaml
# configs/strategies/ema_cross_btc.yaml
strategy:
  class_name: EMACrossStrategy
  instrument_id: BTCUSDT-PERP.BINANCE
  bar_type: BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-INTERNAL

parameters:
  fast_period: 10
  slow_period: 20
  trade_size: 0.1
  stop_loss_pct: 0.02
  take_profit_pct: 0.04
```

## Configuration Types

### Strategy Configs (`strategies/`)

Settings for trading strategies.

**Pattern:**
```yaml
# configs/strategies/my_strategy_btc.yaml
strategy:
  class_name: MyStrategy
  instrument_id: BTCUSDT-PERP.BINANCE
  bar_type: BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-INTERNAL

parameters:
  # Strategy-specific parameters
  period: 20
  threshold: 0.5
  trade_size: 1.0

risk:
  max_position_size: 10.0
  stop_loss_pct: 0.02
  max_daily_loss: 1000.0

environment:
  mode: backtest  # or sandbox, live
  log_level: INFO
```

**Loading in code:**
```python
import yaml

with open('configs/strategies/my_strategy_btc.yaml') as f:
    config = yaml.safe_load(f)

strategy_config = MyStrategyConfig(
    instrument_id=config['strategy']['instrument_id'],
    bar_type=config['strategy']['bar_type'],
    **config['parameters']
)
```

### ML Configs (`ml/`)

Machine learning configurations.

#### Training Config
```yaml
# configs/ml/training/direction_model.yaml
model:
  type: RandomForestClassifier
  params:
    n_estimators: 200
    max_depth: 15
    min_samples_split: 100
    random_state: 42

features:
  groups:
    - technical
    - microstructure
  lookback_periods:
    - 20
    - 50
    - 100

training:
  train_start: 2023-01-01
  train_end: 2024-10-31
  test_start: 2024-11-01
  test_end: 2024-11-19
  validation_split: 0.2

output:
  model_path: models/direction_predictor/v1_20241119
  save_metrics: true
```

#### Inference Config
```yaml
# configs/ml/inference/direction_model.yaml
model:
  path: models/direction_predictor/production
  version: v2_20241115

inference:
  batch_size: 100
  confidence_threshold: 0.6

features:
  buffer_size: 200  # Bars needed for feature calculation
```

### Alternative Data Configs (`alternative_data/`)

Configurations for data collection and processing.

#### Scraper Config
```yaml
# configs/alternative_data/scrapers/news_sources.yaml
sources:
  - name: newsapi
    enabled: true
    rate_limit: 1.0  # requests per second
    query: "bitcoin OR ethereum"
    language: en

  - name: coindesk
    enabled: true
    rate_limit: 0.5
    urls:
      - https://www.coindesk.com/tag/bitcoin
      - https://www.coindesk.com/tag/ethereum

symbols:
  - BTC
  - ETH
  - SOL

schedule:
  interval_minutes: 15
```

#### API Keys (NEVER COMMIT!)
```yaml
# configs/alternative_data/scrapers/api_keys.yaml
# ⚠️ ADD TO .gitignore!
newsapi_key: "your_api_key_here"
twitter_bearer_token: "your_token_here"
reddit_client_id: "your_client_id"
reddit_client_secret: "your_secret"
```

#### Processor Config
```yaml
# configs/alternative_data/processors/sentiment_config.yaml
sentiment_model:
  name: ProsusAI/finbert
  device: cpu  # or cuda

processing:
  batch_size: 32
  min_confidence: 0.5

aggregation:
  window_hours: 1
  min_articles: 5
```

### Venue Configs (`venues/`)

Exchange/broker connection settings.

```yaml
# configs/venues/binance.yaml
venue:
  name: BINANCE
  type: futures

connection:
  testnet: false
  api_key_env: BINANCE_API_KEY      # Read from environment
  api_secret_env: BINANCE_API_SECRET

rate_limits:
  requests_per_second: 10

instruments:
  - BTCUSDT-PERP
  - ETHUSDT-PERP
  - SOLUSDT-PERP

defaults:
  leverage: 1
  margin_mode: CROSS
```

## Environment-Specific Configs

Use different configs for different environments:

```
configs/strategies/
├── ema_cross_backtest.yaml     # Backtest settings
├── ema_cross_paper.yaml        # Paper trading settings
└── ema_cross_live.yaml         # Live trading settings
```

**Differences:**
```yaml
# Backtest
environment:
  mode: backtest
  starting_balance: 100000
  data_path: data/catalog

# Paper trading
environment:
  mode: sandbox
  starting_balance: 10000
  venue_testnet: true

# Live trading
environment:
  mode: live
  venue_testnet: false
  risk_limits:
    max_position_value: 5000
```

## Loading Configurations

### Simple Loading
```python
import yaml

with open('configs/strategies/my_strategy.yaml') as f:
    config = yaml.safe_load(f)

# Access values
instrument = config['strategy']['instrument_id']
params = config['parameters']
```

### With Environment Variables
```python
import os
import yaml

with open('configs/venues/binance.yaml') as f:
    config = yaml.safe_load(f)

# Load sensitive data from environment
api_key = os.getenv(config['connection']['api_key_env'])
api_secret = os.getenv(config['connection']['api_secret_env'])
```

### Using Pydantic for Validation
```python
from pydantic import BaseModel

class StrategyConfigFile(BaseModel):
    strategy: dict
    parameters: dict
    risk: dict

with open('configs/strategies/my_strategy.yaml') as f:
    raw_config = yaml.safe_load(f)

config = StrategyConfigFile(**raw_config)  # Validates structure
```

## Best Practices

### 1. No Secrets in Git
```yaml
# ❌ BAD: Hard-coded API key
api_key: "abc123xyz"

# ✅ GOOD: Reference environment variable
api_key_env: BINANCE_API_KEY

# ✅ GOOD: Separate file (gitignored)
# configs/alternative_data/scrapers/api_keys.yaml
```

### 2. Descriptive Names
```yaml
# ❌ BAD
configs/strategies/config1.yaml

# ✅ GOOD
configs/strategies/ema_cross_btc_5m.yaml
```

### 3. Document Parameters
```yaml
# configs/strategies/my_strategy.yaml
parameters:
  fast_period: 10          # Fast EMA period
  slow_period: 20          # Slow EMA period
  threshold: 0.5           # Signal threshold (0-1)
  trade_size: 1.0          # Position size in BTC
```

### 4. Version Control
```yaml
# Track config changes in git
# Include metadata
metadata:
  version: 1.0
  created: 2024-11-19
  author: Benjamin
  description: "EMA cross strategy for BTC 5-minute bars"
```

### 5. Default Values
```yaml
# Provide sensible defaults
parameters:
  fast_period: 10          # Required
  slow_period: 20          # Required
  stop_loss_pct: 0.02      # Optional, default 2%
  take_profit_pct: null    # Optional, no default
```

## Multi-Instrument Configs

### Option 1: One File Per Instrument
```
configs/strategies/
├── ema_cross_btc.yaml
├── ema_cross_eth.yaml
└── ema_cross_sol.yaml
```

### Option 2: Single File, Multiple Instruments
```yaml
# configs/strategies/ema_cross_all.yaml
base_parameters:
  fast_period: 10
  slow_period: 20

instruments:
  - symbol: BTCUSDT-PERP.BINANCE
    bar_type: 5-MINUTE-LAST
    trade_size: 0.1

  - symbol: ETHUSDT-PERP.BINANCE
    bar_type: 5-MINUTE-LAST
    trade_size: 1.0

  - symbol: SOLUSDT-PERP.BINANCE
    bar_type: 5-MINUTE-LAST
    trade_size: 10.0
```

## Parameter Optimization Configs

Store optimization results:

```yaml
# configs/strategies/ema_cross_optimized.yaml
optimization:
  date: 2024-11-19
  data_range:
    start: 2024-01-01
    end: 2024-10-31
  metric: sharpe_ratio

  search_space:
    fast_period: [5, 10, 15]
    slow_period: [20, 30, 40, 50]

  best_params:
    fast_period: 10
    slow_period: 30
    sharpe_ratio: 1.85
    win_rate: 0.58

# Use best params
parameters:
  fast_period: 10
  slow_period: 30
```

## Dynamic Configs

Generate configs programmatically:

```python
# scripts/generate_configs.py
import yaml

instruments = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
timeframes = ['1-MINUTE', '5-MINUTE', '15-MINUTE']

for instrument in instruments:
    for timeframe in timeframes:
        config = {
            'strategy': {
                'class_name': 'EMACrossStrategy',
                'instrument_id': f'{instrument}-PERP.BINANCE',
                'bar_type': f'{instrument}-PERP.BINANCE-{timeframe}-LAST-INTERNAL'
            },
            'parameters': {
                'fast_period': 10,
                'slow_period': 20
            }
        }

        filename = f'configs/strategies/ema_cross_{instrument.lower()}_{timeframe.lower()}.yaml'
        with open(filename, 'w') as f:
            yaml.dump(config, f)
```

## Migrating Configs

When updating config structure:

```python
# scripts/migrate_configs.py
import yaml
from pathlib import Path

def migrate_v1_to_v2(old_config):
    """Migrate old config format to new format"""
    new_config = {
        'version': 2,
        'strategy': old_config['strategy'],
        'parameters': old_config['params'],  # Renamed
        'risk': {  # New section
            'stop_loss_pct': old_config.get('stop_loss', 0.02)
        }
    }
    return new_config

# Migrate all configs
for config_file in Path('configs/strategies').glob('*.yaml'):
    with open(config_file) as f:
        old_config = yaml.safe_load(f)

    new_config = migrate_v1_to_v2(old_config)

    with open(config_file, 'w') as f:
        yaml.dump(new_config, f)
```

## Resources

- [YAML Specification](https://yaml.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- Main README: [../README.md](../README.md)
