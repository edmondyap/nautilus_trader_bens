# Strategies

This directory contains production trading strategies built on NautilusTrader.

## Organization

Strategies are organized by type:

```
strategies/
├── traditional/       # Price/indicator-based strategies
│   ├── ema_cross.py
│   ├── breakout.py
│   └── rsi_strategy.py
├── ml/               # Machine learning strategies
│   ├── direction_predictor.py
│   └── volatility_strategy.py
├── alternative_data/ # News/sentiment-based strategies
│   └── news_sentiment.py
├── arbitrage/        # Arbitrage strategies
│   └── funding_rate_arb.py
└── execution/        # Execution algorithms
    ├── twap.py
    └── vwap.py
```

## Creating a Strategy

### 1. Strategy Structure

Every NautilusTrader strategy follows this pattern:

```python
from decimal import Decimal
from nautilus_trader.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.identifiers import InstrumentId

# 1. Configuration class
class MyStrategyConfig(StrategyConfig, frozen=True):
    """Configuration for MyStrategy"""
    instrument_id: str
    bar_type: str
    trade_size: Decimal
    # Your parameters...
    fast_period: int = 10
    slow_period: int = 20

# 2. Strategy class
class MyStrategy(Strategy):
    """Your strategy description"""

    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
        # Initialize state
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        # Initialize indicators, variables...

    def on_start(self):
        """Called when strategy starts"""
        # Subscribe to data
        self.subscribe_bars(BarType.from_str(self.config.bar_type))

    def on_bar(self, bar: Bar):
        """Called on each new bar"""
        # Your trading logic
        pass

    def on_stop(self):
        """Called when strategy stops"""
        # Cleanup: close positions, cancel orders
        self.close_all_positions(self.instrument_id)
        self.cancel_all_orders(self.instrument_id)
```

### 2. Development Workflow

```
1. Research in notebook
   └─> notebooks/strategies/my_strategy.ipynb

2. Extract to Python module
   └─> strategies/traditional/my_strategy.py

3. Create configuration
   └─> configs/strategies/my_strategy.yaml

4. Add tests
   └─> tests/test_strategies/test_my_strategy.py

5. Backtest
   └─> notebooks/backtests/backtest_my_strategy.ipynb

6. Deploy
   └─> Use in live trading
```

## Strategy Categories

### Traditional (`traditional/`)
Price and indicator-based strategies:
- Trend following (EMA cross, MACD, breakouts)
- Mean reversion (Bollinger Bands, RSI)
- Pattern recognition (candlestick patterns)

**Example**: EMA Cross
```python
class EMACrossStrategy(Strategy):
    def on_bar(self, bar: Bar):
        if fast_ema > slow_ema:
            # Go long
        elif fast_ema < slow_ema:
            # Go short
```

### ML (`ml/`)
Strategies using machine learning models:
- Price direction prediction
- Volatility forecasting
- Regime classification

**Example**: ML Direction
```python
class MLDirectionStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.model = DirectionPredictor.load(config.model_path)

    def on_bar(self, bar: Bar):
        prediction = self.model.predict(features)
        if prediction == 'up':
            # Go long
```

### Alternative Data (`alternative_data/`)
Strategies using news, sentiment, social media:
- News sentiment trading
- Event-driven trading
- Social media signals

**Example**: News Sentiment
```python
class NewsSentimentStrategy(Strategy):
    def on_data(self, data):
        if isinstance(data, NewsSentimentData):
            if data.sentiment_score > threshold:
                # Go long on positive news
```

### Arbitrage (`arbitrage/`)
Cross-exchange or statistical arbitrage:
- Funding rate arbitrage
- Triangular arbitrage
- Statistical arbitrage

**Example**: Funding Rate Arb
```python
class FundingRateArbStrategy(Strategy):
    def on_funding_rate_update(self, data):
        if funding_rate > threshold:
            # Go short on high funding
```

### Execution (`execution/`)
Algorithms for optimal order execution:
- TWAP (Time-Weighted Average Price)
- VWAP (Volume-Weighted Average Price)
- Implementation Shortfall

