# Orderbook Strategies

Strategies that trade based on L2 (Level 2) orderbook data.

## Overview

These strategies use the full limit order book with multiple price levels to make trading decisions. NautilusTrader provides native orderbook handling - no custom processing needed.

## Common Strategy Types

### Market Making
Provide liquidity on both sides of the orderbook:
- Post limit orders at bid and ask
- Profit from the spread
- Adjust quotes based on inventory and risk

### Orderbook Imbalance
Trade based on bid/ask volume imbalance:
- Calculate volume imbalance at different depths
- Predict short-term price movements
- Enter positions when imbalance is strong

### Liquidity Provision
Passive strategies that provide liquidity:
- Post orders at specific depth levels
- Earn rebates from exchanges
- Minimize adverse selection

## Key Orderbook Handlers

NautilusTrader strategies can use:

```python
def on_order_book_deltas(self, deltas: OrderBookDeltas):
    """Handle incremental orderbook updates (most efficient)"""
    pass

def on_order_book(self, order_book: OrderBook):
    """Handle full orderbook snapshots"""
    pass
```

## Accessing Orderbook State

```python
from nautilus_trader.trading.strategy import Strategy

class MyOrderbookStrategy(Strategy):
    def on_order_book_deltas(self, deltas: OrderBookDeltas):
        # Get current orderbook state
        order_book = self.cache.order_book(deltas.instrument_id)

        # Best bid/ask
        best_bid = order_book.best_bid_price()
        best_ask = order_book.best_ask_price()
        best_bid_size = order_book.best_bid_size()
        best_ask_size = order_book.best_ask_size()

        # Spread
        spread = order_book.spread()

        # Mid price
        mid_price = order_book.midpoint()

        # Access bids/asks at depth
        bids = order_book.bids  # OrderedDict of price -> size
        asks = order_book.asks

        # Get specific level
        second_best_bid = list(bids.keys())[1] if len(bids) > 1 else None

        # Total volume at depth
        bid_volume_top5 = sum(list(bids.values())[:5])
        ask_volume_top5 = sum(list(asks.values())[:5])
```

## Example: Simple Market Maker

```python
from decimal import Decimal
from nautilus_trader.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.enums import OrderSide

class SimpleMarketMakerConfig(StrategyConfig, frozen=True):
    instrument_id: str
    quote_size: Decimal
    spread_bps: int = 10  # Spread in basis points

class SimpleMarketMaker(Strategy):
    def __init__(self, config: SimpleMarketMakerConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.quote_size = config.quote_size
        self.spread_bps = config.spread_bps

    def on_start(self):
        # Subscribe to orderbook
        self.subscribe_order_book_deltas(self.instrument_id)

    def on_order_book_deltas(self, deltas: OrderBookDeltas):
        order_book = self.cache.order_book(deltas.instrument_id)

        # Calculate quote prices
        mid = order_book.midpoint()
        spread_offset = mid * (self.spread_bps / 10000)

        bid_price = mid - spread_offset
        ask_price = mid + spread_offset

        # Cancel existing orders
        self.cancel_all_orders(self.instrument_id)

        # Place new quotes
        self.place_limit_order(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.quote_size,
            price=bid_price
        )

        self.place_limit_order(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.quote_size,
            price=ask_price
        )
```

## Best Practices

### 1. Use Deltas, Not Snapshots
```python
# Efficient: Handle incremental updates
def on_order_book_deltas(self, deltas: OrderBookDeltas):
    pass

# Less efficient: Full snapshot every time
def on_order_book(self, order_book: OrderBook):
    pass
```

### 2. Manage Quote Updates
```python
# Don't spam the exchange
# Only update quotes when meaningful change occurs
if abs(new_mid - old_mid) / old_mid > 0.001:  # 0.1% change
    self.update_quotes()
```

### 3. Monitor Inventory
```python
# Track your position
position = self.portfolio.position(self.instrument_id)
if position and abs(position.quantity) > self.max_inventory:
    # Adjust quotes to reduce inventory
    pass
```

### 4. Handle Adverse Selection
```python
# Widen spread when volatility increases
volatility = calculate_recent_volatility()
adjusted_spread = base_spread * (1 + volatility)
```

## Data Requirements

Orderbook strategies need:
- L2 orderbook subscription (live or historical)
- Low latency (important for market making)
- High message throughput handling

See [../../data/README.md](../../data/README.md) for L2 data collection and storage.

## Resources

- [NautilusTrader Orderbook Documentation](https://nautilustrader.io/docs/latest/api_reference/model/orderbook)
- [Market Making Overview](https://www.investopedia.com/terms/m/marketmaker.asp)
- Main README: [../../README.md](../../README.md)
