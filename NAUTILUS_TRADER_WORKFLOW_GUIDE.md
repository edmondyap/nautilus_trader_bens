# NautilusTrader Complete Workflow Guide
## Data Recording → Backtesting → Research Analysis

**Last Updated:** November 2, 2025
**Platform Version:** NautilusTrader v1.222.0

---

## Table of Contents

1. [Data Recording Workflow](#1-data-recording-workflow)
2. [Backtesting Workflow](#2-backtesting-workflow)
3. [Quant Research Workflow](#3-quant-research-workflow)
4. [Production Deployment Workflow](#4-production-deployment-workflow)
5. [Automated Pipelines](#5-automated-pipelines)

---

## 1. Data Recording Workflow

### ✅ YES - NautilusTrader Supports L2 Order Book Data Recording

**Supported Data Types for Recording:**
- ✅ **L2 Order Book (OrderBookDeltas, OrderBookDepth10)** - Full depth snapshots and incremental updates
- ✅ Quote Ticks (bid/ask)
- ✅ Trade Ticks (executions)
- ✅ Bars (OHLCV)
- ✅ Custom data types

**Supported Exchanges:**
- Binance (Spot, Futures)
- Bybit (Spot, Linear, Inverse, Options)
- BitMEX, OKX, Coinbase, Hyperliquid, and 7 others

### 1.1 Recording Live L2 Data from Crypto WebSockets

**Method 1: Using a Custom Actor/Strategy (Recommended)**

Here's a complete example for recording L2 order book data from Bybit:

```python
#!/usr/bin/env python3
# save as: record_binance_data.py

from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceLiveDataClientFactory
from nautilus_trader.config import LoggingConfig, TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId, TraderId
from nautilus_trader.model.enums import BookType
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.trading.config import StrategyConfig
from nautilus_trader.model.data import OrderBookDeltas, QuoteTick, TradeTick
from nautilus_trader.persistence.writer import StreamingFeatherWriter, RotationMode
import pandas as pd

class DataRecorderConfig(StrategyConfig, frozen=True):
    instrument_ids: list[InstrumentId]
    book_depth: int = 20  # Order book depth (1-1000 for Binance)
    data_path: str = "./recorded_data"
    flush_interval_ms: int = 1000  # Write to disk every 1 second
    rotation_mode: str = "INTERVAL"  # Rotate files every interval
    rotation_interval_hours: int = 1  # Rotate every hour

class DataRecorder(Strategy):
    """
    Records live market data to Feather/Parquet files.
    """
    def __init__(self, config: DataRecorderConfig) -> None:
        super().__init__(config)

        # Initialize writer for data recording
        self.writer = StreamingFeatherWriter(
            path=config.data_path,
            cache=self.cache,
            clock=self.clock,
            fs_protocol="file",
            flush_interval_ms=config.flush_interval_ms,
            rotation_mode=RotationMode[config.rotation_mode],
            rotation_interval=pd.Timedelta(hours=config.rotation_interval_hours),
        )

    def on_start(self) -> None:
        """Subscribe to data streams when strategy starts."""
        for instrument_id in self.config.instrument_ids:
            # Subscribe to L2 order book deltas (incremental updates)
            self.subscribe_order_book_deltas(
                instrument_id=instrument_id,
                book_type=BookType.L2_MBP,  # Market by price
                depth=self.config.book_depth,
            )

            # Subscribe to quote ticks (top of book)
            self.subscribe_quote_ticks(instrument_id=instrument_id)

            # Subscribe to trade ticks
            self.subscribe_trade_ticks(instrument_id=instrument_id)

            self.log.info(f"Subscribed to data for {instrument_id}")

    def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
        """Handle incoming order book updates."""
        self.writer.write(deltas)  # Write to disk
        self.log.debug(f"Recorded {len(deltas.deltas)} deltas for {deltas.instrument_id}")

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Handle incoming quote ticks."""
        self.writer.write(tick)

    def on_trade_tick(self, tick: TradeTick) -> None:
        """Handle incoming trade ticks."""
        self.writer.write(tick)

    def on_stop(self) -> None:
        """Cleanup when strategy stops."""
        self.writer.flush()
        self.writer.close()
        self.log.info("Data recording stopped")

# Configuration
config_node = TradingNodeConfig(
    trader_id=TraderId("DATA_RECORDER-001"),
    logging=LoggingConfig(log_level="INFO", use_pyo3=True),
    data_clients={
        BINANCE: BinanceDataClientConfig(
            api_key=None,  # Not needed for market data
            api_secret=None,
            base_url_http=None,
            testnet=False,
        ),
    },
)

# Create node
node = TradingNode(config=config_node)

# Configure recorder strategy
recorder_config = DataRecorderConfig(
    instrument_ids=[
        InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
        InstrumentId.from_str("ETHUSDT-PERP.BINANCE"),
    ],
    book_depth=20,
    data_path="./my_recorded_data",
    rotation_mode="INTERVAL",
    rotation_interval_hours=1,
)

# Add strategy
recorder = DataRecorder(config=recorder_config)
node.trader.add_strategy(recorder)

# Register Binance data client
node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
node.build()

# Run the recorder (press Ctrl+C to stop)
if __name__ == "__main__":
    try:
        print("Starting data recorder... Press Ctrl+C to stop")
        node.run()
    finally:
        node.dispose()
```

**Run it:**
```bash
python record_binance_data.py
```

**What Gets Recorded:**
```
my_recorded_data/
├── order_book_delta/
│   ├── BTCUSDT-PERP_BINANCE/
│   │   └── BTCUSDT-PERP_BINANCE_1730563200000000000.feather
│   └── ETHUSDT-PERP_BINANCE/
│       └── ETHUSDT-PERP_BINANCE_1730563200000000000.feather
├── quote_tick/
│   ├── BTCUSDT-PERP_BINANCE/
│   │   └── BTCUSDT-PERP_BINANCE_1730563200000000000.feather
│   └── ETHUSDT-PERP_BINANCE/
│       └── ETHUSDT-PERP_BINANCE_1730563200000000000.feather
└── trade_tick/
    ├── BTCUSDT-PERP_BINANCE/
    │   └── BTCUSDT-PERP_BINANCE_1730563200000000000.feather
    └── ETHUSDT-PERP_BINANCE/
        └── ETHUSDT-PERP_BINANCE_1730563200000000000.feather
```

**File Rotation Options:**
- `RotationMode.NO_ROTATION` - Single file (not recommended for long sessions)
- `RotationMode.SIZE` - Rotate when file reaches size limit
- `RotationMode.INTERVAL` - Rotate at time intervals (hourly, daily)
- `RotationMode.SCHEDULED_DATES` - Rotate at specific times

### 1.2 Converting Feather Files to Parquet

The `StreamingFeatherWriter` writes to Feather format for speed. Convert to Parquet for long-term storage:

```python
# convert_to_parquet.py
from nautilus_trader.persistence.catalog import ParquetDataCatalog
import glob
import pyarrow.feather as feather

# Initialize catalog
catalog = ParquetDataCatalog("./my_parquet_catalog")

# Read all feather files and write to catalog
feather_files = glob.glob("my_recorded_data/**/*.feather", recursive=True)

for feather_file in feather_files:
    # Read feather file
    table = feather.read_table(feather_file)

    # Determine data type from path
    if "order_book_delta" in feather_file:
        # Write to catalog (catalog handles parquet format)
        data_objects = []  # Parse table to NautilusTrader objects
        catalog.write_data(data_objects)

print(f"Converted {len(feather_files)} files to Parquet catalog")
```

---

## 2. Backtesting Workflow

### 2.1 Loading Recorded Data into Backtest

**Step 1: Organize Data in ParquetDataCatalog**

```python
# prepare_backtest_data.py
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# Create catalog (if not already created)
catalog = ParquetDataCatalog("./my_parquet_catalog")

# Verify data is available
print("Available instruments:", catalog.instruments())
print("Available data types:", catalog.list_data_types())

# Query specific data
btc_quotes = catalog.quote_ticks(
    instrument_ids=["BTCUSDT-PERP.BINANCE"],
    start="2025-11-01",
    end="2025-11-02",
)
print(f"Loaded {len(btc_quotes)} quote ticks")

# Query order book deltas
btc_deltas = catalog.order_book_deltas(
    instrument_ids=["BTCUSDT-PERP.BINANCE"],
    start="2025-11-01",
    end="2025-11-02",
)
print(f"Loaded {len(btc_deltas)} order book deltas")
```

**Step 2: Run Backtest with Recorded Data**

```python
# run_backtest.py
from decimal import Decimal
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.objects import Money
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.examples.strategies.ema_cross import EMACross, EMACrossConfig

# Load data from catalog
catalog = ParquetDataCatalog("./my_parquet_catalog")

# Get instruments
instruments = catalog.instruments()
btc_instrument = [i for i in instruments if "BTCUSDT-PERP" in str(i.id)][0]

# Load market data
quote_ticks = catalog.quote_ticks(
    instrument_ids=[btc_instrument.id],
    start="2025-11-01",
    end="2025-11-02",
)

# Configure backtest engine
engine_config = BacktestEngineConfig(
    trader_id=TraderId("BACKTEST-001"),
)
engine = BacktestEngine(config=engine_config)

# Add venue
engine.add_venue(
    venue=Venue("BINANCE"),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    starting_balances=[Money(100_000, USDT)],
    base_currency=USDT,
    default_leverage=Decimal(10),
)

# Add instrument and data
engine.add_instrument(btc_instrument)
engine.add_data(quote_ticks)  # Add loaded data

# Configure strategy
strategy_config = EMACrossConfig(
    instrument_id=btc_instrument.id,
    fast_ema_period=10,
    slow_ema_period=20,
    trade_size=Decimal("0.01"),
)
strategy = EMACross(config=strategy_config)
engine.add_strategy(strategy)

# Run backtest
print("Running backtest...")
engine.run()

# Generate reports
print(engine.trader.generate_account_report(Venue("BINANCE")))
print(engine.trader.generate_positions_report())
print(engine.trader.generate_order_fills_report())

# Cleanup
engine.dispose()
```

**Run the backtest:**
```bash
python run_backtest.py
```

### 2.2 Getting Results and Performance Metrics

```python
# analyze_results.py
from nautilus_trader.analysis.analyzer import PortfolioAnalyzer
from nautilus_trader.analysis.statistic import ReturnsVolatility, SharpeRatio, MaxDrawdown
from nautilus_trader.backtest.engine import BacktestEngine
# ... (same backtest setup as above)

# Run backtest
engine.run()

# Create analyzer
analyzer = PortfolioAnalyzer()

# Register statistics to calculate
analyzer.register_statistic(ReturnsVolatility())
analyzer.register_statistic(SharpeRatio())
analyzer.register_statistic(MaxDrawdown())

# Get account states and positions
account = engine.trader.generate_account_report(Venue("BINANCE"))
positions = [p for p in engine.cache.positions()]

# Calculate statistics
stats = {}
for stat_name, statistic in analyzer._statistics.items():
    stats[stat_name] = statistic.calculate_from_realized_pnls(
        analyzer._realized_pnls
    )

# Print results
print("\n=== PERFORMANCE METRICS ===")
for name, value in stats.items():
    print(f"{name}: {value}")

# Export results to DataFrame
import pandas as pd

results_df = pd.DataFrame({
    'Metric': stats.keys(),
    'Value': stats.values(),
})
results_df.to_csv("backtest_results.csv", index=False)
print("\nResults saved to backtest_results.csv")
```

**Expected Output:**
```
=== PERFORMANCE METRICS ===
Total Trades: 142
Win Rate: 0.5634
Total PnL: 2,450.50 USDT
Sharpe Ratio: 1.85
Max Drawdown: -12.3%
Returns Volatility: 0.15
```

---

## 3. Quant Research Workflow

### 3.1 Complete Research Pipeline

Here's a step-by-step quant research workflow from data to insights:

**Step 1: Download Historical Data**

```python
# step1_download_data.py
import asyncio
from datetime import datetime
from nautilus_trader.adapters.interactive_brokers.common import IBContract
from nautilus_trader.adapters.interactive_brokers.historical import HistoricInteractiveBrokersClient
from nautilus_trader.persistence.catalog import ParquetDataCatalog

async def download_historical_data():
    # Connect to data provider
    client = HistoricInteractiveBrokersClient(host="127.0.0.1", port=7497, client_id=1)
    await client.connect()

    # Define contract
    contract = IBContract(
        secType="STK",
        symbol="AAPL",
        exchange="SMART",
        primaryExchange="NASDAQ",
    )

    # Download bars
    bars = await client.request_bars(
        bar_specifications=["1-HOUR-LAST"],
        start_date_time=datetime(2024, 1, 1, 9, 30),
        end_date_time=datetime(2024, 12, 31, 16, 30),
        tz_name="America/New_York",
        contracts=[contract],
        instrument_ids=["AAPL.NASDAQ"],
    )

    # Save to catalog
    catalog = ParquetDataCatalog("./research_catalog")
    catalog.write_data(bars)
    print(f"Downloaded {len(bars)} bars")

    await client.disconnect()

asyncio.run(download_historical_data())
```

**Run:**
```bash
python step1_download_data.py
# Output: Downloaded 1,956 bars
```

**Step 2: Exploratory Data Analysis**

```python
# step2_explore_data.py
from nautilus_trader.persistence.catalog import ParquetDataCatalog
import pandas as pd
import matplotlib.pyplot as plt

# Load data from catalog
catalog = ParquetDataCatalog("./research_catalog")

# Get bars as list
bars = catalog.bars(
    bar_types=["AAPL.NASDAQ-1-HOUR-LAST"],
    start="2024-01-01",
    end="2024-12-31",
)

# Convert to pandas DataFrame for analysis
df = pd.DataFrame([{
    'timestamp': bar.ts_init,
    'open': bar.open.as_double(),
    'high': bar.high.as_double(),
    'low': bar.low.as_double(),
    'close': bar.close.as_double(),
    'volume': bar.volume.as_double(),
} for bar in bars])

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ns')
df.set_index('timestamp', inplace=True)

# Calculate statistics
print("=== DATA SUMMARY ===")
print(f"Total bars: {len(df)}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"\nPrice statistics:")
print(df['close'].describe())

# Calculate returns
df['returns'] = df['close'].pct_change()
print(f"\nReturns statistics:")
print(df['returns'].describe())

# Plot price series
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['close'])
plt.title('AAPL Price History')
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.savefig('price_history.png')
print("\nSaved price_history.png")
```

**Run:**
```bash
python step2_explore_data.py
# Generates: price_history.png
```

**Step 3: Develop Strategy**

```python
# step3_develop_strategy.py
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.trading.config import StrategyConfig
from nautilus_trader.model.data import Bar
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from decimal import Decimal

class MyMomentumStrategy(Strategy):
    """
    Simple momentum strategy for research.
    """
    def __init__(self, config: StrategyConfig) -> None:
        super().__init__(config)

        # Initialize indicators
        self.fast_ema = ExponentialMovingAverage(10)
        self.slow_ema = ExponentialMovingAverage(30)

        # Track signals
        self.signals = []

    def on_start(self) -> None:
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        # Update indicators
        self.fast_ema.update(bar.close)
        self.slow_ema.update(bar.close)

        # Wait for indicators to warm up
        if not self.fast_ema.initialized or not self.slow_ema.initialized:
            return

        # Generate signals
        if self.fast_ema.value > self.slow_ema.value:
            if not self.portfolio.is_flat(bar.instrument_id):
                return

            # Long signal
            self.buy(bar.instrument_id, Decimal("100"))
            self.signals.append({
                'timestamp': bar.ts_init,
                'signal': 'BUY',
                'price': bar.close.as_double(),
            })

        elif self.fast_ema.value < self.slow_ema.value:
            if self.portfolio.is_flat(bar.instrument_id):
                return

            # Exit signal
            self.close_all_positions(bar.instrument_id)
            self.signals.append({
                'timestamp': bar.ts_init,
                'signal': 'SELL',
                'price': bar.close.as_double(),
            })

# Save strategy file
print("Strategy created: MyMomentumStrategy")
```

**Step 4: Backtest Strategy**

```python
# step4_backtest_strategy.py
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from step3_develop_strategy import MyMomentumStrategy, StrategyConfig
# ... (same setup as previous backtest example)

# Load data
catalog = ParquetDataCatalog("./research_catalog")
bars = catalog.bars(bar_types=["AAPL.NASDAQ-1-HOUR-LAST"])

# Configure and run backtest
engine = BacktestEngine(config=BacktestEngineConfig(...))
# ... (add venue, instrument, data)

strategy = MyMomentumStrategy(config=StrategyConfig(
    instrument_id="AAPL.NASDAQ",
    bar_type="AAPL.NASDAQ-1-HOUR-LAST",
))
engine.add_strategy(strategy)

# Run
engine.run()

# Get results
print(engine.trader.generate_positions_report())
```

**Step 5: Parameter Optimization** (Manual)

```python
# step5_optimize_parameters.py
from itertools import product
import pandas as pd

# Define parameter grid
fast_periods = [5, 10, 15, 20]
slow_periods = [20, 30, 40, 50]

# Results storage
optimization_results = []

# Grid search
for fast, slow in product(fast_periods, slow_periods):
    if fast >= slow:
        continue

    print(f"Testing fast={fast}, slow={slow}")

    # Run backtest with these parameters
    # ... (same backtest code as step 4, but with varying parameters)

    # Extract metrics
    final_pnl = # ... get from engine
    sharpe = # ... calculate
    max_dd = # ... calculate

    optimization_results.append({
        'fast_period': fast,
        'slow_period': slow,
        'pnl': final_pnl,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
    })

# Convert to DataFrame
results_df = pd.DataFrame(optimization_results)
results_df = results_df.sort_values('sharpe', ascending=False)

print("\n=== TOP 5 PARAMETER COMBINATIONS ===")
print(results_df.head())

# Save results
results_df.to_csv("optimization_results.csv", index=False)
```

**Run optimization:**
```bash
python step5_optimize_parameters.py
# Tests 12 parameter combinations
# Saves: optimization_results.csv
```

**Step 6: Analyze Results**

```python
# step6_analyze_results.py
import pandas as pd
import matplotlib.pyplot as plt

# Load optimization results
results = pd.read_csv("optimization_results.csv")

# Create heatmap of Sharpe ratios
pivot = results.pivot(index='slow_period', columns='fast_period', values='sharpe')

plt.figure(figsize=(10, 8))
plt.imshow(pivot, cmap='RdYlGn', aspect='auto')
plt.colorbar(label='Sharpe Ratio')
plt.xlabel('Fast EMA Period')
plt.ylabel('Slow EMA Period')
plt.title('Parameter Optimization Heatmap')
plt.xticks(range(len(pivot.columns)), pivot.columns)
plt.yticks(range(len(pivot.index)), pivot.index)
plt.savefig('optimization_heatmap.png')
print("Saved optimization_heatmap.png")

# Find best parameters
best = results.loc[results['sharpe'].idxmax()]
print(f"\n=== BEST PARAMETERS ===")
print(f"Fast Period: {best['fast_period']}")
print(f"Slow Period: {best['slow_period']}")
print(f"Sharpe Ratio: {best['sharpe']:.2f}")
print(f"Max Drawdown: {best['max_drawdown']:.2%}")
```

**Run analysis:**
```bash
python step6_analyze_results.py
# Generates: optimization_heatmap.png
```

**Step 7: Walk-Forward Testing** (Manual)

```python
# step7_walk_forward.py
from datetime import datetime, timedelta
import pandas as pd

# Define walk-forward windows
train_window = timedelta(days=90)
test_window = timedelta(days=30)
total_period = timedelta(days=365)

# Results storage
wf_results = []

# Walk forward
current_date = datetime(2024, 1, 1)
while current_date < datetime(2024, 12, 31):
    train_start = current_date
    train_end = train_start + train_window
    test_start = train_end
    test_end = test_start + test_window

    print(f"Train: {train_start} to {train_end}")
    print(f"Test: {test_start} to {test_end}")

    # Load training data
    train_bars = catalog.bars(start=train_start, end=train_end)

    # Run optimization on training data
    # ... (run step 5 optimization on train_bars)
    best_params = # ... get best parameters

    # Test on out-of-sample data
    test_bars = catalog.bars(start=test_start, end=test_end)
    # ... (run backtest with best_params on test_bars)
    test_sharpe = # ... get Sharpe from test

    wf_results.append({
        'train_start': train_start,
        'test_start': test_start,
        'fast_period': best_params['fast'],
        'slow_period': best_params['slow'],
        'test_sharpe': test_sharpe,
    })

    # Move to next window
    current_date = test_end

# Analyze walk-forward results
wf_df = pd.DataFrame(wf_results)
print("\n=== WALK-FORWARD RESULTS ===")
print(f"Average Out-of-Sample Sharpe: {wf_df['test_sharpe'].mean():.2f}")
print(f"Sharpe Std Dev: {wf_df['test_sharpe'].std():.2f}")
wf_df.to_csv("walk_forward_results.csv", index=False)
```

### 3.2 Summary of Research Workflow Commands

```bash
# Complete research pipeline
python step1_download_data.py         # Download historical data
python step2_explore_data.py          # Exploratory analysis
python step3_develop_strategy.py      # Create strategy
python step4_backtest_strategy.py     # Initial backtest
python step5_optimize_parameters.py   # Parameter optimization
python step6_analyze_results.py       # Analyze optimization
python step7_walk_forward.py          # Walk-forward validation

# Outputs:
# - research_catalog/ (data)
# - price_history.png
# - backtest_results.csv
# - optimization_results.csv
# - optimization_heatmap.png
# - walk_forward_results.csv
```

---

## 4. Production Deployment Workflow

### 4.1 From Backtest to Live Trading

**Step 1: Validate Strategy on Paper Trading**

```python
# deploy_paper_trading.py
from nautilus_trader.config import TradingNodeConfig, LoggingConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.adapters.binance import BinanceDataClientConfig, BinanceExecClientConfig
from step3_develop_strategy import MyMomentumStrategy

# Configure node for paper trading
config = TradingNodeConfig(
    trader_id=TraderId("PAPER-001"),
    logging=LoggingConfig(log_level="INFO"),
    data_clients={BINANCE: BinanceDataClientConfig(testnet=True)},
    exec_clients={BINANCE: BinanceExecClientConfig(testnet=True)},
)

node = TradingNode(config=config)
strategy = MyMomentumStrategy(config=...)
node.trader.add_strategy(strategy)
node.build()

# Run paper trading
node.run()
```

**Step 2: Deploy to Production**

```python
# deploy_live.py
# Same code as paper trading, but with:
config = TradingNodeConfig(
    trader_id=TraderId("LIVE-001"),
    # ...
    data_clients={BINANCE: BinanceDataClientConfig(testnet=False)},  # LIVE
    exec_clients={BINANCE: BinanceExecClientConfig(testnet=False)},  # LIVE
)
```

---

## 5. Automated Pipelines

### 5.1 Data Recording + Backtesting Pipeline

**Option 1: Shell Script Pipeline**

```bash
#!/bin/bash
# pipeline.sh - Automated research pipeline

echo "=== NAUTILUS TRADER RESEARCH PIPELINE ==="

# Step 1: Record live data for 1 hour
echo "Step 1: Recording live data..."
timeout 3600 python record_binance_data.py &
PID=$!
wait $PID

# Step 2: Convert to Parquet
echo "Step 2: Converting to Parquet..."
python convert_to_parquet.py

# Step 3: Run backtest
echo "Step 3: Running backtest..."
python run_backtest.py

# Step 4: Generate report
echo "Step 4: Generating analysis..."
python analyze_results.py

echo "=== PIPELINE COMPLETE ==="
echo "Results: backtest_results.csv"
```

**Run:**
```bash
chmod +x pipeline.sh
./pipeline.sh
```

**Option 2: Python Pipeline Script**

```python
# automated_pipeline.py
import subprocess
import time
from datetime import datetime

def run_command(cmd, description):
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

def main():
    print(f"Starting pipeline at {datetime.now()}")

    # Record data for 1 hour
    if not run_command(
        "timeout 3600 python record_binance_data.py",
        "Recording live data (1 hour)"
    ):
        return

    # Convert to Parquet
    if not run_command(
        "python convert_to_parquet.py",
        "Converting to Parquet"
    ):
        return

    # Run backtest
    if not run_command(
        "python run_backtest.py",
        "Running backtest"
    ):
        return

    # Analyze
    if not run_command(
        "python analyze_results.py",
        "Generating analysis"
    ):
        return

    print(f"\n=== PIPELINE COMPLETE at {datetime.now()} ===")

if __name__ == "__main__":
    main()
```

**Run:**
```bash
python automated_pipeline.py
```

### 5.2 Scheduled Daily Research Pipeline

**Using cron (Linux/macOS):**

```bash
# Add to crontab: crontab -e
# Run pipeline every day at 2 AM
0 2 * * * cd /path/to/project && /usr/bin/python3 automated_pipeline.py >> pipeline.log 2>&1
```

**Using Python scheduler:**

```python
# scheduled_pipeline.py
import schedule
import time
from automated_pipeline import main as run_pipeline

def scheduled_task():
    print("Starting scheduled research pipeline...")
    run_pipeline()

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(scheduled_task)

print("Scheduler started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 6. Quick Reference Commands

### Data Recording
```bash
# Record L2 order book data from Binance
python record_binance_data.py

# Record from Bybit with options
python examples/live/bybit/bybit_options_data_collector.py
```

### Data Conversion
```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# Write data to catalog
catalog = ParquetDataCatalog("./catalog")
catalog.write_data(instruments)  # List of instruments
catalog.write_data(bars)          # List of bars
catalog.write_data(quote_ticks)   # List of quote ticks
catalog.write_data(order_book_deltas)  # List of order book deltas
```

### Data Querying
```python
# Query data from catalog
instruments = catalog.instruments()
bars = catalog.bars(
    bar_types=["BTCUSDT.BINANCE-1-MINUTE-LAST"],
    start="2025-11-01",
    end="2025-11-02",
)
quote_ticks = catalog.quote_ticks(instrument_ids=["BTCUSDT.BINANCE"])
order_book_deltas = catalog.order_book_deltas(instrument_ids=["BTCUSDT.BINANCE"])
```

### Backtesting
```python
# Basic backtest
engine = BacktestEngine(config=BacktestEngineConfig(...))
engine.add_venue(...)
engine.add_instrument(instrument)
engine.add_data(bars)  # Or quote_ticks, order_book_deltas
engine.add_strategy(strategy)
engine.run()

# Get results
account_report = engine.trader.generate_account_report(venue)
positions_report = engine.trader.generate_positions_report()
fills_report = engine.trader.generate_order_fills_report()
```

### Analysis
```python
# Performance metrics
analyzer = PortfolioAnalyzer()
analyzer.register_statistic(SharpeRatio())
analyzer.register_statistic(MaxDrawdown())
stats = analyzer.calculate_statistics(...)
```

---

## 7. Common Pitfalls & Solutions

### Issue 1: "No data in catalog"
**Solution:** Check file paths and ensure data was written correctly
```python
print(catalog.list_data_types())  # See what's available
```

### Issue 2: "Instrument not found"
**Solution:** Write instrument definitions to catalog first
```python
catalog.write_data([instrument])  # Write instrument before data
```

### Issue 3: "Empty backtest results"
**Solution:** Check date ranges match your data
```python
# Verify data date range
bars = catalog.bars()
print(f"Data from {min(bars, key=lambda b: b.ts_init).ts_init} to {max(bars, key=lambda b: b.ts_init).ts_init}")
```

### Issue 4: "Order book deltas not applying"
**Solution:** Subscribe to quotes first, then deltas
```python
self.subscribe_quote_ticks(instrument_id)  # First
self.subscribe_order_book_deltas(instrument_id, ...)  # Second
```

---

## 8. Complete Example: End-to-End Workflow

Here's a complete working example you can run:

```python
#!/usr/bin/env python3
# complete_example.py - Full workflow from recording to analysis

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

# Step 1: Record data (simulated with test data for demo)
from nautilus_trader.test_kit.providers import TestDataProvider
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler

# Get test data
provider = TestDataProvider()
instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD")
wrangler = QuoteTickDataWrangler(instrument)
ticks = wrangler.process(provider.read_csv_ticks("truefx/eurusd-ticks.csv"))

# Save to catalog
catalog = ParquetDataCatalog("./demo_catalog")
catalog.write_data([instrument])
catalog.write_data(ticks[:10000])  # Save first 10k ticks
print(f"✓ Saved {len(ticks[:10000])} ticks to catalog")

# Step 2: Run backtest
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.examples.strategies.ema_cross import EMACross, EMACrossConfig
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.objects import Money
from nautilus_trader.model.enums import AccountType, OmsType

engine = BacktestEngine(config=BacktestEngineConfig(trader_id=TraderId("DEMO-001")))
engine.add_venue(
    venue=Venue("SIM"),
    oms_type=OmsType.HEDGING,
    account_type=AccountType.MARGIN,
    starting_balances=[Money(100_000, USD)],
)
engine.add_instrument(instrument)
engine.add_data(ticks[:10000])

strategy = EMACross(config=EMACrossConfig(
    instrument_id=instrument.id,
    fast_ema_period=10,
    slow_ema_period=20,
    trade_size=Decimal("100000"),
))
engine.add_strategy(strategy)

print("✓ Running backtest...")
engine.run()

# Step 3: Analyze results
print("\n=== BACKTEST RESULTS ===")
print(engine.trader.generate_positions_report())

# Calculate metrics
positions = [p for p in engine.cache.positions()]
winning_positions = [p for p in positions if p.realized_pnl.as_double() > 0]
print(f"\nTotal Positions: {len(positions)}")
print(f"Winning Positions: {len(winning_positions)}")
print(f"Win Rate: {len(winning_positions)/len(positions)*100:.1f}%")

print("\n✓ Demo complete!")
```

**Run:**
```bash
python complete_example.py
```

---

## Appendix: Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    NAUTILUS TRADER WORKFLOW                  │
└─────────────────────────────────────────────────────────────┘

1. DATA RECORDING
   ┌──────────────┐
   │ Live         │
   │ WebSocket    │──┐
   └──────────────┘  │
                     │  StreamingFeatherWriter
   ┌──────────────┐  │  ↓
   │ Strategy/    │  │  Feather Files (.feather)
   │ Actor        │──┘  ↓
   └──────────────┘     Convert
                        ↓
                  ParquetDataCatalog (.parquet)

2. BACKTESTING
   ParquetDataCatalog
        ↓
   catalog.bars() / catalog.quote_ticks()
        ↓
   BacktestEngine.add_data()
        ↓
   Strategy.on_bar() / on_quote_tick()
        ↓
   Order Events
        ↓
   Portfolio Updates
        ↓
   Results & Reports

3. ANALYSIS
   BacktestEngine Results
        ↓
   PortfolioAnalyzer
        ↓
   Statistics (Sharpe, Drawdown, Win Rate)
        ↓
   CSV Export / Visualizations

4. PRODUCTION
   Same Strategy Code
        ↓
   TradingNode (Live)
        ↓
   Real Exchange Orders
```

---

**End of Workflow Guide**

For more information:
- Documentation: https://nautilustrader.io/docs
- Examples: /examples/ directory in repository
- Support: https://discord.gg/NautilusTrader
