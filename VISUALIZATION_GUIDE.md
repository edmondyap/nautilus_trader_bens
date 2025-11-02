# NautilusTrader Visualization Guide
## OrderBook Visualization, Live Trading Monitors & Dashboards

**Last Updated:** November 2, 2025
**Platform Version:** NautilusTrader v1.222.0

---

## Table of Contents

1. [What Exists Out-of-the-Box](#1-what-exists-out-of-the-box)
2. [OrderBook Visualization](#2-orderbook-visualization)
3. [Live Trading Monitoring](#3-live-trading-monitoring)
4. [Building Custom Dashboards](#4-building-custom-dashboards)
5. [Jupyter Notebook Integration](#5-jupyter-notebook-integration)
6. [Complete Examples](#6-complete-examples)

---

## 1. What Exists Out-of-the-Box

### ✅ Available Visualization Features

**Backtest Analysis (Plotly-based):**
- ✅ Interactive HTML tearsheets
- ✅ Equity curves
- ✅ Drawdown charts
- ✅ Monthly/yearly returns heatmaps
- ✅ Returns distribution
- ✅ Rolling Sharpe ratio
- ✅ Custom chart registration

**OrderBook Text Visualization:**
- ✅ Pretty-print orderbook to console (`book.pprint()`)
- ✅ Tabular display of bid/ask levels

**Data Reports:**
- ✅ Account reports (balances, PnL)
- ✅ Position reports
- ✅ Order fills report
- ✅ Performance statistics

### ❌ NOT Available Out-of-the-Box

**Missing Visualizations:**
- ❌ Real-time depth-of-market (DOM) GUI
- ❌ Price ladder like TT MD Trader
- ❌ Live trading dashboard
- ❌ Real-time orderbook heatmap
- ❌ WebSocket API for external dashboards
- ❌ Built-in web UI

**The Good News:** You can build these yourself using NautilusTrader's APIs!

---

## 2. OrderBook Visualization

### 2.1 Built-in: Console Pretty-Print

**Available Method:** `book.pprint(num_levels)`

**Example:**

```python
from nautilus_trader.model.book import OrderBook
from nautilus_trader.trading.strategy import Strategy

class MyStrategy(Strategy):
    def on_order_book_deltas(self, deltas):
        book = self.cache.order_book(self.config.instrument_id)

        # Pretty print to console
        print(book.pprint(num_levels=10))
```

**Output:**

```
╒═══════════╤═════════╤═══════════╕
│   Bids    │  Price  │   Asks    │
╞═══════════╪═════════╪═══════════╡
│ 15.234 BTC│         │           │
│  8.567 BTC│ 42100.50│           │
│ 12.123 BTC│ 42100.00│           │
│  5.000 BTC│ 42099.50│           │
│           │ 42099.00│  3.234 BTC│
│           │ 42098.50│  7.891 BTC│
│           │ 42098.00│ 11.456 BTC│
│           │         │ 20.000 BTC│
╘═══════════╧═════════╧═══════════╛
```

### 2.2 Custom: Depth-of-Market Chart (Plotly)

**Build Your Own DOM Visualization:**

```python
import plotly.graph_objects as go
from nautilus_trader.model.book import OrderBook

def create_dom_chart(book: OrderBook, num_levels: int = 20) -> go.Figure:
    """
    Create a depth-of-market chart like TT MD Trader.

    Shows cumulative volume at each price level.
    """
    bid_levels = book.bids()[:num_levels]
    ask_levels = book.asks()[:num_levels]

    # Extract data for bids
    bid_prices = [level.price.as_double() for level in bid_levels]
    bid_sizes = [level.size() for level in bid_levels]
    bid_cumulative = []
    cumsum = 0
    for size in bid_sizes:
        cumsum += size
        bid_cumulative.append(cumsum)

    # Extract data for asks
    ask_prices = [level.price.as_double() for level in ask_levels]
    ask_sizes = [level.size() for level in ask_levels]
    ask_cumulative = []
    cumsum = 0
    for size in ask_sizes:
        cumsum += size
        ask_cumulative.append(cumsum)

    # Create figure
    fig = go.Figure()

    # Add bid depth
    fig.add_trace(go.Scatter(
        x=bid_prices,
        y=bid_cumulative,
        fill='tozeroy',
        name='Bids',
        line=dict(color='green'),
        fillcolor='rgba(0, 255, 0, 0.3)',
    ))

    # Add ask depth
    fig.add_trace(go.Scatter(
        x=ask_prices,
        y=ask_cumulative,
        fill='tozeroy',
        name='Asks',
        line=dict(color='red'),
        fillcolor='rgba(255, 0, 0, 0.3)',
    ))

    # Add vertical line at mid price
    mid_price = book.midpoint()
    fig.add_vline(
        x=mid_price,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Mid: {mid_price:.2f}",
    )

    fig.update_layout(
        title=f"{book.instrument_id} Depth of Market",
        xaxis_title="Price",
        yaxis_title="Cumulative Volume",
        hovermode='x unified',
        template='plotly_dark',
    )

    return fig

# Usage in strategy
class DOMStrategy(Strategy):
    def on_order_book_deltas(self, deltas):
        book = self.cache.order_book(self.config.instrument_id)

        # Create and save DOM chart
        fig = create_dom_chart(book, num_levels=20)
        fig.write_html("dom_snapshot.html")

        # Or display in Jupyter
        # fig.show()
```

### 2.3 Custom: Price Ladder Visualization

**Create a TT-style Price Ladder:**

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_price_ladder(
    book: OrderBook,
    num_levels: int = 20,
    highlight_best: bool = True,
) -> go.Figure:
    """
    Create a price ladder display similar to TT MD Trader.

    Shows:
    - Bid sizes | Price | Ask sizes
    - Highlighted best bid/ask
    - Color-coded levels
    """
    bid_levels = book.bids()[:num_levels]
    ask_levels = book.asks()[:num_levels]

    # Combine and sort all prices
    all_prices = sorted(
        set([level.price.as_double() for level in bid_levels + ask_levels]),
        reverse=True,
    )

    # Build data for table
    bid_data = {level.price.as_double(): level.size() for level in bid_levels}
    ask_data = {level.price.as_double(): level.size() for level in ask_levels}

    bid_column = []
    price_column = []
    ask_column = []
    row_colors = []

    best_bid = book.best_bid_price().as_double() if book.best_bid_price() else None
    best_ask = book.best_ask_price().as_double() if book.best_ask_price() else None

    for price in all_prices:
        bid_size = bid_data.get(price, 0)
        ask_size = ask_data.get(price, 0)

        bid_column.append(f"{bid_size:.3f}" if bid_size > 0 else "")
        price_column.append(f"{price:.2f}")
        ask_column.append(f"{ask_size:.3f}" if ask_size > 0 else "")

        # Color coding
        if price == best_bid:
            row_colors.append('rgba(0, 255, 0, 0.3)')  # Green for best bid
        elif price == best_ask:
            row_colors.append('rgba(255, 0, 0, 0.3)')  # Red for best ask
        elif bid_size > 0:
            row_colors.append('rgba(0, 255, 0, 0.1)')
        elif ask_size > 0:
            row_colors.append('rgba(255, 0, 0, 0.1)')
        else:
            row_colors.append('white')

    # Create table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Bid Size</b>', '<b>Price</b>', '<b>Ask Size</b>'],
            fill_color='darkgray',
            align='center',
            font=dict(size=14, color='white'),
        ),
        cells=dict(
            values=[bid_column, price_column, ask_column],
            fill_color=[row_colors] * 3,
            align=['right', 'center', 'left'],
            font=dict(size=12),
            height=25,
        ),
    )])

    fig.update_layout(
        title=f"{book.instrument_id} Price Ladder",
        height=600,
        template='plotly_dark',
    )

    return fig

# Usage
fig = create_price_ladder(book, num_levels=20)
fig.write_html("price_ladder.html")
```

### 2.4 Custom: Orderbook Heatmap (Live Updates)

```python
import plotly.graph_objects as go
import numpy as np
from collections import deque

class OrderBookHeatmap:
    """
    Track orderbook changes over time and visualize as heatmap.

    Similar to volume profile or delta profile charts.
    """

    def __init__(self, instrument_id, num_levels=20, history_length=100):
        self.instrument_id = instrument_id
        self.num_levels = num_levels
        self.history_length = history_length

        # Store historical book snapshots
        self.bid_history = deque(maxlen=history_length)
        self.ask_history = deque(maxlen=history_length)
        self.timestamps = deque(maxlen=history_length)

    def update(self, book: OrderBook):
        """Add current book state to history."""
        bid_levels = book.bids()[:self.num_levels]
        ask_levels = book.asks()[:self.num_levels]

        # Store as dict: price -> size
        bid_snapshot = {level.price.as_double(): level.size() for level in bid_levels}
        ask_snapshot = {level.price.as_double(): level.size() for level in ask_levels}

        self.bid_history.append(bid_snapshot)
        self.ask_history.append(ask_snapshot)
        self.timestamps.append(book.ts_last)

    def create_heatmap(self) -> go.Figure:
        """Create heatmap visualization of orderbook evolution."""
        if len(self.bid_history) == 0:
            return go.Figure()

        # Get all unique prices
        all_prices = sorted(
            set().union(*[snapshot.keys() for snapshot in self.bid_history + self.ask_history]),
            reverse=True,
        )

        # Build 2D array: time x price
        bid_matrix = []
        for bid_snapshot in self.bid_history:
            row = [bid_snapshot.get(price, 0) for price in all_prices]
            bid_matrix.append(row)

        ask_matrix = []
        for ask_snapshot in self.ask_history:
            row = [ask_snapshot.get(price, 0) for price in all_prices]
            ask_matrix.append(row)

        # Transpose for plotting (prices as y-axis)
        bid_matrix = np.array(bid_matrix).T
        ask_matrix = np.array(ask_matrix).T

        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Bid Depth Over Time', 'Ask Depth Over Time'),
        )

        # Bid heatmap
        fig.add_trace(
            go.Heatmap(
                z=bid_matrix,
                y=[f"{p:.2f}" for p in all_prices],
                colorscale='Greens',
                name='Bids',
            ),
            row=1, col=1,
        )

        # Ask heatmap
        fig.add_trace(
            go.Heatmap(
                z=ask_matrix,
                y=[f"{p:.2f}" for p in all_prices],
                colorscale='Reds',
                name='Asks',
            ),
            row=1, col=2,
        )

        fig.update_layout(
            title=f"{self.instrument_id} OrderBook Heatmap",
            height=800,
            template='plotly_dark',
        )

        return fig

# Usage in strategy
class HeatmapStrategy(Strategy):
    def on_start(self):
        self.heatmap = OrderBookHeatmap(
            self.config.instrument_id,
            num_levels=20,
            history_length=100,
        )

    def on_order_book_deltas(self, deltas):
        book = self.cache.order_book(self.config.instrument_id)
        self.heatmap.update(book)

        # Periodically save heatmap
        if self.clock.timestamp_ns() % 10_000_000_000 == 0:  # Every 10 seconds
            fig = self.heatmap.create_heatmap()
            fig.write_html("orderbook_heatmap.html")
```

---

## 3. Live Trading Monitoring

### 3.1 Console Monitoring (Built-in)

**Log Live Trading Activity:**

```python
class MonitoredStrategy(Strategy):
    def on_order_submitted(self, event):
        self.log.info(f"📤 Order submitted: {event.client_order_id}")

    def on_order_filled(self, event):
        self.log.info(
            f"✅ Order filled: {event.client_order_id} "
            f"@ {event.last_px} x {event.last_qty}"
        )

    def on_position_opened(self, event):
        position = self.cache.position(event.position_id)
        self.log.info(
            f"🟢 Position opened: {position.quantity} {position.instrument_id} "
            f"@ {position.avg_px_open}"
        )

    def on_position_changed(self, event):
        position = self.cache.position(event.position_id)
        unrealized_pnl = position.unrealized_pnl(position.last).as_double()
        self.log.info(
            f"📊 Position PnL: {unrealized_pnl:.2f} {position.quote_currency}"
        )

    def on_position_closed(self, event):
        position = self.cache.position(event.position_id)
        realized_pnl = position.realized_pnl.as_double()
        self.log.info(
            f"🔴 Position closed: PnL = {realized_pnl:.2f} {position.quote_currency}"
        )
```

### 3.2 Custom: Real-Time Dashboard (Streamlit)

**Build a Streamlit Dashboard for Live Monitoring:**

```python
# live_dashboard.py
import streamlit as st
import pandas as pd
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.live.node import TradingNode
import plotly.graph_objects as go
import time

st.set_page_config(page_title="NautilusTrader Live Dashboard", layout="wide")

st.title("🚀 NautilusTrader Live Dashboard")

# Sidebar configuration
st.sidebar.header("Configuration")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 5)

