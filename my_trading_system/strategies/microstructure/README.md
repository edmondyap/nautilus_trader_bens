# Microstructure Strategies

Strategies based on market microstructure analysis - the study of how orders become trades.

## Overview

Microstructure strategies analyze:
- Order flow patterns
- Trade imbalances
- Information content of trades
- Market impact
- Adverse selection

These strategies typically operate on high-frequency data (orderbook and trade ticks).

## Common Strategy Types

### Order Flow Imbalance
Trade based on net buying/selling pressure:
```python
# Net order flow over time window
buy_volume = sum(aggressive_buys)
sell_volume = sum(aggressive_sells)
ofi = buy_volume - sell_volume

if ofi > threshold:
    # Net buying pressure → Go long
```

### VPIN (Volume-Synchronized Probability of Informed Trading)
Measure toxicity of order flow:
- High VPIN → informed traders active → wider spreads
- Low VPIN → uninformed flow → tighter spreads

### Spread Capture
Capture bid-ask spread through intelligent execution:
- Monitor spread dynamics
- Post passive orders when spread is wide
- Cancel when spread tightens

### Trade Size Analysis
Different trade sizes have different information content:
- Large trades may signal informed trading
- Small trades more likely noise

## Key Data

Microstructure strategies use:
- **Trade ticks**: Every executed trade with aggressor side
- **L2 orderbook**: To measure depth and imbalance
- **Quote ticks**: Best bid/ask updates

## Example: Simple Order Flow Imbalance

```python
from collections import deque
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import TradeTick

class OrderFlowImbalanceConfig(StrategyConfig, frozen=True):
    instrument_id: str
    lookback_trades: int = 100
    imbalance_threshold: float = 0.3

class OrderFlowImbalanceStrategy(Strategy):
    def __init__(self, config: OrderFlowImbalanceConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)

        # Track recent trades
        self.recent_trades = deque(maxlen=config.lookback_trades)
        self.threshold = config.imbalance_threshold

    def on_start(self):
        # Subscribe to trade ticks
        self.subscribe_trade_ticks(self.instrument_id)

    def on_trade_tick(self, tick: TradeTick):
        # Store trade
        self.recent_trades.append({
            'size': float(tick.size),
            'aggressor': tick.aggressor_side  # BUY or SELL
        })

        if len(self.recent_trades) < self.recent_trades.maxlen:
            return

        # Calculate order flow imbalance
        buy_volume = sum(
            t['size'] for t in self.recent_trades
            if t['aggressor'] == AggressorSide.BUYER
        )
        sell_volume = sum(
            t['size'] for t in self.recent_trades
            if t['aggressor'] == AggressorSide.SELLER
        )

        total_volume = buy_volume + sell_volume
        if total_volume == 0:
            return

        imbalance = (buy_volume - sell_volume) / total_volume

        # Trading logic
        if imbalance > self.threshold:
            # Strong buying → Go long
            if not self.portfolio.is_long(self.instrument_id):
                self.buy()
        elif imbalance < -self.threshold:
            # Strong selling → Go short
            if not self.portfolio.is_short(self.instrument_id):
                self.sell()
```

## Common Microstructure Features

### 1. Order Flow Imbalance (OFI)
```python
def calculate_ofi(trades, window):
    """Net buying - selling over window"""
    buy_vol = sum(t.size for t in trades if t.is_buy)
    sell_vol = sum(t.size for t in trades if t.is_sell)
    return buy_vol - sell_vol
```

### 2. Trade Intensity
```python
def calculate_trade_intensity(trades, window_seconds):
    """Number of trades per second"""
    return len(trades) / window_seconds
```

### 3. Effective Spread
```python
def calculate_effective_spread(trade_price, mid_price):
    """How far trade is from mid (measure of liquidity cost)"""
    return 2 * abs(trade_price - mid_price)
```

### 4. Price Impact
```python
def calculate_price_impact(price_before, price_after, trade_size):
    """Price change per unit traded"""
    price_change = price_after - price_before
    return price_change / trade_size
```

### 5. Kyle's Lambda
```python
def calculate_kyle_lambda(price_changes, signed_order_flow):
    """Permanent price impact coefficient"""
    # Linear regression: ΔP = λ * Q
    return np.cov(price_changes, signed_order_flow)[0,1] / np.var(signed_order_flow)
```

## Data Handlers

```python
from nautilus_trader.model.data import TradeTick, QuoteTick

class MicrostructureStrategy(Strategy):
    def on_trade_tick(self, tick: TradeTick):
        """Handle executed trades"""
        price = tick.price
        size = tick.size
        aggressor_side = tick.aggressor_side  # BUYER or SELLER
        # Analyze trade...

    def on_quote_tick(self, tick: QuoteTick):
        """Handle best bid/ask updates"""
        bid = tick.bid_price
        ask = tick.ask_price
        mid = (bid + ask) / 2
        spread = ask - bid
        # Analyze spread dynamics...
```

## Best Practices

### 1. Handle High-Frequency Data
```python
# Microstructure strategies process many messages/second
# Be efficient - avoid expensive calculations in hot path

def on_trade_tick(self, tick):
    # Fast: Simple calculation
    self.trade_count += 1

    # Slow: Avoid in on_tick
    # self.recalculate_everything()
```

### 2. Use Buffering
```python
# Buffer data and process in batches
self.trade_buffer.append(tick)

if len(self.trade_buffer) >= 100:
    self.process_batch(self.trade_buffer)
    self.trade_buffer.clear()
```

### 3. Monitor Data Quality
```python
# Check for stale data, gaps, etc.
time_since_last_trade = now - self.last_trade_time
if time_since_last_trade > max_staleness:
    self.log.warning("Stale data - no trades received")
```

### 4. Combine with Orderbook
```python
# Microstructure features are stronger with L2 context
def on_trade_tick(self, tick):
    order_book = self.cache.order_book(tick.instrument_id)

    # Combine trade and orderbook info
    imbalance = calculate_orderbook_imbalance(order_book)
    trade_side = tick.aggressor_side

    # Trade in direction of imbalance = stronger signal
    if imbalance > 0 and trade_side == AggressorSide.BUYER:
        # Strong buy signal
        pass
```

## ML Integration

Extract microstructure features for ML models:

```python
# ml/features/microstructure.py
class MicrostructureFeatures:
    @staticmethod
    def create_features(trades_df, orderbook_df):
        features = {}

        # Order flow imbalance
        features['ofi_100'] = calculate_ofi(trades_df, window=100)
        features['ofi_500'] = calculate_ofi(trades_df, window=500)

        # Trade intensity
        features['trade_intensity'] = len(trades_df) / time_window

        # Effective spread
        features['eff_spread'] = calculate_effective_spread(trades_df)

        # Price impact
        features['price_impact'] = calculate_price_impact(trades_df)

        return features
```

## Resources

- [Market Microstructure Theory](https://en.wikipedia.org/wiki/Market_microstructure)
- [VPIN and Order Flow Toxicity](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695596)
- [NautilusTrader Trade Tick Documentation](https://nautilustrader.io/docs/latest/api_reference/model/data)
- Main README: [../../README.md](../../README.md)
