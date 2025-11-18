# Nautilus Trader: Pattern Extraction from bybit_options_data_collector.py

**Document Version**: 1.0  
**Created**: 2025-11-09  
**Agent**: Agent 5 (Explore Specialist)  
**Source File**: `nautilus_trader/examples/live/bybit/bybit_options_data_collector.py` (867 lines)  
**Purpose**: Extract reusable patterns for building a simplified SPOT data collector  

---

## Executive Summary

### Overview
The `bybit_options_data_collector.py` is a robust, production-ready example that:
- Collects data from 100+ instruments (OPTIONS + SPOT)
- Uses pandas DataFrame buffering (NOT ParquetDataCatalog)
- Writes directly to parquet with periodic flushing
- Implements comprehensive error handling and monitoring
- Total: 867 lines

### Key Findings

**Architecture**: Single Strategy class inheriting from `nautilus_trader.trading.strategy.Strategy`

**Data Flow**:
```
WebSocket Stream → on_quote_tick()/on_order_book_deltas() → 
dict[str, list[dict]] buffer → periodic flush → 
pandas.DataFrame → to_parquet() → disk
```

**Critical Discovery**: This example does NOT use ParquetDataCatalog for live collection. It uses:
1. In-memory dict buffers (`self.quote_ticks_data: dict[str, list[dict]]`)
2. Periodic DataFrame conversion
3. Direct parquet writes with `df.to_parquet()`

### Simplification Opportunity

| Component | Original LOC | Simplified Est. | Reduction | Notes |
|-----------|--------------|-----------------|-----------|-------|
| Config | 15 | 12 | 20% | Remove options-specific params |
| Initialization | 128 | 60 | 53% | No instrument discovery, single symbol |
| Instrument Discovery | 136 | 0 | 100% | Hardcode symbols |
| Subscription Management | 62 | 25 | 60% | Single subscribe call |
| Data Collection | 64 | 60 | 6% | Keep most logic |
| Data Storage | 95 | 75 | 21% | Simplify directory structure |
| Periodic Logging | 98 | 50 | 49% | Reduce complexity |
| Error Handling | 52 | 45 | 13% | Keep most |
| Cleanup | 44 | 30 | 32% | Keep essentials |
| Main/Node Setup | 87 | 60 | 31% | Simplify config |
| Utilities | 86 | 30 | 65% | Remove options logic |
| **Total** | **867** | **~447** | **48%** | **420 lines saved** |

### Estimated Implementation: ~450 lines (vs 867 original)

---

## 1. Code Structure Breakdown

### File Organization (Lines 1-867)

```
Lines 1-46:   Imports and warnings suppression
Lines 49-64:  Configuration class definition
Lines 66-128: Strategy __init__ and setup
Lines 129-172: Spot data initialization
Lines 173-194: on_start lifecycle
Lines 195-316: Instrument discovery & validation
Lines 318-336: Order book initialization
Lines 337-393: Subscription management
Lines 394-448: Data collection callbacks
Lines 449-495: Data storage methods
Lines 496-567: Periodic logging and saving
Lines 568-659: Parquet persistence logic
Lines 660-713: Cleanup and lifecycle
Lines 714-778: Utility methods
Lines 780-867: Main function and node setup
```

### Class Hierarchy

```python
BybitOptionsDataCollectorConfig(StrategyConfig, frozen=True)
    └── Configuration dataclass (lines 49-64)
        - spot_instrument_id: InstrumentId (required)
        - underlying_asset: str = "BTC"
        - options_depth: int = 25
        - spot_depth: int = 50
        - batch_size: int = 1000
        - data_dir: str = "data"
        - log_interval: float = 60.0
        - verbose_logging: bool = True
        - save_logs: bool = True
        - log_level: str = "INFO"

BybitOptionsDataCollector(Strategy)
    └── Main strategy class (lines 66-778)
        ├── __init__(config)
        ├── Lifecycle hooks:
        │   ├── on_start()
        │   ├── on_stop()
        ├── Data callbacks:
        │   ├── on_quote_tick(tick)
        │   ├── on_order_book_deltas(deltas)
        ├── Private methods:
        │   ├── _discover_options()
        │   ├── _validate_instruments()
        │   ├── _initialize_order_books()
        │   ├── _subscribe_to_data_streams()
        │   ├── _store_quote_tick(tick, key)
        │   ├── _store_order_book_delta(deltas, key)
        │   ├── _check_and_log_data()
        │   ├── _log_and_save_data()
        │   ├── _save_all_data_to_parquet()
        │   ├── _append_to_parquet_file(data, filepath, type, key)
        │   └── _reset_counters()
        └── Utility methods:
            ├── get_log_filepath()
            └── rotate_log_file()
```

### Data Structure Map

```python
# Primary Data Buffers (lines 94-96)
self.quote_ticks_data: dict[str, list[dict]] = {}
    # Key: instrument_id as string
    # Value: list of quote dictionaries
    # Example: {"BTCUSDT-SPOT.BYBIT": [{"timestamp": ..., "bid_price": ...}, ...]}

self.order_book_deltas_data: dict[str, list[dict]] = {}
    # Key: instrument_id as string
    # Value: list of delta dictionaries

# File Path Registry (lines 98-99)
self.quote_ticks_files: dict[str, str] = {}
    # Maps instrument_id → parquet file path
    # Example: {"BTCUSDT-SPOT.BYBIT": "data/BTC/USDT/spot/BTCUSDT-SPOT_BYBIT_quote.parquet"}

self.order_book_deltas_files: dict[str, str] = {}
    # Maps instrument_id → orderbook parquet file path

# Order Books for BBO Tracking (lines 102)
self.books: dict[str, OrderBook] = {}
    # Maintains live order book state per instrument

# Counters and Monitoring (lines 105-117)
self.quote_count: int = 0               # Total options quotes
self.delta_count: int = 0               # Total deltas
self.spot_quote_count: int = 0          # Spot quotes only
self.last_log_time: float = 0.0         # Last logging timestamp
self.last_spot_price: Decimal | None    # Latest mid price
self.last_data_time: float              # For connection monitoring
self.connection_warnings: int = 0       # Warning counter

# Per-instrument counters (lines 116-117)
self.instrument_quote_counts: dict[str, int] = {}
self.instrument_delta_counts: dict[str, int] = {}

# Discovered instruments (line 120)
self.discovered_options: list[InstrumentId] = []
```

---

## 2. Subscription Management Patterns

### Instrument Discovery (lines 195-230) - **CAN SKIP FOR SINGLE SYMBOL**

```python
def _discover_options(self) -> None:
    """Discover all available options for the underlying asset."""
    # Get all instruments from cache (already loaded by InstrumentProvider)
    all_instruments = self.cache.instruments()
    
    # Filter for options with matching underlying
    options = [
        instrument
        for instrument in all_instruments
        if (
            str(instrument.symbol).startswith(self.underlying_asset)
            and instrument.instrument_class == InstrumentClass.OPTION
        )
    ]
    
    # Group by expiry (for logging/organization)
    expiry_groups: dict[str, list[Instrument]] = {}
    for option in options:
        from nautilus_trader.core.datetime import unix_nanos_to_dt
        expiry_dt = unix_nanos_to_dt(option.expiration_ns)
        expiry = expiry_dt.strftime("%d%b%y").upper()
        if expiry not in expiry_groups:
            expiry_groups[expiry] = []
        expiry_groups[expiry].append(option)
    
    # Store for later use
    self.discovered_options = [option.id for option in options]
```