# Connect to live node (you'd need to expose node state via file/Redis)
# For now, read from catalog or logs
catalog = ParquetDataCatalog("./live_data")

# Layout
col1, col2, col3 = st.columns(3)

# Metrics
with col1:
    st.metric("Open Positions", "3")
    st.metric("Total PnL", "$2,450.50", "+12.5%")

with col2:
    st.metric("Orders Today", "142")
    st.metric("Fill Rate", "98.5%")

with col3:
    st.metric("Win Rate", "56.3%")
    st.metric("Sharpe Ratio", "1.85")

# Live positions table
st.subheader("📊 Live Positions")
positions_data = {
    'Instrument': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    'Side': ['LONG', 'LONG', 'SHORT'],
    'Quantity': [0.5, 10.0, 50.0],
    'Entry Price': [42100.50, 2250.30, 105.25],
    'Current Price': [42350.00, 2280.00, 103.50],
    'Unrealized PnL': [125.00, 297.00, 87.50],
}
st.dataframe(pd.DataFrame(positions_data), use_container_width=True)

# Live equity curve
st.subheader("📈 Equity Curve (Live)")
# Read from catalog or cache
equity_data = pd.DataFrame({
    'timestamp': pd.date_range(start='2025-11-01', periods=100, freq='1min'),
    'equity': [100000 + i * 100 for i in range(100)],
})

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=equity_data['timestamp'],
    y=equity_data['equity'],
    mode='lines',
    name='Equity',
    line=dict(color='green'),
))
fig.update_layout(
    title='Account Equity',
    xaxis_title='Time',
    yaxis_title='Equity (USD)',
    template='plotly_dark',
    height=400,
)
st.plotly_chart(fig, use_container_width=True)

