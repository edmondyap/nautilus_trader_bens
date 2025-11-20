# Data

This directory stores all trading data.

## Structure

```
data/
├── raw/               # Raw data files (as downloaded)
│   ├── orderbook/    # L2 orderbook data (snapshots/deltas)
│   ├── trades/       # Trade tick data
│   └── bars/         # Bar/candle data (optional)
├── processed/         # Cleaned/processed data
│   ├── orderbook_features/  # Features extracted from L2 data
│   └── bars/         # Processed bar data
├── features/          # Engineered features for ML
├── alternative/       # Alternative data (news, social, etc.)
│   ├── news/
│   │   ├── raw/
│   │   └── processed/
│   ├── twitter/
│   └── reddit/
└── catalog/          # NautilusTrader ParquetDataCatalog
    ├── order_book_deltas/   # L2 orderbook deltas
    ├── order_book_depth10/  # L2 snapshots at depth
    ├── quote_ticks/         # Best bid/ask
    └── trade_ticks/         # Trades
```

## Data Organization

### Raw Data (`raw/`)

Original, unmodified data files.

```
raw/
├── binance/
│   ├── BTCUSDT_2024-01.csv
│   ├── BTCUSDT_2024-02.csv
│   └── ...
├── bybit/
└── databento/
```

**Never modify files in raw/** - keep original data intact.

### Processed Data (`processed/`)

Cleaned, validated, ready-to-use data.

```
processed/
├── BTCUSDT_1m_2024.parquet
├── ETHUSDT_1m_2024.parquet
└── multi_asset_2024.parquet
```

**Characteristics:**
- Cleaned (outliers removed, gaps filled)
- Validated (no missing values, correct types)
- Optimized format (Parquet for efficiency)

### Features (`features/`)

Engineered features for ML models.

```
features/
├── btcusdt_technical_features_2024.parquet
├── ethusdt_all_features_2024.parquet
└── multi_asset_features_2024.parquet
```

**Contains:**
- Technical indicators
- Alternative data features
- Derived features

### Alternative Data (`alternative/`)

Non-price data sources.

```
alternative/
├── news/
│   ├── raw/                  # Raw scraped articles
│   │   └── 2024-11/
│   │       ├── news_20241119.parquet
│   │       └── news_20241120.parquet
│   └── processed/            # With sentiment scores
│       ├── btc_news_2024.parquet
│       └── eth_news_2024.parquet
├── twitter/
│   ├── raw/
│   └── processed/
└── reddit/
    ├── raw/
    └── processed/
```

### Orderbook Data (`raw/orderbook/` and `processed/orderbook_features/`)

**Primary data type for high-frequency and market making strategies.**

L2 (Level 2) orderbook data contains the full limit order book with multiple price levels.

#### Storage Structure
```
raw/orderbook/
├── binance/
│   ├── BTCUSDT/
│   │   ├── 2024-11-19_00.parquet    # Hourly files
│   │   ├── 2024-11-19_01.parquet
│   │   └── ...
│   └── ETHUSDT/
└── bybit/

processed/orderbook_features/
├── BTCUSDT_imbalance_2024.parquet   # Bid/ask imbalance features
├── BTCUSDT_depth_2024.parquet       # Depth features
└── BTCUSDT_spread_2024.parquet      # Spread metrics
```

#### Data Format
```python
# Orderbook snapshot/delta format
{
    'timestamp': int64,        # Nanosecond timestamp
    'instrument_id': str,      # e.g., 'BTCUSDT-PERP.BINANCE'
    'bids': List[Tuple],       # [(price, size), ...]
    'asks': List[Tuple],       # [(price, size), ...]
    'sequence': int64          # Message sequence number
}
```

#### Storage Best Practices

**1. Use NautilusTrader Catalog (Recommended)**
```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.data import OrderBookDeltas

catalog = ParquetDataCatalog('data/catalog')

# Write orderbook deltas
catalog.write_data([orderbook_deltas])

# Read orderbook deltas
deltas = catalog.order_book_deltas(
    instrument_ids=['BTCUSDT-PERP.BINANCE']
)
```

**2. Data Volume Considerations**

L2 orderbook data is **significantly larger** than bar data:
- Bars (1m): ~525K rows/year per instrument
- L2 snapshots (1s): ~31M rows/year per instrument
- L2 deltas: 100M+ events/year per instrument

**Storage recommendations:**
- Use Parquet with `gzip` or `zstd` compression
- Partition by date (hourly or daily files)
- Store only deltas, not full snapshots (reconstruct on-the-fly)
- Consider downsampling to 100ms or 1s snapshots for backtesting

**3. Example: Collecting Live L2 Data**
```python
# scripts/data/collect_orderbook_live.py
from nautilus_trader.live.node import TradingNode

# Subscribes to L2 orderbook via WebSocket
# NautilusTrader handles the orderbook state management
# Data automatically saved to catalog
```

#### Orderbook Features

Extract features from L2 data for ML models:

```python
# ml/features/orderbook.py
class OrderbookFeatures:
    @staticmethod
    def calculate_imbalance(bids, asks, depth=10):
        """Bid/ask volume imbalance"""
        bid_volume = sum(size for _, size in bids[:depth])
        ask_volume = sum(size for _, size in asks[:depth])
        return (bid_volume - ask_volume) / (bid_volume + ask_volume)

    @staticmethod
    def calculate_microprice(best_bid, best_ask, bid_size, ask_size):
        """Volume-weighted mid price"""
        return (best_bid * ask_size + best_ask * bid_size) / (bid_size + ask_size)
```

Common orderbook features to extract:
- **Imbalance**: Bid/ask volume imbalance at various depths
- **Microprice**: Volume-weighted mid price
- **Spread**: Bid-ask spread (absolute and relative)
- **Depth**: Total volume at different price levels
- **Order flow**: Net order flow over time windows
- **Toxicity**: VPIN (Volume-Synchronized Probability of Informed Trading)

### Catalog (`catalog/`)

NautilusTrader's ParquetDataCatalog - optimized storage for backtesting.

**Supports all data types including L2 orderbook:**

```
catalog/
├── instruments/
├── order_book_deltas/      # L2 orderbook deltas (recommended)
├── order_book_depth10/     # L2 snapshots at 10 levels
├── bars/                   # OHLCV bars
├── quote_ticks/           # Best bid/ask (Level 1)
└── trade_ticks/           # Executed trades
```

**Working with Orderbook Data:**
```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog('data/catalog')

# Query orderbook deltas
deltas = catalog.order_book_deltas(
    instrument_ids=['BTCUSDT-PERP.BINANCE'],
    start='2024-11-01',
    end='2024-11-19'
)

# NautilusTrader reconstructs orderbook state automatically
# Use in backtests or analysis
```

## Data Formats

### Recommended: Parquet
```python
# Save
df.to_parquet('data/processed/BTCUSDT_1m_2024.parquet')

# Load
df = pd.read_parquet('data/processed/BTCUSDT_1m_2024.parquet')
```

**Advantages:**
- Fast read/write
- Efficient compression
- Preserves data types
- Columnar storage (perfect for analytics)

### Also Supported: CSV
```python
# For raw data from exchanges
df = pd.read_csv('data/raw/binance/BTCUSDT.csv')
```

### NautilusTrader Catalog
```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog('data/catalog')

# Write data
catalog.write_data([bars])

# Read data
bars = catalog.bars(bar_types=['BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-INTERNAL'])
```

## Data Pipeline

```
1. Download Raw Data
   ├─> scripts/data/download_binance_data.py
   └─> Save to data/raw/

2. Process Data
   ├─> scripts/data/process_data.py
   ├─> Clean, validate
   └─> Save to data/processed/

3. Engineer Features (if needed)
   ├─> scripts/data/create_features.py
   └─> Save to data/features/

4. Load into Catalog (for NautilusTrader)
   ├─> scripts/data/build_catalog.py
   └─> Save to data/catalog/
```

## Git Ignore

**Important:** Data files should NOT be committed to git.

The `.gitignore` includes:
```
data/raw/*
data/processed/*
data/features/*
data/alternative/*/raw/*
data/alternative/*/processed/*
data/catalog/*
```

Only `.gitkeep` files are tracked to preserve directory structure.

## Data Loading Utilities

Use shared utilities for consistent loading:

```python
# shared/data/loaders.py
from shared.data.loaders import (
    load_binance_data,
    load_from_catalog,
    load_news_data
)

# Load price data
bars = load_binance_data('BTCUSDT', '2024-01-01', '2024-11-19')

# Load from catalog
bars = load_from_catalog('BTCUSDT-PERP.BINANCE', '1-MINUTE-LAST')

# Load news data
news = load_news_data('BTC', '2024-01-01', '2024-11-19')
```

## Data Size Management

### Compression
```python
# Parquet automatically compresses
df.to_parquet('data.parquet', compression='snappy')  # Default
df.to_parquet('data.parquet', compression='gzip')     # Higher compression
```

### Partitioning
```python
# For large datasets, partition by date
data/processed/
├── BTCUSDT/
│   ├── year=2024/
│   │   ├── month=01/
│   │   │   └── data.parquet
│   │   ├── month=02/
│   │   │   └── data.parquet
│   │   └── ...

# Read with filters
df = pd.read_parquet(
    'data/processed/BTCUSDT',
    filters=[('year', '=', 2024), ('month', '=', 11)]
)
```

### Archiving
```bash
# Archive old data
tar -czf data_archive_2023.tar.gz data/raw/2023/
rm -rf data/raw/2023/
```

## Best Practices

### 1. Preserve Raw Data
```python
# Never modify raw data
# Always create new processed files
```

### 2. Document Data Sources
```python
# Add metadata file
# data/raw/binance/METADATA.txt
"""
Source: Binance API
Download date: 2024-11-19
Symbols: BTCUSDT, ETHUSDT
Timeframe: 1 minute
Period: 2024-01-01 to 2024-11-19
Script: scripts/data/download_binance_data.py
"""
```

### 3. Validate Data
```python
def validate_ohlcv_data(df):
    """Validate OHLCV data"""
    assert 'timestamp' in df.columns
    assert 'open' in df.columns
    # ... other checks

    # Check for missing data
    assert df.isna().sum().sum() == 0

    # Check for duplicates
    assert df['timestamp'].duplicated().sum() == 0

    # Check OHLC relationships
    assert (df['high'] >= df['low']).all()
    assert (df['high'] >= df['open']).all()
```

### 4. Consistent Schemas
```python
# Standard OHLCV schema
OHLCV_SCHEMA = {
    'timestamp': 'datetime64[ns]',
    'open': 'float64',
    'high': 'float64',
    'low': 'float64',
    'close': 'float64',
    'volume': 'float64'
}
```

### 5. Incremental Updates
```python
# Don't re-download everything
# Load existing data and append new data

existing = pd.read_parquet('data/processed/BTCUSDT_2024.parquet')
last_date = existing['timestamp'].max()

# Download only new data since last_date
new_data = download_since(last_date)

# Append
updated = pd.concat([existing, new_data])
updated.to_parquet('data/processed/BTCUSDT_2024.parquet')
```

## Common Tasks

### Download Historical Data
```bash
python scripts/data/download_binance_data.py \
    --symbol BTCUSDT \
    --start 2024-01-01 \
    --end 2024-11-19 \
    --timeframe 1m
```

### Process Raw Data
```bash
python scripts/data/process_data.py \
    --input data/raw/binance/BTCUSDT.csv \
    --output data/processed/BTCUSDT_1m_2024.parquet
```

### Build NautilusTrader Catalog
```bash
python scripts/data/build_catalog.py \
    --input data/processed/ \
    --output data/catalog/
```

### Update with Latest Data
```bash
# Daily cron job
python scripts/data/update_daily.py
```

## Data Backup

```bash
# Backup processed data (raw can be re-downloaded)
rsync -av data/processed/ backup/data/processed/

# Or use cloud storage
aws s3 sync data/processed/ s3://my-bucket/trading-data/processed/
```

## Adding New Data Types

When adding a new data type (e.g., on-chain data):

```bash
# 1. Create directory structure
mkdir -p data/blockchain/{raw,processed}

# 2. Add .gitkeep
touch data/blockchain/raw/.gitkeep
touch data/blockchain/processed/.gitkeep

# 3. Update .gitignore
echo "data/blockchain/raw/*" >> .gitignore
echo "data/blockchain/processed/*" >> .gitignore

# 4. Create loading utility
# shared/data/loaders.py
def load_blockchain_data(chain, start, end):
    pass
```

## Data Sources

### Orderbook Data (L2)
- **Binance** - Free WebSocket API for real-time L2 orderbook
- **Bybit** - Free WebSocket API for real-time L2 orderbook
- **DataBento** - Paid, institutional quality L2 historical data
- **Tardis.dev** - Historical orderbook data (paid)
- **NautilusTrader Live Adapters** - Connect directly to exchanges for live L2 streaming

**Collecting Live Orderbook Data:**
```python
# NautilusTrader handles L2 WebSocket connections automatically
# See scripts/data/collect_orderbook_live.py for example
```

### Price Data (Bars/Candles)
- **Binance** - Free API, good historical data
- **Bybit** - Free API
- **Interactive Brokers** - Requires account
- **DataBento** - Paid, institutional quality

### Alternative Data
- **News**: NewsAPI, GDELT, CryptoPanic
- **Social**: Twitter API, Reddit API
- **On-chain**: Etherscan, Blockchain.com

### Economic Data
- **FRED** - Federal Reserve Economic Data
- **Yahoo Finance** - Free historical data

## Resources

- [Pandas Documentation](https://pandas.pydata.org/)
- [Parquet Format](https://parquet.apache.org/)
- [NautilusTrader Data Documentation](https://nautilustrader.io/docs/latest/concepts/data)
- Main README: [../README.md](../README.md)