**Simplification for SPOT-only**:
```python
# Skip discovery entirely - hardcode instruments
def _initialize_instruments(self) -> None:
    """Initialize hardcoded instrument list."""
    # For SPOT only - just use config instrument IDs
    self.instrument_ids = [
        InstrumentId.from_str("BTCUSDT-SPOT.BYBIT"),
        # InstrumentId.from_str("ETHUSDT-SPOT.BYBIT"),  # If needed
    ]
    self.log.info(f"Initialized {len(self.instrument_ids)} instruments")
```

**Lines saved**: ~136 lines (entire discovery + grouping logic)

### Subscription Lifecycle (lines 337-378)

```python
def _subscribe_to_data_streams(self) -> None:
    """Subscribe to all data streams."""
    # Subscribe to quote ticks for all options FIRST
    for instrument_id in self.discovered_options:
        self.subscribe_quote_ticks(instrument_id=instrument_id)
    
    # Subscribe to spot quote ticks
    self.subscribe_quote_ticks(instrument_id=self.config.spot_instrument_id)
    
    # Subscribe to order book deltas for all options AFTER quotes
    for instrument_id in self.discovered_options:
        self.subscribe_order_book_deltas(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=self.config.options_depth,
        )
    
    # Subscribe to spot order book deltas
    self.subscribe_order_book_deltas(
        instrument_id=self.config.spot_instrument_id,
        book_type=BookType.L2_MBP,
        depth=self.config.spot_depth,
    )
```

**Simplification for 1-3 symbols**:
```python
def _subscribe_to_data_streams(self) -> None:
    """Subscribe to data streams for configured instruments."""
    for instrument_id in self.instrument_ids:
        # Subscribe to quotes
        self.subscribe_quote_ticks(instrument_id=instrument_id)
        
        # Subscribe to order book deltas
        self.subscribe_order_book_deltas(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=self.config.depth,  # Single depth param
        )
    
    self.log.info(f"Subscribed to {len(self.instrument_ids)} instruments")
```

**Lines saved**: ~40 lines (remove dual loop, spot/options separation)

### SPOT vs OPTIONS Differences - **REMOVE FOR SPOT-ONLY**

The original code separates:
- **Spot directory**: `data/BTC/USDT/spot/` (lines 83)
- **Options directory**: `data/BTC/USDT/options/` (line 84)
- **Spot depth**: 50 levels (line 57)
- **Options depth**: 25 or 100 levels (line 56)
- **Separate counters**: `spot_quote_count` vs `quote_count` (lines 105-107)

**Simplification**: Single directory structure, single depth parameter, unified counters.

---

## 3. Data Collection & Buffering

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ WebSocket Stream (Bybit)                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├──> on_quote_tick(tick: QuoteTick)
                 │    │
                 │    ├─> Validate (bid/ask > 0, bid < ask)
                 │    ├─> Extract to dict: {timestamp, bid_price, ask_price, ...}
                 │    ├─> Append to self.quote_ticks_data[instrument_key]
                 │    ├─> Update counters
                 │    └─> Check if time to log/save
                 │
                 └──> on_order_book_deltas(deltas: OrderBookDeltas)
                      │
                      ├─> Apply deltas to OrderBook
                      ├─> Extract BBO from updated book
                      ├─> Create dict: {timestamp, sequence, best_bid, best_ask, ...}
                      ├─> Append to self.order_book_deltas_data[instrument_key]
                      └─> Check if time to log/save
                           │
                           ▼
                 ┌─────────────────────────────┐
                 │ Periodic Check (every 60s)  │
                 └────────┬────────────────────┘
                          │
                          ├─> _log_and_save_data()
                          │   ├─> Log statistics
                          │   └─> _save_all_data_to_parquet()
                          │       │
                          │       ├─> For each instrument:
                          │       │   ├─> Convert list[dict] → DataFrame
                          │       │   ├─> Read existing parquet (if exists)
                          │       │   ├─> Concat old + new DataFrames
                          │       │   ├─> Write to parquet
                          │       │   └─> Clear buffer: data[key].clear()
                          │       │
                          │       └─> Log save summary
                          │
                          └─> _reset_counters()
                              └─> Reset interval counters to 0