# Live orderbook
st.subheader("📕 Live OrderBook")
# Would connect to strategy's orderbook cache
col_bid, col_ask = st.columns(2)

with col_bid:
    st.markdown("**Bids**")
    bid_data = pd.DataFrame({
        'Price': [42100.0, 42099.5, 42099.0],
        'Size': [15.234, 8.567, 12.123],
    })
    st.dataframe(bid_data, use_container_width=True)

with col_ask:
    st.markdown("**Asks**")
    ask_data = pd.DataFrame({
        'Price': [42101.0, 42101.5, 42102.0],
        'Size': [3.234, 7.891, 11.456],
    })
    st.dataframe(ask_data, use_container_width=True)

# Recent fills
st.subheader("📋 Recent Fills")
fills_data = {
    'Time': ['10:25:33', '10:24:15', '10:22:01'],
    'Instrument': ['BTCUSDT', 'ETHUSDT', 'BTCUSDT'],
    'Side': ['BUY', 'SELL', 'BUY'],
    'Price': [42100.50, 2250.30, 42095.00],
    'Quantity': [0.5, 5.0, 0.3],
}
st.dataframe(pd.DataFrame(fills_data), use_container_width=True)

# Auto-refresh
time.sleep(refresh_rate)
st.rerun()
```

**Run:**
```bash
streamlit run live_dashboard.py
```

### 3.3 Custom: WebSocket API for External Dashboards

**Expose Live Data via WebSocket:**

```python
# websocket_server.py
import asyncio
import json
import websockets
from nautilus_trader.trading.strategy import Strategy