**Example**: TWAP
```python
class TWAPStrategy(Strategy):
    def on_start(self):
        # Split order into time slices
        pass
```

## Key Handler Methods

Strategies can implement these handlers:

### Data Handlers
```python
def on_start(self):
    """Strategy initialization - subscribe to data"""

def on_stop(self):
    """Strategy shutdown - cleanup"""

def on_bar(self, bar: Bar):
    """New bar received"""

def on_quote_tick(self, tick: QuoteTick):
    """New quote received (bid/ask)"""

def on_trade_tick(self, tick: TradeTick):
    """New trade received"""

def on_data(self, data: Data):
    """Custom data received"""
```

### Order Handlers
```python
def on_order_submitted(self, event: OrderSubmitted):
    """Order submitted to exchange"""

def on_order_filled(self, event: OrderFilled):
    """Order filled"""

def on_order_rejected(self, event: OrderRejected):
    """Order rejected"""

def on_order_canceled(self, event: OrderCanceled):
    """Order canceled"""
```

### Position Handlers
```python
def on_position_opened(self, event: PositionOpened):
    """New position opened"""

def on_position_changed(self, event: PositionChanged):
    """Position modified"""

def on_position_closed(self, event: PositionClosed):
    """Position closed"""
```

## Best Practices

### 1. Configuration Over Hard-Coding
```python
# Good: Use config
class MyStrategyConfig(StrategyConfig, frozen=True):
    fast_period: int = 10
    slow_period: int = 20

# Bad: Hard-coded
class MyStrategy(Strategy):
    def __init__(self):
        self.fast_period = 10  # Hard-coded
```

### 2. Environment Agnostic
Write strategies that work in backtest, sandbox, and live:
```python
# Same strategy code works everywhere
# Different configs for different environments
```

### 3. Proper State Management
```python
def __init__(self, config):
    super().__init__(config)
    # Initialize all state variables
    self.position = None
    self.last_signal = None
```

### 4. Risk Management
```python
def on_bar(self, bar: Bar):
    # Check risk before trading
    if self.portfolio.unrealized_pnl() < max_loss:
        self.close_all_positions()
        return

    # Your trading logic...
```

### 5. Logging
```python
def on_bar(self, bar: Bar):
    self.log.info(f"Processing bar: {bar}")

    if signal:
        self.log.info(f"Signal detected: {signal}")
```

## Testing Strategies

### Unit Tests
```python
# tests/test_strategies/test_ema_cross.py
def test_ema_cross_long_signal():
    config = EMACrossConfig(...)
    strategy = EMACrossStrategy(config)
    # Test logic...
```

### Backtests
```python
# notebooks/backtests/test_strategy.ipynb
from shared.backtesting import run_backtest

results = run_backtest(
    strategy_class=MyStrategy,
    config=MyStrategyConfig(...),
    data_path="data/catalog"
)
```

## Using Strategies

### In Backtests
```python
from nautilus_trader.backtest.engine import BacktestEngine
from strategies.traditional.ema_cross import EMACrossStrategy

engine = BacktestEngine()
# ... setup engine
engine.add_strategy(EMACrossStrategy(config))
engine.run()
```

### In Live Trading
```python
from nautilus_trader.live.node import TradingNode
from strategies.traditional.ema_cross import EMACrossStrategy

node = TradingNode()
# ... setup node
node.add_strategy(EMACrossStrategy(config))
node.run()
```

## Adding New Strategy Categories

If you need a new category:

```bash
# 1. Create directory
mkdir strategies/new_category

# 2. Add __init__.py
touch strategies/new_category/__init__.py

# 3. Add README (optional)
echo "# New Category Strategies" > strategies/new_category/README.md

# 4. Create base class (optional)
# strategies/new_category/base.py
```

## Resources

- [NautilusTrader Strategy Documentation](https://nautilustrader.io/docs/latest/concepts/strategies)
- [NautilusTrader Example Strategies](https://github.com/nautechsystems/nautilus_trader/tree/develop/nautilus_trader/examples/strategies)
- Main README: [../README.md](../README.md)