```

### Quote Tick Collection (lines 418-447)

```python
def on_quote_tick(self, tick: QuoteTick) -> None:
    """Handle incoming quote ticks (both options and spot)."""
    # Update connection monitoring
    self.last_data_time = time.time()
    
    instrument_key = str(tick.instrument_id)
    
    # CRITICAL: Validate quote data
    if tick.bid_price.as_double() <= 0 or tick.ask_price.as_double() <= 0:
        self.log.warning(
            f"Invalid quote prices for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return
    
    if tick.bid_price.as_double() >= tick.ask_price.as_double():
        self.log.warning(
            f"Invalid quote spread for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return
    
    # Store quote tick data
    self._store_quote_tick(tick, instrument_key)
    
    # Update counters
    self._update_counters(tick, instrument_key)
    
    # Check if we need to log and save data
    self._check_and_log_data()
```

**Key Pattern**: Always validate before storing, update monitoring timestamps.

### Quote Tick Storage (lines 467-482)

```python
def _store_quote_tick(self, tick: QuoteTick, instrument_key: str) -> None:
    """Store quote tick data."""
    quote_data = {
        "timestamp": pd.Timestamp.now(),  # Local collection time
        "instrument_id": str(tick.instrument_id),
        "bid_price": tick.bid_price.as_double(),
        "ask_price": tick.ask_price.as_double(),
        "bid_size": tick.bid_size.as_double(),
        "ask_size": tick.ask_size.as_double(),
        "ts_event": tick.ts_event,  # Exchange timestamp (nanoseconds)
        "ts_init": tick.ts_init,    # Nautilus initialization time (nanoseconds)
    }
    
    self.quote_ticks_data[instrument_key].append(quote_data)
```

**Critical Fields**:
- `timestamp`: Local collection time (for debugging)
- `ts_event`: Exchange timestamp (PRIMARY for analysis)
- `ts_init`: Nautilus reception time (for latency measurement)

### Order Book Delta Collection (lines 394-416)

```python
def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
    """Handle incoming order book deltas."""
    # Update connection monitoring
    self.last_data_time = time.time()
    
    instrument_key = str(deltas.instrument_id)
    
    if instrument_key not in self.books:
        self.log.error(f"No order book initialized for {instrument_key}")
        return
    
    # Apply deltas to maintain the order book state
    self.books[instrument_key].apply_deltas(deltas)
    self.delta_count += 1
    self.instrument_delta_counts[instrument_key] += 1
    
    # Store delta data (extracts BBO from updated book)
    self._store_order_book_delta(deltas, instrument_key)
    
    # Check if we need to log and save data
    self._check_and_log_data()
```

### Order Book Delta Storage (lines 449-465)

```python
def _store_order_book_delta(self, deltas: OrderBookDeltas, instrument_key: str) -> None:
    """Store order book delta data."""
    book = self.books[instrument_key]
    delta_data = {
        "timestamp": pd.Timestamp.now(),
        "instrument_id": str(deltas.instrument_id),
        "sequence": deltas.sequence,  # For ordering/gap detection
        "delta_count": len(deltas.deltas),  # Number of changes in this update
        "best_bid": book.best_bid_price().as_double() if book.best_bid_price() else None,
        "best_ask": book.best_ask_price().as_double() if book.best_ask_price() else None,
        "bid_size": book.best_bid_size().as_double() if book.best_bid_size() else None,
        "ask_size": book.best_ask_size().as_double() if book.best_ask_size() else None,
    }
    
    self.order_book_deltas_data[instrument_key].append(delta_data)
```

**Key Pattern**: Store BBO snapshot after applying deltas, not the deltas themselves.

### Memory Management

**Buffering Strategy**:
1. Append to list (unbounded growth between flushes)
2. Periodic flush every `log_interval` seconds (default 60s)
3. Clear buffers after successful write: `data[key].clear()` (line 586)

**Risk**: If flush fails, data remains in buffer and will be retried next interval.

---

## 4. Parquet Persistence Patterns

### When to Write (lines 496-518)

```python
def _check_and_log_data(self) -> None:
    """Check if it's time to log and save data."""
    current_time = time.time()
    
    # Connection monitoring (check for timeout)
    if current_time - self.last_data_time > 120:  # 2 minutes no data
        self.connection_warnings += 1
        if self.connection_warnings <= 3:
            self.log.warning(
                f"No data received for {int(current_time - self.last_data_time)} seconds"
            )
        elif self.connection_warnings == 4:
            self.log.error("Multiple connection warnings - consider restarting")
    else:
        self.connection_warnings = 0  # Reset on successful data
    
    # Periodic flush trigger
    if current_time - self.last_log_time >= self.log_interval:
        self._log_and_save_data()
        self.last_log_time = current_time
```

**Triggers**:
1. **Periodic**: Every `log_interval` seconds (60s default)
2. **On shutdown**: `on_stop()` calls `_save_all_data_to_parquet()` (line 699)

**NOT triggered by**:
- Buffer size (batch_size param is unused in this version!)
- Data count
- Manual flush command

### File Organization (lines 81-88, 156-165)

```python
# Directory structure created in __init__
self.base_data_dir = os.path.join(self.data_dir, self.underlying_asset, "USDT")
self.spot_data_dir = os.path.join(self.base_data_dir, "spot")
self.options_data_dir = os.path.join(self.base_data_dir, "options")

os.makedirs(self.spot_data_dir, exist_ok=True)
os.makedirs(self.options_data_dir, exist_ok=True)

# File naming pattern
spot_name = spot_key.replace(".", "_")  # "BTCUSDT-SPOT.BYBIT" → "BTCUSDT-SPOT_BYBIT"
self.quote_ticks_files[spot_key] = os.path.join(
    self.spot_data_dir,
    f"{spot_name}_quote.parquet",
)
self.order_book_deltas_files[spot_key] = os.path.join(
    self.spot_data_dir,
    f"{spot_name}_orderbook.parquet",
)
```

**Resulting structure**:
```
data/
└── BTC/
    └── USDT/
        ├── spot/
        │   ├── BTCUSDT-SPOT_BYBIT_quote.parquet
        │   └── BTCUSDT-SPOT_BYBIT_orderbook.parquet
        └── options/
            ├── BTC-02AUG25-50000-C_OPTION_BYBIT_quote.parquet
            ├── BTC-02AUG25-50000-C_OPTION_BYBIT_orderbook.parquet
            └── ... (100+ files)
```

**Simplification for SPOT-only**:
```python
# Flat structure
self.data_dir = Path(config.data_dir) / "spot"
self.data_dir.mkdir(parents=True, exist_ok=True)

# Simpler naming
instrument_name = str(instrument_id).replace(".", "_").replace("-", "_")
quote_file = self.data_dir / f"{instrument_name}_quotes.parquet"
orderbook_file = self.data_dir / f"{instrument_name}_orderbook.parquet"
```

**Result**:
```
data/
└── spot/
    ├── BTCUSDT_SPOT_BYBIT_quotes.parquet
    ├── BTCUSDT_SPOT_BYBIT_orderbook.parquet
    ├── ETHUSDT_SPOT_BYBIT_quotes.parquet
    └── ETHUSDT_SPOT_BYBIT_orderbook.parquet
```

### Parquet Writing Logic (lines 568-659)

**Main orchestrator** (lines 568-603):
```python
def _save_all_data_to_parquet(self) -> None:
    """Save all accumulated data to parquet files."""
    total_quotes_saved = 0
    total_deltas_saved = 0
    instruments_with_quotes = 0
    instruments_with_deltas = 0
    
    # Save quote ticks for each instrument
    for instrument_key, data in self.quote_ticks_data.items():
        if data:  # Only write if buffer has data
            filepath = self.quote_ticks_files[instrument_key]
            self._append_to_parquet_file(data, filepath, "quote_ticks", instrument_key)
            total_quotes_saved += len(data)
            instruments_with_quotes += 1
            # CRITICAL: Clear buffer after save
            self.quote_ticks_data[instrument_key].clear()
    
    # Save order book deltas for each instrument
    for instrument_key, data in self.order_book_deltas_data.items():
        if data:
            filepath = self.order_book_deltas_files[instrument_key]
            self._append_to_parquet_file(data, filepath, "order_book_deltas", instrument_key)
            total_deltas_saved += len(data)
            instruments_with_deltas += 1
            # CRITICAL: Clear buffer after save
            self.order_book_deltas_data[instrument_key].clear()
    
    # Log summary
    if total_quotes_saved > 0 or total_deltas_saved > 0:
        self.log.info(
            f"Data saved: {total_quotes_saved} quotes ({instruments_with_quotes} instruments), "
            f"{total_deltas_saved} deltas ({instruments_with_deltas} instruments)"
        )
```

**Append logic** (lines 605-659):
```python
def _append_to_parquet_file(
    self,
    data: list[dict],
    filepath: str,
    data_type: str,
    instrument_key: str,
) -> None:
    """Append data to a parquet file."""
    if not data:
        return
    
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    # Convert new data to DataFrame
    df = pd.DataFrame(data)
    
    try:
        if df.empty:
            return
        
        # If file exists, read and concat
        if Path(filepath).exists():
            try:
                existing_df = pd.read_parquet(filepath)
                if existing_df.empty:
                    combined_df = df
                else:
                    # CRITICAL: Align columns (handle schema evolution)
                    all_columns = sorted(set(existing_df.columns) | set(df.columns))
                    for col in all_columns:
                        if col not in existing_df:
                            existing_df[col] = pd.NA
                        if col not in df:
                            df[col] = pd.NA
                    
                    # Concat old + new
                    combined_df = pd.concat(
                        [existing_df[all_columns], df[all_columns]],
                        ignore_index=True,
                    )
            except Exception as e:
                self.log.error(f"Failed to read existing parquet: {e}")
                combined_df = df  # Fallback: overwrite with new data
        else:
            combined_df = df
        
        # Write to file
        combined_df.to_parquet(filepath, index=False)
        
        self.log.debug(f"Saved {len(df)} {data_type} records to {filepath}")
        
    except Exception as e:
        self.log.error(f"Error saving {data_type} to {filepath}: {e}")
```

**Key Features**:
1. **Append mode**: Reads existing file, concats with new data
2. **Schema evolution**: Handles new columns with `pd.NA`
3. **Error recovery**: Falls back to overwrite on read failure
4. **No indexing**: `index=False` for space efficiency

**Potential Issues**:
- **Growing file size**: Each append reads entire file → slow for large files
- **No compression**: Could add `compression='snappy'` or `'gzip'`
- **No partitioning**: Could partition by date/hour for large datasets

**Recommended Enhancement for Phase 3**:
```python
# Add compression and partitioning
combined_df.to_parquet(
    filepath,
    index=False,
    compression='snappy',  # Fast compression
    # engine='pyarrow',  # Default, but explicit
)

# Or partition by hour for large datasets
hour_dir = filepath.parent / f"hour={pd.Timestamp.now().strftime('%Y%m%d_%H')}"
hour_dir.mkdir(exist_ok=True)
hourly_file = hour_dir / filepath.name
```

---

## 5. Error Handling & Monitoring

### Exception Handling in Callbacks (lines 427-438)

```python
def on_quote_tick(self, tick: QuoteTick) -> None:
    """Handle incoming quote ticks."""
    # Update monitoring first (even if validation fails)
    self.last_data_time = time.time()
    
    instrument_key = str(tick.instrument_id)
    
    # Validate quote data - return early on invalid data
    if tick.bid_price.as_double() <= 0 or tick.ask_price.as_double() <= 0:
        self.log.warning(
            f"Invalid quote prices for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return  # Skip processing but don't crash
    
    if tick.bid_price.as_double() >= tick.ask_price.as_double():
        self.log.warning(
            f"Invalid quote spread for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return
    
    # Continue processing...
```

**Pattern**: Validate → warn → return early (don't crash, don't store invalid data)

### Connection Health Monitoring (lines 502-513)

```python
# In _check_and_log_data()
current_time = time.time()

# Check for data timeout (no data for 2 minutes)
if current_time - self.last_data_time > 120:  # 2 minutes
    self.connection_warnings += 1
    if self.connection_warnings <= 3:  # Only warn first 3 times
        self.log.warning(
            f"No data received for {int(current_time - self.last_data_time)} seconds"
        )
    elif self.connection_warnings == 4:
        self.log.error("Multiple connection warnings - consider restarting")
else:
    # Reset warnings if we're getting data
    self.connection_warnings = 0
```

**Pattern**: 
- Track `last_data_time` in every callback
- Warn if no data for 2 minutes
- Limit warning spam (max 3 warnings)
- Auto-reset on recovery

### Data Validation Checks (lines 427-438, 403-404)

**Quote validation**:
```python
# Prices must be positive
if tick.bid_price.as_double() <= 0 or tick.ask_price.as_double() <= 0:
    self.log.warning(f"Invalid quote prices: bid={tick.bid_price}, ask={tick.ask_price}")
    return

# Bid must be < Ask (no crossed market)
if tick.bid_price.as_double() >= tick.ask_price.as_double():
    self.log.warning(f"Invalid quote spread: bid={tick.bid_price}, ask={tick.ask_price}")
    return
```

**Order book validation**:
```python
# Ensure order book exists before applying deltas
if instrument_key not in self.books:
    self.log.error(f"No order book initialized for {instrument_key}")
    return
```

**Parquet write validation** (lines 624-658):
```python
try:
    if df.empty:
        return  # Skip empty DataFrames
    
    # Try to read existing file
    if Path(filepath).exists():
        try:
            existing_df = pd.read_parquet(filepath)
            # ... concat logic ...
        except Exception as e:
            self.log.error(f"Failed to read existing parquet: {e}")
            combined_df = df  # Fallback to new data only
    
    # Write to file
    combined_df.to_parquet(filepath, index=False)
    
except Exception as e:
    self.log.error(f"Error saving {data_type} to {filepath}: {e}")
    # Note: Data remains in buffer (not cleared on error)
```

### Logging Patterns

**Logging levels used**:
- `self.log.debug()`: Per-file save confirmation (line 655)
- `self.log.info()`: Startup, subscriptions, periodic stats (lines 168-171, 367-377, 524-563)
- `self.log.warning()`: Invalid data, connection issues (lines 429, 435, 507)
- `self.log.error()`: Missing instruments, persistent failures (lines 276, 404, 510, 647, 658)

**Structured logging example** (lines 552-560):
```python
self.log.info(f"=== {self.log_interval} SECOND UPDATE ===")
self.log.info(f"Active instruments: {active_options}/{len(self.discovered_options)} options, 1/1 spot")
self.log.info(f"Monitoring {len(expiry_groups)} maturities: {', '.join(sorted(expiry_groups.keys()))}")
self.log.info(f"Data received: {total_quotes} quotes, {total_deltas} deltas")
self.log.info(f"  Options: {options_quote_total} quotes, {options_delta_total} deltas")
self.log.info(f"  Spot: {spot_quote_count} quotes, {spot_delta_count} deltas")
```

**Pattern**: Hierarchical structure (=== header, indented details)

### Graceful Degradation

**On invalid data**: Skip and continue (don't crash)
**On missing instrument**: Log error but don't stop other instruments
**On file write error**: Log error but data stays in buffer for retry
**On connection timeout**: Warn but keep running (assumes reconnection)

**Missing**: No explicit reconnection logic (relies on Nautilus adapter to handle)

---

## 6. Configuration Management

### Config Class Structure (lines 49-64)

```python
class BybitOptionsDataCollectorConfig(StrategyConfig, frozen=True):
    """Configuration for the Bybit Options Data Collector Strategy."""
    
    # Required parameters
    spot_instrument_id: InstrumentId  # No default - must be provided
    
    # Optional parameters with defaults
    underlying_asset: str = "BTC"
    options_depth: int = 25  # Options support 25 or 100 levels
    spot_depth: int = 50     # Spot supports 1, 50, or 200 levels
    batch_size: int = 1000   # UNUSED in current implementation
    data_dir: str = "data"
    log_interval: float = 60.0  # Seconds between log/save
    verbose_logging: bool = True
    save_logs: bool = True
    log_level: str = "INFO"
```

**Inheritance**: `StrategyConfig` (from Nautilus) + `frozen=True` (immutable dataclass)

**Validation**: None explicit - relies on type annotations

### Config Usage in Strategy (lines 72-79)

```python
def __init__(self, config: BybitOptionsDataCollectorConfig) -> None:
    super().__init__(config)  # Pass to Strategy base class
    
    # Extract config values to instance attributes
    self.underlying_asset = config.underlying_asset
    self.batch_size = config.batch_size
    self.data_dir = config.data_dir
    self.log_interval = config.log_interval
    
    # Use config values to set up paths
    self.base_data_dir = os.path.join(
        self.data_dir,
        self.underlying_asset,
        "USDT"
    )
```

**Pattern**: Extract config values to instance vars for convenience

### Simplified Config Template for Phase 3

```python
from pathlib import Path
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.config import StrategyConfig

class SpotDataCollectorConfig(StrategyConfig, frozen=True):
    """Configuration for SPOT data collector."""
    
    # Required
    instrument_ids: list[str]  # e.g., ["BTCUSDT-SPOT.BYBIT"]
    
    # Optional with defaults
    data_dir: str = "data/spot"
    depth: int = 50  # Order book depth (1, 50, or 200 for Bybit SPOT)
    log_interval: float = 60.0  # Flush interval in seconds
    session_duration: float | None = None  # None = run until stopped
    
    # Metadata
    run_id: str | None = None  # Auto-generated if None
    add_checksums: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        # Convert string IDs to InstrumentId objects
        object.__setattr__(
            self,
            'instrument_ids',
            [InstrumentId.from_str(id) for id in self.instrument_ids]
        )
        
        # Generate run_id if not provided
        if self.run_id is None:
            import uuid
            object.__setattr__(self, 'run_id', str(uuid.uuid4())[:8])
```

**Usage**:
```python
config = SpotDataCollectorConfig(
    instrument_ids=["BTCUSDT-SPOT.BYBIT", "ETHUSDT-SPOT.BYBIT"],
    data_dir="recordings",
    log_interval=30.0,
    session_duration=300.0,  # 5 minutes
)
```

---

## 7. Simplification Roadmap

### Detailed Component Analysis

#### A. Instrument Discovery (136 lines → 0 lines)

**Original complexity** (lines 195-316):
- Discovery: Query cache, filter by asset + class (36 lines)
- Grouping: Group by expiry, count per maturity (36 lines)
- Validation: Check each instrument exists, is active, is correct type (48 lines)
- Initialization: Create storage structures for each discovered instrument (58 lines)

**Simplification**:
```python
# Single line in config
instrument_ids = [InstrumentId.from_str("BTCUSDT-SPOT.BYBIT")]

# Minimal validation in on_start
for instrument_id in self.config.instrument_ids:
    if self.cache.instrument(instrument_id) is None:
        self.log.error(f"Instrument not found: {instrument_id}")
        self.stop()
        return
```

**Lines saved**: 136  
**Risk**: Low - hardcoded instruments are simpler and more predictable

#### B. Subscription Management (62 lines → 25 lines)

**Original** (lines 337-393):
- Separate loops for options vs spot (16 lines)
- Separate loops for quotes vs deltas (20 lines)
- Expiry grouping for logging (26 lines)

**Simplified**:
```python
def _subscribe_to_data_streams(self) -> None:
    for instrument_id in self.config.instrument_ids:
        self.subscribe_quote_ticks(instrument_id=instrument_id)
        self.subscribe_order_book_deltas(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=self.config.depth,
        )
    self.log.info(f"Subscribed to {len(self.config.instrument_ids)} instruments")
```

**Lines saved**: 37  
**Risk**: None - simplified code is clearer

#### C. Directory Structure (Complex → Flat)

**Original** (lines 81-88):
```
data/BTC/USDT/spot/...
data/BTC/USDT/options/...
```

**Simplified**:
```
data/spot/BTCUSDT_SPOT_BYBIT_quotes.parquet
data/spot/BTCUSDT_SPOT_BYBIT_orderbook.parquet
```

**Code reduction**: ~30 lines (remove spot/options separation logic)  
**Risk**: None - simpler is better for SPOT-only

#### D. Counters and Logging (98 lines → 50 lines)

**Original counters** (lines 105-117):
- `quote_count` (options only)
- `spot_quote_count` (spot only)
- `delta_count` (all)
- `instrument_quote_counts` (per-instrument)
- `instrument_delta_counts` (per-instrument)
- Separate logging for spot vs options

**Simplified**:
```python
# Single set of counters
self.total_quotes = 0
self.total_deltas = 0
self.instrument_stats: dict[str, dict] = {}  # Per-instrument combined stats

# Unified logging
self.log.info(f"Total: {self.total_quotes} quotes, {self.total_deltas} deltas")
for instrument_id, stats in self.instrument_stats.items():
    self.log.info(f"  {instrument_id}: {stats['quotes']} quotes, {stats['deltas']} deltas")
```

**Lines saved**: 48  
**Risk**: None - simpler tracking

#### E. Options-Specific Logic (86 lines → 0 lines)

**Remove entirely**:
- `_discover_options()` (36 lines)
- `_get_expiry_groups()` (14 lines)
- `_initialize_options_data_storage()` (36 lines)
- Options vs spot separation logic throughout

**Lines saved**: 86  
**Risk**: None - not needed for SPOT

#### F. File Logging Management (65 lines → 10 lines)

**Original** (lines 129-143, 714-778):
- Custom file handler setup (15 lines)
- Log rotation method (65 lines)

**Simplified** (use Nautilus built-in):
```python
# In TradingNodeConfig
logging=LoggingConfig(
    log_level="INFO",
    log_directory="data/logs",
    log_file_name="spot_collector",
)
```

**Lines saved**: 55  
**Risk**: None - built-in logging is sufficient

### Overall Reduction Summary

| Component | Original | Simplified | Saved | % Reduction |
|-----------|----------|------------|-------|-------------|
| Imports | 27 | 20 | 7 | 26% |
| Config | 15 | 12 | 3 | 20% |
| Init (basic) | 56 | 40 | 16 | 29% |
| Init (discovery) | 136 | 0 | 136 | 100% |
| Subscription | 62 | 25 | 37 | 60% |
| Data callbacks | 64 | 60 | 4 | 6% |
| Storage methods | 33 | 30 | 3 | 9% |
| Parquet logic | 95 | 75 | 20 | 21% |
| Logging/stats | 98 | 50 | 48 | 49% |
| Error handling | 52 | 45 | 7 | 13% |
| Cleanup | 44 | 30 | 14 | 32% |
| Main/setup | 87 | 60 | 27 | 31% |
| Utilities | 86 | 0 | 86 | 100% |
| **TOTAL** | **855** | **447** | **408** | **48%** |

### Risk Assessment per Simplification

| Simplification | Risk Level | Mitigation |
|----------------|------------|------------|
| Remove instrument discovery | LOW | Hardcode + validate on startup |
| Single directory structure | NONE | Simpler is better |
| Unified counters | NONE | Easier to understand |
| Remove options logic | NONE | Not needed for SPOT |
| Use built-in logging | LOW | Nautilus logging is well-tested |
| Single depth parameter | NONE | Fewer config params to manage |
| Remove expiry grouping | NONE | Not applicable to SPOT |

**Overall Risk**: LOW - Most simplifications remove unnecessary complexity without losing functionality.

---

## 8. Extract Reusable Components

### Copy Directly (with attribution)

#### A. Quote Tick Storage (lines 467-482)
```python
# ATTRIBUTION: Adapted from nautilus_trader/examples/live/bybit/bybit_options_data_collector.py:467-482
def _store_quote_tick(self, tick: QuoteTick, instrument_key: str) -> None:
    """Store quote tick data."""
    quote_data = {
        "timestamp": pd.Timestamp.now(),
        "instrument_id": str(tick.instrument_id),
        "bid_price": tick.bid_price.as_double(),
        "ask_price": tick.ask_price.as_double(),
        "bid_size": tick.bid_size.as_double(),
        "ask_size": tick.ask_size.as_double(),
        "ts_event": tick.ts_event,
        "ts_init": tick.ts_init,
    }
    self.quote_ticks_data[instrument_key].append(quote_data)
```

#### B. Order Book Delta Storage (lines 449-465)
```python
# ATTRIBUTION: Adapted from nautilus_trader/examples/live/bybit/bybit_options_data_collector.py:449-465
def _store_order_book_delta(self, deltas: OrderBookDeltas, instrument_key: str) -> None:
    """Store order book delta data."""
    book = self.books[instrument_key]
    delta_data = {
        "timestamp": pd.Timestamp.now(),
        "instrument_id": str(deltas.instrument_id),
        "sequence": deltas.sequence,
        "delta_count": len(deltas.deltas),
        "best_bid": book.best_bid_price().as_double() if book.best_bid_price() else None,
        "best_ask": book.best_ask_price().as_double() if book.best_ask_price() else None,
        "bid_size": book.best_bid_size().as_double() if book.best_bid_size() else None,
        "ask_size": book.best_ask_size().as_double() if book.best_ask_size() else None,
    }
    self.order_book_deltas_data[instrument_key].append(delta_data)
```

#### C. Parquet Append Logic (lines 605-659)
```python
# ATTRIBUTION: Adapted from nautilus_trader/examples/live/bybit/bybit_options_data_collector.py:605-659
def _append_to_parquet_file(
    self,
    data: list[dict],
    filepath: str,
    data_type: str,
    instrument_key: str,
) -> None:
    """Append data to a parquet file."""
    if not data:
        return
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    
    try:
        if df.empty:
            return
        
        if Path(filepath).exists():
            try:
                existing_df = pd.read_parquet(filepath)
                if not existing_df.empty:
                    all_columns = sorted(set(existing_df.columns) | set(df.columns))
                    for col in all_columns:
                        if col not in existing_df:
                            existing_df[col] = pd.NA
                        if col not in df:
                            df[col] = pd.NA
                    combined_df = pd.concat(
                        [existing_df[all_columns], df[all_columns]],
                        ignore_index=True,
                    )
                else:
                    combined_df = df
            except Exception as e:
                self.log.error(f"Failed to read existing parquet: {e}")
                combined_df = df
        else:
            combined_df = df
        
        combined_df.to_parquet(filepath, index=False)
        self.log.debug(f"Saved {len(df)} {data_type} records to {filepath}")
        
    except Exception as e:
        self.log.error(f"Error saving {data_type} to {filepath}: {e}")
```

#### D. Connection Monitoring (lines 502-513)
```python
# ATTRIBUTION: Adapted from nautilus_trader/examples/live/bybit/bybit_options_data_collector.py:502-513
def _check_connection_health(self) -> None:
    """Monitor connection health."""
    current_time = time.time()
    
    if current_time - self.last_data_time > 120:  # 2 minutes
        self.connection_warnings += 1
        if self.connection_warnings <= 3:
            self.log.warning(
                f"No data received for {int(current_time - self.last_data_time)} seconds"
            )
        elif self.connection_warnings == 4:
            self.log.error("Multiple connection warnings - consider restarting")
    else:
        self.connection_warnings = 0
```

#### E. Quote Validation (lines 427-438)
```python
# ATTRIBUTION: Adapted from nautilus_trader/examples/live/bybit/bybit_options_data_collector.py:427-438
def _validate_quote(self, tick: QuoteTick, instrument_key: str) -> bool:
    """Validate quote tick data."""
    if tick.bid_price.as_double() <= 0 or tick.ask_price.as_double() <= 0:
        self.log.warning(
            f"Invalid quote prices for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return False
    
    if tick.bid_price.as_double() >= tick.ask_price.as_double():
        self.log.warning(
            f"Invalid quote spread for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return False
    
    return True
```

### Components to Simplify

#### F. Subscription (from lines 337-378)
```python
# SIMPLIFIED from lines 337-378
def _subscribe_to_data_streams(self) -> None:
    """Subscribe to data streams for configured instruments."""
    for instrument_id in self.config.instrument_ids:
        self.subscribe_quote_ticks(instrument_id=instrument_id)
        self.subscribe_order_book_deltas(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=self.config.depth,
        )
    self.log.info(f"Subscribed to {len(self.config.instrument_ids)} instruments")
```

#### G. Order Book Initialization (from lines 318-336)
```python
# SIMPLIFIED from lines 318-336
def _initialize_order_books(self) -> None:
    """Initialize order books for all instruments."""
    for instrument_id in self.config.instrument_ids:
        self.books[str(instrument_id)] = OrderBook(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
        )
```

### Components to Add (Not in Original)

#### H. Session Metadata
```python
def _create_session_metadata(self) -> dict:
    """Create session metadata for this recording."""
    return {
        "run_id": self.config.run_id,
        "start_time": pd.Timestamp.now().isoformat(),
        "instruments": [str(id) for id in self.config.instrument_ids],
        "depth": self.config.depth,
        "session_duration": self.config.session_duration,
    }

def _save_session_metadata(self) -> None:
    """Save session metadata to JSON."""
    metadata = {
        **self._session_metadata,
        "end_time": pd.Timestamp.now().isoformat(),
        "total_quotes": self.total_quotes,
        "total_deltas": self.total_deltas,
        "instrument_stats": self.instrument_stats,
    }
    
    metadata_file = self.data_dir / f"session_{self.config.run_id}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
```

#### I. SHA256 Checksums
```python
import hashlib

def _compute_file_checksum(self, filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def _save_checksums(self) -> None:
    """Save checksums for all data files."""
    checksums = {}
    for filepath in self.data_dir.glob("*.parquet"):
        checksums[filepath.name] = self._compute_file_checksum(filepath)
    
    checksum_file = self.data_dir / f"checksums_{self.config.run_id}.json"
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)
```

#### J. Session Duration Control
```python
def _check_session_duration(self) -> None:
    """Check if session duration has been reached."""
    if self.config.session_duration is None:
        return  # Run indefinitely
    
    elapsed = time.time() - self.start_time
    if elapsed >= self.config.session_duration:
        self.log.info(f"Session duration reached: {elapsed:.1f}s")
        self._save_all_data_to_parquet()
        self._save_session_metadata()
        if self.config.add_checksums:
            self._save_checksums()
        self.stop()
```

---

## 9. Phase 3 Implementation Guide

### Step-by-Step Build Sequence

#### Step 1: Configuration (Est. 30 lines)
**Build**: `SpotDataCollectorConfig` class
**Reference**: Section 6, lines 49-64
**Test**: Instantiate with various parameters
**Success**: Config validates and generates run_id

#### Step 2: Basic Strategy Structure (Est. 80 lines)
**Build**: 
- `SpotDataCollector(Strategy)` class
- `__init__()` with data structures
- `on_start()` stub
- `on_stop()` stub

**Reference**: Lines 66-128, 173-194, 669-713
**Test**: Strategy can be instantiated and added to node
**Success**: Strategy starts and stops cleanly

#### Step 3: Subscription (Est. 40 lines)
**Build**:
- `_validate_instruments()`
- `_initialize_order_books()`
- `_subscribe_to_data_streams()`

**Reference**: Section 2, lines 269-393
**Test**: Subscribe to BTCUSDT-SPOT.BYBIT in testnet
**Success**: Receives quote ticks and order book deltas

#### Step 4: Data Collection (Est. 100 lines)
**Build**:
- `on_quote_tick()` with validation
- `on_order_book_deltas()`
- `_store_quote_tick()`
- `_store_order_book_delta()`

**Reference**: Section 3, lines 394-495
**Code**: Copy from Section 8A, 8B, 8E
**Test**: Log received data to console
**Success**: Data structures populate with valid ticks

#### Step 5: Parquet Persistence (Est. 100 lines)
**Build**:
- `_save_all_data_to_parquet()`
- `_append_to_parquet_file()`
- Periodic flush logic

**Reference**: Section 4, lines 496-659
**Code**: Copy from Section 8C
**Test**: Run for 2 minutes, verify parquet files created
**Success**: Files exist, readable, contain expected data

#### Step 6: Error Handling (Est. 50 lines)
**Build**:
- Connection monitoring
- Data validation
- Error recovery

**Reference**: Section 5, lines 427-513
**Code**: Copy from Section 8D, 8E
**Test**: Inject invalid ticks, simulate connection loss
**Success**: Graceful degradation, appropriate warnings

#### Step 7: Session Management (Est. 60 lines)
**Build**:
- Session metadata creation
- Duration control
- Checksums

**Reference**: Section 8H, 8I, 8J
**Test**: Run fixed-duration session (5 minutes)
**Success**: Auto-stops, creates metadata + checksums

#### Step 8: Node Setup (Est. 60 lines)
**Build**:
- `main()` function
- TradingNodeConfig
- CLI argument parsing

**Reference**: Lines 780-867
**Test**: Run from command line
**Success**: Can specify symbols, duration, data dir via CLI

#### Step 9: Testing & Validation (Est. 30 lines)
**Build**:
- Unit tests for core methods
- Integration test (full 5-min session)

**Test**: Comprehensive test coverage
**Success**: All tests pass, data quality verified

#### Step 10: Documentation (Est. 20 lines)
**Build**:
- README with usage examples
- Inline docstrings

**Success**: Clear, complete documentation

### Total Estimated Lines: ~570 lines (including tests & docs)

---

## 10. Code Snippets Library

### Ready-to-Use Snippets

#### Snippet 1: Config Template
**Purpose**: Configuration class for SPOT collector  
**Source**: Adapted from lines 49-64  
**Usage**: Modify parameters as needed  

```python
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.config import StrategyConfig

class SpotDataCollectorConfig(StrategyConfig, frozen=True):
    """Configuration for SPOT data collector.
    
    Attributes:
        instrument_ids: List of instrument ID strings to collect data for
        data_dir: Base directory for data storage
        depth: Order book depth (1, 50, or 200 for Bybit SPOT)
        log_interval: Seconds between periodic logging and data flushing
        session_duration: Optional fixed session duration in seconds (None = run until stopped)
        run_id: Unique identifier for this session (auto-generated if None)
        add_checksums: Whether to generate SHA256 checksums for data files
    """
    
    instrument_ids: list[str]
    data_dir: str = "data/spot"
    depth: int = 50
    log_interval: float = 60.0
    session_duration: float | None = None
    run_id: str | None = None
    add_checksums: bool = True
```

#### Snippet 2: Strategy Initialization
**Purpose**: Initialize data structures and directories  
**Source**: Adapted from lines 72-128  
**Usage**: In `__init__()` method  

```python
def __init__(self, config: SpotDataCollectorConfig) -> None:
    super().__init__(config)
    
    # Extract config
    self.data_dir = Path(config.data_dir)
    self.log_interval = config.log_interval
    
    # Create data directory
    self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # Data buffers (dict[instrument_key, list[data_dict]])
    self.quote_ticks_data: dict[str, list[dict]] = {}
    self.order_book_deltas_data: dict[str, list[dict]] = {}
    
    # File paths (dict[instrument_key, filepath])
    self.quote_files: dict[str, Path] = {}
    self.orderbook_files: dict[str, Path] = {}
    
    # Order books (dict[instrument_key, OrderBook])
    self.books: dict[str, OrderBook] = {}
    
    # Initialize storage for each instrument
    for instrument_id in config.instrument_ids:
        key = str(instrument_id)
        self.quote_ticks_data[key] = []
        self.order_book_deltas_data[key] = []
        
        # Create file paths
        name = key.replace(".", "_").replace("-", "_")
        self.quote_files[key] = self.data_dir / f"{name}_quotes.parquet"
        self.orderbook_files[key] = self.data_dir / f"{name}_orderbook.parquet"
    
    # Monitoring
    self.last_data_time = time.time()
    self.connection_warnings = 0
    self.start_time = time.time()
    
    self.log.info(f"Initialized data collector for {len(config.instrument_ids)} instruments")
    self.log.info(f"Data directory: {self.data_dir}")
```

#### Snippet 3: Quote Tick Handler
**Purpose**: Collect and validate quote ticks  
**Source**: Lines 418-447, 467-482  
**Usage**: Copy as-is  

```python
def on_quote_tick(self, tick: QuoteTick) -> None:
    """Handle incoming quote ticks."""
    # Update connection monitoring
    self.last_data_time = time.time()
    
    instrument_key = str(tick.instrument_id)
    
    # Validate quote data
    if not self._validate_quote(tick, instrument_key):
        return
    
    # Store quote tick
    self._store_quote_tick(tick, instrument_key)
    
    # Check if time to flush
    self._check_and_flush()

def _validate_quote(self, tick: QuoteTick, instrument_key: str) -> bool:
    """Validate quote tick data."""
    if tick.bid_price.as_double() <= 0 or tick.ask_price.as_double() <= 0:
        self.log.warning(
            f"Invalid prices for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return False
    
    if tick.bid_price.as_double() >= tick.ask_price.as_double():
        self.log.warning(
            f"Invalid spread for {instrument_key}: "
            f"bid={tick.bid_price}, ask={tick.ask_price}"
        )
        return False
    
    return True

def _store_quote_tick(self, tick: QuoteTick, instrument_key: str) -> None:
    """Store quote tick data."""
    quote_data = {
        "timestamp": pd.Timestamp.now(),
        "instrument_id": str(tick.instrument_id),
        "bid_price": tick.bid_price.as_double(),
        "ask_price": tick.ask_price.as_double(),
        "bid_size": tick.bid_size.as_double(),
        "ask_size": tick.ask_size.as_double(),
        "ts_event": tick.ts_event,
        "ts_init": tick.ts_init,
    }
    self.quote_ticks_data[instrument_key].append(quote_data)
```

#### Snippet 4: Order Book Delta Handler
**Purpose**: Collect order book updates  
**Source**: Lines 394-416, 449-465  
**Usage**: Copy as-is  

```python
def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
    """Handle incoming order book deltas."""
    # Update connection monitoring
    self.last_data_time = time.time()
    
    instrument_key = str(deltas.instrument_id)
    
    # Ensure order book exists
    if instrument_key not in self.books:
        self.log.error(f"No order book for {instrument_key}")
        return
    
    # Apply deltas to maintain book state
    self.books[instrument_key].apply_deltas(deltas)
    
    # Store BBO snapshot
    self._store_order_book_delta(deltas, instrument_key)
    
    # Check if time to flush
    self._check_and_flush()

def _store_order_book_delta(self, deltas: OrderBookDeltas, instrument_key: str) -> None:
    """Store order book delta (BBO snapshot)."""
    book = self.books[instrument_key]
    delta_data = {
        "timestamp": pd.Timestamp.now(),
        "instrument_id": str(deltas.instrument_id),
        "sequence": deltas.sequence,
        "delta_count": len(deltas.deltas),
        "best_bid": book.best_bid_price().as_double() if book.best_bid_price() else None,
        "best_ask": book.best_ask_price().as_double() if book.best_ask_price() else None,
        "bid_size": book.best_bid_size().as_double() if book.best_bid_size() else None,
        "ask_size": book.best_ask_size().as_double() if book.best_ask_size() else None,
    }
    self.order_book_deltas_data[instrument_key].append(delta_data)
```

#### Snippet 5: Parquet Persistence
**Purpose**: Flush buffers to parquet files  
**Source**: Lines 568-659  
**Usage**: Copy with minor simplifications  

```python
def _flush_to_parquet(self) -> None:
    """Flush all buffers to parquet files."""
    total_quotes = 0
    total_deltas = 0
    
    # Flush quote ticks
    for instrument_key, data in self.quote_ticks_data.items():
        if data:
            filepath = self.quote_files[instrument_key]
            self._append_to_parquet(data, filepath, "quotes")
            total_quotes += len(data)
            self.quote_ticks_data[instrument_key].clear()
    
    # Flush order book deltas
    for instrument_key, data in self.order_book_deltas_data.items():
        if data:
            filepath = self.orderbook_files[instrument_key]
            self._append_to_parquet(data, filepath, "orderbook")
            total_deltas += len(data)
            self.order_book_deltas_data[instrument_key].clear()
    
    if total_quotes > 0 or total_deltas > 0:
        self.log.info(f"Flushed {total_quotes} quotes, {total_deltas} deltas")

def _append_to_parquet(self, data: list[dict], filepath: Path, data_type: str) -> None:
    """Append data to parquet file."""
    if not data:
        return
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    
    try:
        if df.empty:
            return
        
        # Read existing file if it exists
        if filepath.exists():
            try:
                existing_df = pd.read_parquet(filepath)
                if not existing_df.empty:
                    # Align columns (handle schema evolution)
                    all_columns = sorted(set(existing_df.columns) | set(df.columns))
                    for col in all_columns:
                        if col not in existing_df:
                            existing_df[col] = pd.NA
                        if col not in df:
                            df[col] = pd.NA
                    # Concat
                    combined_df = pd.concat(
                        [existing_df[all_columns], df[all_columns]],
                        ignore_index=True,
                    )
                else:
                    combined_df = df
            except Exception as e:
                self.log.error(f"Failed to read existing file: {e}")
                combined_df = df
        else:
            combined_df = df
        
        # Write to file
        combined_df.to_parquet(filepath, index=False, compression='snappy')
        self.log.debug(f"Saved {len(df)} {data_type} records to {filepath}")
        
    except Exception as e:
        self.log.error(f"Error saving {data_type}: {e}")
```

#### Snippet 6: Periodic Check & Flush
**Purpose**: Check connection health and trigger periodic flush  
**Source**: Lines 496-518  
**Usage**: Call in every callback  

```python
def _check_and_flush(self) -> None:
    """Check connection health and flush data if needed."""
    current_time = time.time()
    
    # Check connection health
    if current_time - self.last_data_time > 120:  # 2 minutes
        self.connection_warnings += 1
        if self.connection_warnings <= 3:
            self.log.warning(
                f"No data for {int(current_time - self.last_data_time)}s"
            )
        elif self.connection_warnings == 4:
            self.log.error("Persistent connection issues - consider restarting")
    else:
        self.connection_warnings = 0
    
    # Check if time to flush
    if current_time - self.last_flush_time >= self.log_interval:
        self._flush_to_parquet()
        self.last_flush_time = current_time
    
    # Check session duration
    if self.config.session_duration:
        elapsed = current_time - self.start_time
        if elapsed >= self.config.session_duration:
            self.log.info(f"Session duration reached: {elapsed:.1f}s")
            self.stop()
```

#### Snippet 7: Subscription Setup
**Purpose**: Subscribe to data streams  
**Source**: Lines 318-378 (simplified)  
**Usage**: Call in `on_start()`  

```python
def _setup_subscriptions(self) -> None:
    """Set up data subscriptions."""
    # Validate instruments
    for instrument_id in self.config.instrument_ids:
        instrument = self.cache.instrument(instrument_id)
        if instrument is None:
            self.log.error(f"Instrument not found: {instrument_id}")
            self.stop()
            return
        self.log.info(f"Found instrument: {instrument}")
    
    # Initialize order books
    for instrument_id in self.config.instrument_ids:
        self.books[str(instrument_id)] = OrderBook(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
        )
    
    # Subscribe to data streams
    for instrument_id in self.config.instrument_ids:
        self.subscribe_quote_ticks(instrument_id=instrument_id)
        self.subscribe_order_book_deltas(
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=self.config.depth,
        )
    
    self.log.info(f"Subscribed to {len(self.config.instrument_ids)} instruments")
```

#### Snippet 8: Session Metadata
**Purpose**: Track session metadata  
**Source**: New (not in original)  
**Usage**: Call in `on_start()` and `on_stop()`  

```python
import json

def _save_session_metadata(self) -> None:
    """Save session metadata."""
    metadata = {
        "run_id": self.config.run_id,
        "start_time": pd.Timestamp(self.start_time, unit='s').isoformat(),
        "end_time": pd.Timestamp.now().isoformat(),
        "instruments": [str(id) for id in self.config.instrument_ids],
        "depth": self.config.depth,
        "log_interval": self.log_interval,
        "session_duration": self.config.session_duration,
        "total_runtime": time.time() - self.start_time,
    }
    
    # Add per-instrument stats
    for key in self.quote_ticks_data.keys():
        # Count records in parquet files
        quote_file = self.quote_files[key]
        orderbook_file = self.orderbook_files[key]
        
        quote_count = 0
        delta_count = 0
        if quote_file.exists():
            quote_count = len(pd.read_parquet(quote_file))
        if orderbook_file.exists():
            delta_count = len(pd.read_parquet(orderbook_file))
        
        metadata[key] = {
            "quotes": quote_count,
            "deltas": delta_count,
        }
    
    # Save to JSON
    metadata_file = self.data_dir / f"session_{self.config.run_id}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    self.log.info(f"Session metadata saved to {metadata_file}")
```

#### Snippet 9: Checksums
**Purpose**: Generate SHA256 checksums for data files  
**Source**: New (not in original)  
**Usage**: Call in `on_stop()` if `add_checksums=True`  

```python
import hashlib

def _compute_checksums(self) -> None:
    """Compute and save SHA256 checksums for all data files."""
    checksums = {}
    
    for filepath in self.data_dir.glob("*.parquet"):
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        checksums[filepath.name] = sha256.hexdigest()
    
    # Save checksums
    checksum_file = self.data_dir / f"checksums_{self.config.run_id}.json"
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    self.log.info(f"Checksums saved to {checksum_file}")
```

#### Snippet 10: Main Function
**Purpose**: Set up and run the trading node  
**Source**: Lines 780-867 (simplified)  
**Usage**: Entry point  

```python
import os
from nautilus_trader.adapters.bybit import BYBIT, BybitDataClientConfig, BybitProductType
from nautilus_trader.config import InstrumentProviderConfig, LoggingConfig, TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import TraderId

def main():
    """Run the SPOT data collector."""
    # Configuration
    instruments = ["BTCUSDT-SPOT.BYBIT"]
    
    # Trading node config
    config_node = TradingNodeConfig(
        trader_id=TraderId("SPOT-COLLECTOR-001"),
        logging=LoggingConfig(
            log_level="INFO",
            log_directory="data/logs",
            log_file_name="spot_collector",
        ),
        data_clients={
            BYBIT: BybitDataClientConfig(
                api_key=os.getenv("BYBIT_API_KEY"),
                api_secret=os.getenv("BYBIT_API_SECRET"),
                instrument_provider=InstrumentProviderConfig(
                    load_all=False,
                    filters={"symbols": ["BTCUSDT"]},
                ),
                product_types=[BybitProductType.SPOT],
                testnet=False,
            ),
        },
        timeout_connection=30.0,
    )
    
    # Create node
    node = TradingNode(config=config_node)
    
    # Create strategy
    strategy_config = SpotDataCollectorConfig(
        instrument_ids=instruments,
        data_dir="data/spot",
        depth=50,
        log_interval=60.0,
        session_duration=300.0,  # 5 minutes
    )
    strategy = SpotDataCollector(config=strategy_config)
    
    # Add strategy to node
    node.trader.add_strategy(strategy)
    
    # Register data client factory
    from nautilus_trader.adapters.bybit import BybitLiveDataClientFactory
    node.add_data_client_factory(BYBIT, BybitLiveDataClientFactory)
    
    # Build and run
    node.build()
    
    try:
        print("Starting SPOT Data Collector")
        print(f"Instruments: {instruments}")
        print("Press Ctrl+C to stop...")
        node.run()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        node.dispose()

if __name__ == "__main__":
    main()
```

---

## Summary for Agent 4

### Key Findings

1. **Architecture**: Single Strategy class, NOT using ParquetDataCatalog
2. **Data Flow**: WebSocket → callbacks → dict buffers → periodic flush → parquet
3. **Buffering**: In-memory list[dict] buffers, flushed every 60s
4. **Persistence**: pandas DataFrame → `to_parquet()` with append logic
5. **Simplification**: 867 → ~447 lines (48% reduction possible)

### Critical Patterns Extracted

- Quote/delta storage methods (ready to copy)
- Parquet append logic (handles schema evolution)
- Connection monitoring (2-minute timeout detection)
- Data validation (price checks, spread checks)
- Periodic flush triggers (time-based, not buffer-size)

### Recommended Next Steps for Phase 3

1. **Start with**: Config + basic strategy structure (Step 1-2)
2. **Core functionality**: Subscription + data collection (Step 3-4)
3. **Persistence**: Parquet writing (Step 5)
4. **Robustness**: Error handling + monitoring (Step 6)
5. **Enhancements**: Session metadata + checksums (Step 7)
6. **Integration**: Node setup + CLI (Step 8)
7. **Validation**: Testing (Step 9-10)

### Risk Assessment

**LOW RISK**: Most simplifications remove unnecessary complexity (options logic, discovery, dual directories)

**KEEP**: Core data collection, validation, persistence, error handling patterns

**ADD**: Session metadata, checksums, duration control (not in original)

---

**Document Complete**: Ready for Phase 3 implementation.