class WebSocketBroadcaster(Strategy):
    """
    Broadcast live trading events to connected WebSocket clients.

    Allows external dashboards (React, Vue, etc.) to monitor live trading.
    """

    def __init__(self, config):
        super().__init__(config)
        self.clients = set()
        self.server = None

    async def start_websocket_server(self):
        """Start WebSocket server on port 8765."""
        async def handler(websocket):
            self.clients.add(websocket)
            self.log.info(f"Client connected: {websocket.remote_address}")
            try:
                await websocket.wait_closed()
            finally:
                self.clients.remove(websocket)

        self.server = await websockets.serve(handler, "localhost", 8765)
        self.log.info("WebSocket server started on ws://localhost:8765")

    async def broadcast(self, event_type, data):
        """Broadcast event to all connected clients."""
        if not self.clients:
            return

        message = json.dumps({
            'type': event_type,
            'data': data,
            'timestamp': self.clock.timestamp_ms(),
        })

        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True,
        )

    def on_start(self):
        # Start WebSocket server in background
        asyncio.create_task(self.start_websocket_server())

    def on_order_book_deltas(self, deltas):
        book = self.cache.order_book(self.config.instrument_id)

        # Broadcast orderbook update
        asyncio.create_task(self.broadcast('orderbook', {
            'instrument_id': str(book.instrument_id),
            'best_bid': book.best_bid_price().as_double() if book.best_bid_price() else None,
            'best_ask': book.best_ask_price().as_double() if book.best_ask_price() else None,
            'spread': book.spread(),
        }))

    def on_order_filled(self, event):
        # Broadcast fill
        asyncio.create_task(self.broadcast('fill', {
            'order_id': str(event.client_order_id),
            'instrument_id': str(event.instrument_id),
            'side': str(event.order_side),
            'price': event.last_px.as_double(),
            'quantity': event.last_qty.as_double(),
        }))

    def on_position_changed(self, event):
        position = self.cache.position(event.position_id)

        # Broadcast position update
        asyncio.create_task(self.broadcast('position', {
            'instrument_id': str(position.instrument_id),
            'side': str(position.side),
            'quantity': position.quantity.as_double(),
            'unrealized_pnl': position.unrealized_pnl(position.last).as_double(),
        }))
```

**Connect from JavaScript:**
```javascript
// dashboard.js
const ws = new WebSocket('ws://localhost:8765');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
        case 'orderbook':
            updateOrderBook(message.data);
            break;
        case 'fill':
            addFillToTable(message.data);
            break;
        case 'position':
            updatePositionTable(message.data);
            break;
    }
};

function updateOrderBook(data) {
    document.getElementById('best-bid').textContent = data.best_bid;
    document.getElementById('best-ask').textContent = data.best_ask;
    document.getElementById('spread').textContent = data.spread;
}
```

---

## 4. Building Custom Dashboards

### 4.1 Technology Stack Recommendations

**Option 1: Streamlit (Easiest)**
- ✅ Python-based
- ✅ Fast prototyping
- ✅ Auto-refresh capabilities
- ✅ Built-in charting (Plotly)
- ❌ Limited customization

**Option 2: Plotly Dash**
- ✅ More control than Streamlit
- ✅ Production-ready
- ✅ Real-time callbacks
- ⚠️ More code required

**Option 3: React + WebSocket**
- ✅ Full customization
- ✅ Professional UI
- ✅ Real-time updates
- ❌ Requires JavaScript knowledge

**Option 4: Jupyter Widgets (ipywidgets)**
- ✅ Great for research
- ✅ Interactive notebooks
- ⚠️ Not for production

### 4.2 Data Access Patterns

**For Live Monitoring:**

```python
# Method 1: Poll cache/catalog
class DashboardDataProvider:
    def __init__(self, catalog_path):
        self.catalog = ParquetDataCatalog(catalog_path)

    def get_live_positions(self):
        # Read from catalog or cache
        # Return as dict/DataFrame
        pass

    def get_account_balance(self):
        pass

    def get_recent_fills(self, limit=10):
        pass

# Method 2: Redis for real-time state
from redis import Redis

class RedisStateProvider:
    def __init__(self):
        self.redis = Redis(host='localhost', port=6379)

    def publish_position_update(self, position):
        self.redis.publish('positions', json.dumps({
            'instrument_id': str(position.instrument_id),
            'quantity': position.quantity.as_double(),
            # ...
        }))

    def subscribe_to_fills(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe('fills')
        for message in pubsub.listen():
            yield json.loads(message['data'])
```

---

## 5. Jupyter Notebook Integration

### 5.1 Interactive OrderBook Visualization

```python
# In Jupyter Notebook
from IPython.display import display, clear_output
import time

class JupyterOrderBookMonitor:
    """Live orderbook monitor for Jupyter notebooks."""

    def __init__(self, strategy, update_interval=1.0):
        self.strategy = strategy
        self.update_interval = update_interval
        self.running = False

    def start(self):
        """Start live monitoring."""
        self.running = True

        while self.running:
            book = self.strategy.cache.order_book(
                self.strategy.config.instrument_id
            )

            # Clear previous output
            clear_output(wait=True)

            # Display orderbook
            print(book.pprint(num_levels=10))

            # Display metrics
            print(f"\nSpread: {book.spread():.2f}")
            print(f"Midpoint: {book.midpoint():.2f}")

            # Display positions
            positions = list(self.strategy.cache.positions())
            if positions:
                print(f"\nOpen Positions: {len(positions)}")
                for pos in positions:
                    print(f"  {pos.instrument_id}: {pos.quantity} @ {pos.avg_px_open}")

            time.sleep(self.update_interval)

    def stop(self):
        """Stop monitoring."""
        self.running = False

# Usage
monitor = JupyterOrderBookMonitor(my_strategy, update_interval=1.0)
monitor.start()  # Ctrl+C to stop
```

### 5.2 Plotly Integration in Jupyter

```python
# In Jupyter Notebook
%matplotlib inline
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_live_dashboard(engine):
    """Create multi-panel dashboard in Jupyter."""

    # Get data
    analyzer = engine.portfolio.analyzer
    returns = analyzer.returns()

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Equity Curve', 'Drawdown', 'Returns Distribution', 'Monthly Returns'),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "histogram"}, {"type": "heatmap"}],
        ],
    )

    # Equity curve
    cumulative_returns = (1 + returns).cumprod()
    fig.add_trace(
        go.Scatter(x=returns.index, y=cumulative_returns, name='Equity'),
        row=1, col=1,
    )

    # Drawdown
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    fig.add_trace(
        go.Scatter(x=returns.index, y=drawdown, name='Drawdown', fill='tozeroy'),
        row=1, col=2,
    )

    # Returns distribution
    fig.add_trace(
        go.Histogram(x=returns, name='Returns', nbinsx=50),
        row=2, col=1,
    )

    # Monthly returns heatmap
    monthly_returns = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    years = monthly_returns.index.year.unique()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    matrix = []
    for year in years:
        year_data = monthly_returns[monthly_returns.index.year == year]
        row = [year_data.get(year_data.index[year_data.index.month == m][0], 0)
               if len(year_data.index[year_data.index.month == m]) > 0 else 0
               for m in range(1, 13)]
        matrix.append(row)

    fig.add_trace(
        go.Heatmap(z=matrix, x=months, y=years, colorscale='RdYlGn'),
        row=2, col=2,
    )

    fig.update_layout(height=800, showlegend=False, template='plotly_dark')
    fig.show()

# Usage
create_live_dashboard(backtest_engine)
```

---

## 6. Complete Examples

### 6.1 Complete Live Monitoring Strategy

```python
# complete_monitor.py
import plotly.graph_objects as go
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import OrderBookDeltas
import time

class CompleteLiveMonitor(Strategy):
    """
    Complete monitoring strategy with visualization.

    Features:
    - Console logging
    - Periodic orderbook snapshots
    - PnL tracking
    - Fill tracking
    """

    def __init__(self, config):
        super().__init__(config)
        self.fills = []
        self.pnl_history = []
        self.last_snapshot_time = 0

    def on_start(self):
        self.subscribe_order_book_deltas(
            self.config.instrument_id,
            BookType.L2_MBP,
            depth=20,
        )

    def on_order_book_deltas(self, deltas: OrderBookDeltas):
        # Snapshot every 10 seconds
        now = self.clock.timestamp_ns()
        if now - self.last_snapshot_time > 10_000_000_000:
            self.save_orderbook_snapshot()
            self.last_snapshot_time = now

    def on_order_filled(self, event):
        # Track fills
        self.fills.append({
            'timestamp': self.clock.utc_now(),
            'order_id': str(event.client_order_id),
            'instrument': str(event.instrument_id),
            'side': str(event.order_side),
            'price': event.last_px.as_double(),
            'quantity': event.last_qty.as_double(),
        })

        self.log.info(
            f"✅ FILL: {event.order_side} {event.last_qty} "
            f"{event.instrument_id} @ {event.last_px}"
        )

        # Save fills to file
        self.save_fills_report()

    def on_position_changed(self, event):
        position = self.cache.position(event.position_id)
        unrealized_pnl = position.unrealized_pnl(position.last).as_double()

        # Track PnL
        self.pnl_history.append({
            'timestamp': self.clock.utc_now(),
            'unrealized_pnl': unrealized_pnl,
        })

        self.log.info(f"📊 Unrealized PnL: {unrealized_pnl:.2f}")

        # Update PnL chart
        self.update_pnl_chart()

    def save_orderbook_snapshot(self):
        """Save current orderbook state as image."""
        book = self.cache.order_book(self.config.instrument_id)

        fig = create_dom_chart(book, num_levels=20)
        filename = f"orderbook_{self.clock.timestamp_ns()}.html"
        fig.write_html(filename)

        self.log.info(f"💾 Saved orderbook snapshot: {filename}")

    def save_fills_report(self):
        """Save fills to CSV."""
        import pandas as pd
        df = pd.DataFrame(self.fills)
        df.to_csv("fills_report.csv", index=False)

    def update_pnl_chart(self):
        """Update live PnL chart."""
        import pandas as pd

        df = pd.DataFrame(self.pnl_history)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['unrealized_pnl'],
            mode='lines+markers',
            name='Unrealized PnL',
        ))
        fig.update_layout(title='Live PnL', template='plotly_dark')
        fig.write_html("live_pnl.html")

    def on_stop(self):
        # Generate final report
        self.log.info(f"\n{'='*50}")
        self.log.info("FINAL STATISTICS")
        self.log.info(f"{'='*50}")
        self.log.info(f"Total Fills: {len(self.fills)}")

        if self.pnl_history:
            final_pnl = self.pnl_history[-1]['unrealized_pnl']
            self.log.info(f"Final PnL: {final_pnl:.2f}")

        self.log.info("Reports saved:")
        self.log.info("  - fills_report.csv")
        self.log.info("  - live_pnl.html")
```

---

## 7. Summary & Recommendations

### What NautilusTrader Provides:

✅ **Post-Backtest Visualization:**
- HTML tearsheets with Plotly
- Equity curves, drawdowns, returns analysis
- Performance statistics

✅ **OrderBook Text Display:**
- `book.pprint()` for console display
- Tabular bid/ask visualization

✅ **Data Reports:**
- Account, position, fill reports
- CSV export capabilities

### What You Need to Build:

❌ **Real-Time Visualizations:**
- DOM charts (use Plotly examples above)
- Price ladders (use table examples above)
- Live dashboards (use Streamlit/Dash)

❌ **Live Monitoring:**
- WebSocket API (build custom)
- Real-time web UI (React + WebSocket)

### Recommended Approach:

**For Research/Backtesting:**
1. Use built-in tearsheets: `create_tearsheet(engine)`
2. Use Jupyter notebooks for interactive analysis
3. Export custom charts with Plotly

**For Live Trading:**
1. Start with console logging
2. Build Streamlit dashboard for monitoring
3. Export state to Redis for external access
4. Build WebSocket API for advanced UIs

**For Production:**
1. Implement Redis pub/sub for state sharing
2. Build custom React/Vue dashboard
3. Use Grafana + Prometheus for metrics
4. Implement alerting (email, SMS, Slack)

---

## 8. Future Enhancements

**Could Be Added to NautilusTrader:**
- Built-in WebSocket API server
- Default Streamlit dashboard template
- Real-time Plotly Dash integration
- Grafana exporter
- Built-in DOM visualization

**Community Contributions Welcome!**

---

**End of Guide**

For more information:
- Tearsheet API: `nautilus_trader/analysis/tearsheet.py`
- OrderBook: `nautilus_trader/model/book.pyx`
- Examples: `examples/backtest/` directory
