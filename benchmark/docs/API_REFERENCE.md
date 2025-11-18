# Native Data Recorder API Reference

Complete API documentation for the Nautilus Trader Native Data Recorder framework.

**Last Updated:** November 9, 2025
**Location:** `benchmark/nautilus_trader/native_recorder/`

---

## Table of Contents

1. [Overview](#overview)
2. [Strategy API](#strategy-api)
3. [Configuration API](#configuration-api)
4. [Persistence API](#persistence-api)
5. [Data Models](#data-models)
6. [Exceptions & Error Handling](#exceptions--error-handling)
7. [Type Hints Reference](#type-hints-reference)
8. [Complete Examples](#complete-examples)
9. [Best Practices](#best-practices)

---

## Overview

The Native Data Recorder is a Nautilus Trader-based system for capturing live market data from Bybit and persisting it to Parquet files. The API is organized into three core modules:

### Module Structure

```
native_recorder/
├── strategy.py       # NativeDataRecorderStrategy, NativeDataRecorderConfig
├── config.py         # RecorderConfigBuilder, configuration helpers
├── persistence.py    # RecordingReader, validation, analysis utilities
└── __init__.py       # Public API exports
```

### Architecture Characteristics

- **85% Native Nautilus Components**: Uses Strategy base class, BybitDataClient, data models (TradeTick, QuoteTick, OrderBookDelta), TradingNode
- **Custom Enhancements**: Adds pandas buffering, direct Parquet writes, session metadata, SHA256 checksums
- **Production-Ready**: Proven patterns extracted from `bybit_options_data_collector.py`

### Key Design Patterns

1. **Strategy-Based Recording**: Leverages Nautilus Strategy lifecycle for clean startup/shutdown
2. **Buffered Persistence**: In-memory buffering with periodic Parquet flushes (configurable intervals)
3. **Session Tracking**: Automatic session metadata and checksums for data integrity
4. **Connection Health Monitoring**: Periodic checks for data flow with configurable timeouts

---

## Strategy API

### NativeDataRecorderConfig

Configuration dataclass for the recording strategy.

#### Class Definition

```python
class NativeDataRecorderConfig(StrategyConfig, frozen=True):
    """Configuration for NativeDataRecorderStrategy."""
```

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `instrument_ids` | `list[str]` | Required | Instrument IDs to record (e.g., `["SOLUSDT-SPOT.BYBIT"]`) |
| `output_dir` | `str` | `"data/recordings"` | Directory path for saving Parquet files |
| `flush_interval_seconds` | `int` | `60` | How often to flush buffered data to disk (seconds) |
| `record_quotes` | `bool` | `True` | Whether to record QuoteTick data |
| `record_orderbook` | `bool` | `True` | Whether to record OrderBookDelta data |
| `orderbook_depth` | `int` | `50` | Order book depth (if recording deltas) |
| `connection_timeout_seconds` | `int` | `120` | Warning threshold for no data received (seconds) |
| `run_duration_seconds` | `int \| None` | `None` | Auto-stop after N seconds (None = run forever) |

#### Usage Examples

**Basic Configuration**

```python
from native_recorder.strategy import NativeDataRecorderConfig

config = NativeDataRecorderConfig(
    instrument_ids=["SOLUSDT-SPOT.BYBIT"],
    output_dir="./data/recordings",
)
```

**Advanced Configuration**

```python
config = NativeDataRecorderConfig(
    instrument_ids=["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
    output_dir="/mnt/data/market_data",
    flush_interval_seconds=30,  # Flush every 30 seconds
    record_quotes=True,
    record_orderbook=True,
    orderbook_depth=100,  # Deep book
    connection_timeout_seconds=180,  # Warn after 3 minutes
    run_duration_seconds=3600,  # 1 hour session
)
```

### NativeDataRecorderStrategy

Main strategy class for data recording using native Nautilus components.

#### Class Definition

```python
class NativeDataRecorderStrategy(Strategy):
    """Native data recording strategy using Nautilus components."""

    def __init__(self, config: NativeDataRecorderConfig):
        """Initialize the recorder strategy."""
```

#### Constructor Parameters

- **config** (`NativeDataRecorderConfig`): Strategy configuration
  - Validates that at least one instrument ID is specified
  - Raises `ValueError` if configuration is invalid

#### Instance Attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `quote_ticks_data` | `dict[str, list[dict]]` | Buffer for quote tick data |
| `order_book_deltas_data` | `dict[str, list[dict]]` | Buffer for order book deltas |
| `quote_count` | `int` | Running count of quote ticks received |
| `delta_count` | `int` | Running count of order book deltas received |
| `last_data_time` | `float` | Unix timestamp of last data received |
| `session_start_time` | `float` | Session start timestamp |
| `run_id` | `str` | Unique session identifier (YYYYMMDD-HHMMSS) |
| `output_path` | `Path` | Base output directory for this session |
| `order_books` | `dict[InstrumentId, OrderBook]` | Maintained order books (if enabled) |

#### Lifecycle Methods

#### `on_start()`

Called when strategy is initialized. Handles all subscriptions and timers.

**Signature:**
```python
def on_start(self) -> None:
    """Subscribe to market data on strategy start."""
```

**Behavior:**
- Creates session directory with unique run ID
- Parses instrument IDs from config
- Subscribes to QuoteTicks (if `record_quotes=True`)
- Subscribes to OrderBookDeltas (if `record_orderbook=True`)
- Initializes managed OrderBook instances
- Schedules periodic flush timer (interval: `flush_interval_seconds`)
- Schedules connection health check timer (30 second interval)
- Schedules auto-stop timer (if `run_duration_seconds` specified)

**Side Effects:**
- Creates output directory structure
- Logs subscription confirmations
- Begins periodic timers

**Example:**
```python
# Strategy automatically calls on_start() during TradingNode initialization
# No manual invocation needed
strategy = NativeDataRecorderStrategy(config)
# on_start() called automatically by the framework
```

#### `on_quote_tick(tick: QuoteTick)`

Handles incoming quote tick data.

**Signature:**
```python
def on_quote_tick(self, tick: QuoteTick) -> None:
    """Handle incoming quote tick."""
```

**Parameters:**
- **tick** (`QuoteTick`): Quote tick from market data feed
  - Contains: `instrument_id`, `bid_price`, `ask_price`, `bid_size`, `ask_size`, `ts_event`, `ts_init`

**Behavior:**
- Validates quote data (prices > 0, no crossed spreads)
- Stores valid quotes in `quote_ticks_data` buffer
- Updates `quote_count` and `last_data_time`
- Logs warnings for invalid data

**Example:**
```python
# Called automatically by Nautilus framework
# Internal data structure after processing:
# {
#     "SOLUSDT-SPOT.BYBIT": [
#         {
#             "timestamp": pd.Timestamp(...),
#             "bid_price": 0.2345,
#             "ask_price": 0.2346,
#             "bid_size": 1000.5,
#             "ask_size": 2000.3,
#         },
#         ...
#     ]
# }
```

#### `on_order_book_deltas(deltas: OrderBookDeltas)`

Handles incoming order book delta data.

**Signature:**
```python
def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
    """Handle incoming order book deltas."""
```

**Parameters:**
- **deltas** (`OrderBookDeltas`): Order book delta message
  - Contains: `instrument_id`, `deltas` (list of individual delta objects), `ts_event`

**Behavior:**
- Iterates over each delta in the message
- Extracts delta action, side, price, size, order_id
- Stores deltas in `order_book_deltas_data` buffer
- Updates `delta_count` and `last_data_time`

**Example:**
```python
# Called automatically by Nautilus framework
# Internal data structure after processing:
# {
#     "SOLUSDT-SPOT.BYBIT": [
#         {
#             "timestamp": pd.Timestamp(...),
#             "action": "ADD",  # or "UPDATE", "DELETE"
#             "side": "BUY",     # or "SELL"
#             "price": 0.2345,
#             "size": 100.5,
#             "order_id": "12345",
#         },
#         ...
#     ]
# }
```

#### `on_stop()`

Called when strategy is stopped. Handles cleanup and final persistence.

**Signature:**
```python
def on_stop(self) -> None:
    """Cleanup and final data save on strategy stop."""
```

**Behavior:**
- Flushes all remaining buffered data to Parquet
- Generates session metadata JSON
- Generates SHA256 checksums for all files
- Logs final statistics (duration, counts, output path)

**Side Effects:**
- Writes final data files
- Creates `session_metadata.json` with summary
- Creates `checksums.json` with SHA256 hashes
- Clears in-memory buffers

**Example:**
```python
# Called automatically by framework when stopping
# No manual invocation needed
node.stop()  # Triggers on_stop()
```

#### Data Validation Methods

#### `_validate_quote(tick: QuoteTick) -> bool`

Validates quote tick data quality.

**Signature:**
```python
def _validate_quote(self, tick: QuoteTick) -> bool:
    """Validate quote tick data quality."""
```

**Parameters:**
- **tick** (`QuoteTick`): Quote to validate

**Returns:**
- `True` if quote passes all validations
- `False` if any validation fails

**Validation Checks:**
1. Bid price > 0
2. Ask price > 0
3. Bid price < Ask price (no crossed spreads)

**Example:**
```python
is_valid = strategy._validate_quote(tick)
if not is_valid:
    # Data logged as warning internally
    # Quote is discarded
    pass
```

#### Data Storage Methods

#### `_store_quote_tick(tick: QuoteTick)`

Stores a validated quote tick in memory buffer.

**Signature:**
```python
def _store_quote_tick(self, tick: QuoteTick) -> None:
    """Store quote tick in buffer."""
```

**Parameters:**
- **tick** (`QuoteTick`): Quote tick to store

**Storage Format:**
```python
{
    "timestamp": pd.Timestamp,  # UTC timestamp
    "bid_price": float,
    "ask_price": float,
    "bid_size": float,
    "ask_size": float,
}
```

**Example:**
```python
# Called internally by on_quote_tick()
# Organizes data by instrument for efficient batch writes
strategy._store_quote_tick(tick)
```

#### `_store_order_book_delta(delta, instrument_id: InstrumentId)`

Stores an order book delta in memory buffer.

**Signature:**
```python
def _store_order_book_delta(self, delta, instrument_id: InstrumentId) -> None:
    """Store order book delta in buffer."""
```

**Parameters:**
- **delta**: Individual delta from OrderBookDeltas.deltas
- **instrument_id** (`InstrumentId`): Instrument identifier

**Storage Format:**
```python
{
    "timestamp": pd.Timestamp,  # UTC timestamp
    "action": str,              # "ADD", "UPDATE", "DELETE"
    "side": str,                # "BUY", "SELL"
    "price": float,
    "size": float,
    "order_id": str,
}
```

#### Flush & Persistence Methods

#### `_periodic_flush()`

Timer callback for periodic data flushing.

**Signature:**
```python
def _periodic_flush(self) -> None:
    """Flush data buffers to parquet files periodically."""
```

**Behavior:**
- Called by `flush_data` timer every N seconds
- Invokes `_save_all_data()` to persist buffers

#### `_save_all_data()`

Saves all buffered data to Parquet files.

**Signature:**
```python
def _save_all_data(self) -> None:
    """Save all buffered data to parquet files."""
```

**Behavior:**
1. Creates type-specific directories (`quote_ticks/`, `order_book_deltas/`)
2. Creates instrument-specific subdirectories
3. Converts each buffer to pandas DataFrame
4. Appends to existing Parquet files (handles schema evolution)
5. Clears in-memory buffers
6. Logs completion statistics

**File Structure Created:**
```
{run_id}/
├── quote_ticks/
│   ├── SOLUSDT-SPOT.BYBIT/
│   │   └── quote_ticks.parquet
│   └── BTCUSDT-SPOT.BYBIT/
│       └── quote_ticks.parquet
├── order_book_deltas/
│   ├── SOLUSDT-SPOT.BYBIT/
│   │   └── order_book_deltas.parquet
│   └── BTCUSDT-SPOT.BYBIT/
│       └── order_book_deltas.parquet
├── session_metadata.json
└── checksums.json
```

**Example:**
```python
# Called automatically by periodic timer
# Or manually:
strategy._save_all_data()
```

#### `_save_to_parquet(data_type: str, instrument_key: str, data: list[dict])`

Saves data to Parquet with append logic.

**Signature:**
```python
def _save_to_parquet(
    self,
    data_type: str,
    instrument_key: str,
    data: list[dict]
) -> None:
    """Save data to parquet file with append logic."""
```

**Parameters:**
- **data_type** (`str`): Type of data (`"quote_ticks"` or `"order_book_deltas"`)
- **instrument_key** (`str`): Instrument ID (e.g., `"SOLUSDT-SPOT.BYBIT"`)
- **data** (`list[dict]`): Records to save

**Behavior:**
1. Creates directory structure if needed
2. Reads existing Parquet file (if present)
3. Aligns column schemas (handles evolution)
4. Concatenates existing + new data
5. Writes combined DataFrame to file
6. Falls back to new-only write if append fails

**Error Handling:**
- Catches read/append failures
- Logs error and saves new data only
- Preserves existing data on failure

**Example:**
```python
# Called internally by _save_all_data()
strategy._save_to_parquet(
    "quote_ticks",
    "SOLUSDT-SPOT.BYBIT",
    [{"timestamp": ..., "bid_price": ...}, ...]
)
```

#### Metadata Methods

#### `_save_session_metadata()`

Saves session summary to JSON file.

**Signature:**
```python
def _save_session_metadata(self) -> None:
    """Save session metadata to JSON."""
```

**Output Format:**
```json
{
    "run_id": "20251109-143022",
    "session_start": 1699547422.123,
    "session_end": 1699547482.456,
    "duration_seconds": 60.333,
    "instruments": ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
    "quote_count": 15234,
    "delta_count": 8901,
    "config": {
        "flush_interval_seconds": 60,
        "record_quotes": true,
        "record_orderbook": true,
        "orderbook_depth": 50
    }
}
```

#### `_generate_checksums()`

Generates SHA256 checksums for all Parquet files.

**Signature:**
```python
def _generate_checksums(self) -> None:
    """Generate SHA256 checksums for all parquet files."""
```

**Output Format:**
```json
{
    "quote_ticks/SOLUSDT-SPOT.BYBIT/quote_ticks.parquet": {
        "sha256": "a1b2c3d4...",
        "size_bytes": 1048576
    },
    "order_book_deltas/SOLUSDT-SPOT.BYBIT/order_book_deltas.parquet": {
        "sha256": "e5f6g7h8...",
        "size_bytes": 2097152
    }
}
```

**Purpose:**
- Verify data integrity
- Detect file corruption or tampering
- Track file sizes for performance analysis

#### Connection Health Methods

#### `_check_connection_health()`

Monitors connection and warns if no data received.

**Signature:**
```python
def _check_connection_health(self) -> None:
    """Monitor connection health and warn if no data received."""
```

**Behavior:**
- Checks time since last data received
- If exceeded `connection_timeout_seconds`: logs warning (limited to 3 warnings)
- On recovery: logs info message and resets warning counter
- Called every 30 seconds

**Example:**
```python
# Connection timeout = 120 seconds
# If no data for 120+ seconds: "⚠️ No data received for 125.3 seconds!"
# When data resumes: "✅ Connection recovered"
```

#### `_auto_stop()`

Auto-stop timer callback.

**Signature:**
```python
def _auto_stop(self) -> None:
    """Auto-stop the strategy after duration."""
```

**Behavior:**
- Called by `auto_stop` timer (if configured)
- Logs session completion message
- Calls `self.stop()` to trigger clean shutdown

---

## Configuration API

### RecorderConfigBuilder

Builder class for creating TradingNode configurations.

#### Class Definition

```python
class RecorderConfigBuilder:
    """Builder for TradingNode configuration."""

    def __init__(self, trader_id: str = "DATA-RECORDER-001"):
        """Initialize the builder."""
```

#### Constructor Parameters

- **trader_id** (`str`, default=`"DATA-RECORDER-001"`): Trader identifier
  - Converted to Nautilus `TraderId` internally

#### Fluent Builder Methods

All builder methods return `self` for method chaining.

#### `add_instrument(instrument_id: str) -> RecorderConfigBuilder`

Add a single instrument to record.

**Parameters:**
- **instrument_id** (`str`): Instrument ID (e.g., `"SOLUSDT-SPOT.BYBIT"`)

**Returns:**
- `self` for chaining

**Example:**
```python
builder = RecorderConfigBuilder()
builder.add_instrument("SOLUSDT-SPOT.BYBIT")
builder.add_instrument("BTCUSDT-SPOT.BYBIT")
```

#### `add_instruments(instrument_ids: list[str]) -> RecorderConfigBuilder`

Add multiple instruments to record.

**Parameters:**
- **instrument_ids** (`list[str]`): List of instrument IDs

**Returns:**
- `self` for chaining

**Example:**
```python
builder.add_instruments([
    "SOLUSDT-SPOT.BYBIT",
    "BTCUSDT-SPOT.BYBIT",
    "ETHUSDT-SPOT.BYBIT",
])
```

#### `set_output_dir(output_dir: str | Path) -> RecorderConfigBuilder`

Set output directory for Parquet files.

**Parameters:**
- **output_dir** (`str | Path`): Output directory path

**Returns:**
- `self` for chaining

**Example:**
```python
builder.set_output_dir("/mnt/data/recordings")
builder.set_output_dir(Path.home() / "data" / "recordings")
```

#### `set_flush_interval(seconds: int) -> RecorderConfigBuilder`

Set flush interval in seconds.

**Parameters:**
- **seconds** (`int`): Flush interval (must be > 0)

**Returns:**
- `self` for chaining

**Example:**
```python
builder.set_flush_interval(30)  # Flush every 30 seconds
builder.set_flush_interval(300)  # Flush every 5 minutes
```

#### `enable_orderbook(depth: int = 50) -> RecorderConfigBuilder`

Enable order book delta recording.

**Parameters:**
- **depth** (`int`, default=`50`): Order book depth

**Returns:**
- `self` for chaining

**Example:**
```python
builder.enable_orderbook()  # Default depth=50
builder.enable_orderbook(depth=100)  # Deeper book
```

#### `disable_quotes() -> RecorderConfigBuilder`

Disable quote tick recording.

**Returns:**
- `self` for chaining

**Example:**
```python
# Only record order book deltas, not quotes
builder.disable_quotes()
builder.enable_orderbook()
```

#### `set_duration(seconds: int) -> RecorderConfigBuilder`

Set session duration for auto-stop.

**Parameters:**
- **seconds** (`int`): Duration in seconds (must be > 0)

**Returns:**
- `self` for chaining

**Example:**
```python
builder.set_duration(3600)  # 1 hour
builder.set_duration(300)   # 5 minutes
```

#### `set_bybit_credentials(api_key: str, api_secret: str, testnet: bool = False) -> RecorderConfigBuilder`

Set Bybit API credentials.

**Parameters:**
- **api_key** (`str`): Bybit API key
- **api_secret** (`str`): Bybit API secret
- **testnet** (`bool`, default=`False`): Use testnet

**Returns:**
- `self` for chaining

**Note:** Not required for public data (quotes and order book deltas)

**Example:**
```python
builder.set_bybit_credentials(
    api_key="your-api-key",
    api_secret="your-api-secret",
    testnet=False
)
```

#### `validate() -> None`

Validate configuration.

**Raises:**
- `ValueError`: If configuration is invalid

**Validation Checks:**
1. At least one instrument specified
2. All instrument IDs contain `.BYBIT` venue
3. Flush interval > 0
4. Order book depth > 0
5. Run duration > 0 or None

**Example:**
```python
try:
    builder.validate()
except ValueError as e:
    print(f"Invalid config: {e}")
```

#### `build() -> tuple[TradingNodeConfig, NativeDataRecorderConfig]`

Build and return configuration objects.

**Returns:**
- `tuple[TradingNodeConfig, NativeDataRecorderConfig]`: Ready for TradingNode

**Raises:**
- `ValueError`: If configuration is invalid (calls `validate()`)

**Example:**
```python
builder = RecorderConfigBuilder("RECORDER-001")
builder.add_instruments(["SOLUSDT-SPOT.BYBIT"])
builder.set_output_dir("./data")
builder.set_duration(600)

node_config, strategy_config = builder.build()

# Use with TradingNode
node = TradingNode.create(node_config)
node.add_strategy(NativeDataRecorderStrategy(strategy_config))
```

#### Fluent Chain Example

```python
builder = RecorderConfigBuilder("RECORDER-BTC-SOL")
node_config, strategy_config = (
    builder
    .add_instruments(["BTCUSDT-SPOT.BYBIT", "SOLUSDT-SPOT.BYBIT"])
    .set_output_dir("/data/market_data")
    .set_flush_interval(30)
    .enable_orderbook(depth=100)
    .set_duration(3600)
    .build()
)
```

### load_config_from_yaml()

Load configuration from YAML file.

**Signature:**
```python
def load_config_from_yaml(
    yaml_path: str | Path
) -> tuple[TradingNodeConfig, NativeDataRecorderConfig]:
    """Load configuration from YAML file."""
```

**Parameters:**
- **yaml_path** (`str | Path`): Path to YAML configuration file

**Returns:**
- `tuple[TradingNodeConfig, NativeDataRecorderConfig]`: Ready for TradingNode

**Raises:**
- `FileNotFoundError`: If YAML file doesn't exist
- `ValueError`: If configuration is invalid

**YAML Format:**
```yaml
trader_id: "RECORDER-001"

strategy:
  instruments:
    - "SOLUSDT-SPOT.BYBIT"
    - "BTCUSDT-SPOT.BYBIT"
  output_dir: "/data/recordings"
  flush_interval_seconds: 60
  record_quotes: true
  record_orderbook: true
  orderbook_depth: 50
  run_duration_seconds: 3600

bybit:
  api_key: "your-key"
  api_secret: "your-secret"
  testnet: false
```

**Example:**
```python
node_config, strategy_config = load_config_from_yaml(
    "config_templates/bybit_spot_recording.yaml"
)
```

### create_quick_config()

Quick configuration builder for common use cases.

**Signature:**
```python
def create_quick_config(
    instruments: list[str],
    output_dir: str = "data/recordings",
    duration_seconds: int | None = None,
    with_orderbook: bool = False,
) -> tuple[TradingNodeConfig, NativeDataRecorderConfig]:
    """Quick configuration builder for common use cases."""
```

**Parameters:**
- **instruments** (`list[str]`): Instrument IDs
- **output_dir** (`str`, default=`"data/recordings"`): Output directory
- **duration_seconds** (`int | None`, default=`None`): Auto-stop duration
- **with_orderbook** (`bool`, default=`False`): Record order book deltas

**Returns:**
- `tuple[TradingNodeConfig, NativeDataRecorderConfig]`: Ready for TradingNode

**Raises:**
- `ValueError`: If configuration is invalid

**Example:**
```python
# Quick 5-minute SOLUSDT recording
node_config, strategy_config = create_quick_config(
    instruments=["SOLUSDT-SPOT.BYBIT"],
    duration_seconds=300
)

# Multi-symbol with order book
node_config, strategy_config = create_quick_config(
    instruments=["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
    with_orderbook=True,
    duration_seconds=600
)
```

---

## Persistence API

### RecordingReader

Read and analyze recorded Parquet data.

#### Class Definition

```python
class RecordingReader:
    """Read and analyze recorded parquet data."""

    def __init__(self, recording_dir: str | Path):
        """Initialize reader with recording directory."""
```

#### Constructor Parameters

- **recording_dir** (`str | Path`): Path to recording directory
  - Must contain `quote_ticks/`, `order_book_deltas/`, `session_metadata.json`

**Raises:**
- `FileNotFoundError`: If directory doesn't exist

#### `read_quotes(instrument_key: str) -> pd.DataFrame`

Read quote ticks for an instrument.

**Parameters:**
- **instrument_key** (`str`): Instrument ID (e.g., `"SOLUSDT-SPOT.BYBIT"`)

**Returns:**
- `pd.DataFrame`: Columns: `timestamp` (UTC), `bid_price`, `ask_price`, `bid_size`, `ask_size`

**Raises:**
- `FileNotFoundError`: If quote data not found

**Example:**
```python
reader = RecordingReader("data/recordings/20251109-143022")
quotes_df = reader.read_quotes("SOLUSDT-SPOT.BYBIT")

print(quotes_df.head())
# Output:
#                    timestamp  bid_price  ask_price  bid_size  ask_size
# 0 2025-11-09 14:30:22.123456       0.2345      0.2346    1000.5    2000.3
# 1 2025-11-09 14:30:22.234567       0.2345      0.2346     900.2    2100.1
```

#### `read_deltas(instrument_key: str) -> pd.DataFrame`

Read order book deltas for an instrument.

**Parameters:**
- **instrument_key** (`str`): Instrument ID

**Returns:**
- `pd.DataFrame`: Columns: `timestamp` (UTC), `action`, `side`, `price`, `size`, `order_id`

**Raises:**
- `FileNotFoundError`: If delta data not found

**Example:**
```python
deltas_df = reader.read_deltas("SOLUSDT-SPOT.BYBIT")

print(deltas_df.head())
# Output:
#                    timestamp action  side  price    size order_id
# 0 2025-11-09 14:30:22.123456    ADD   BUY  0.2345  100.5    12345
# 1 2025-11-09 14:30:22.234567    ADD  SELL  0.2346   50.2    12346
```

#### `list_instruments() -> dict[str, list[str]]`

List all recorded instruments by data type.

**Returns:**
- `dict[str, list[str]]`: Maps data type to list of instruments

**Example:**
```python
instruments = reader.list_instruments()

# Output:
# {
#     "quote_ticks": ["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
#     "order_book_deltas": ["SOLUSDT-SPOT.BYBIT"]
# }
```

#### `get_metadata() -> dict[str, Any]`

Read session metadata.

**Returns:**
- `dict[str, Any]`: Session summary (run_id, timestamps, counts, config)

**Raises:**
- `FileNotFoundError`: If metadata not found

**Example:**
```python
metadata = reader.get_metadata()

print(metadata)
# Output:
# {
#     "run_id": "20251109-143022",
#     "session_start": 1699547422.123,
#     "session_end": 1699547482.456,
#     "duration_seconds": 60.333,
#     "instruments": ["SOLUSDT-SPOT.BYBIT"],
#     "quote_count": 15234,
#     "delta_count": 0,
#     "config": {...}
# }
```

#### `get_checksums() -> dict[str, dict[str, Any]]`

Read checksums file.

**Returns:**
- `dict[str, dict[str, Any]]`: Maps file path to `{"sha256": "...", "size_bytes": 12345}`

**Raises:**
- `FileNotFoundError`: If checksums not found

**Example:**
```python
checksums = reader.get_checksums()

for path, info in checksums.items():
    print(f"{path}: {info['sha256'][:8]}... ({info['size_bytes']} bytes)")
```

#### `get_statistics() -> dict[str, Any]`

Generate comprehensive statistics.

**Returns:**
- `dict[str, Any]`: Complete statistics including:
  - `recording_dir`: Directory path
  - `instruments`: List of recorded instruments
  - `session`: Session metadata
  - `data_types`: Stats per instrument and type
  - `total_parquet_size_mb`: Total size

**Example:**
```python
stats = reader.get_statistics()

print(f"Recording size: {stats['total_parquet_size_mb']:.2f} MB")
print(f"Quote count: {stats['data_types']['quote_ticks']['SOLUSDT-SPOT.BYBIT']['count']}")
print(f"Time range: {stats['data_types']['quote_ticks']['SOLUSDT-SPOT.BYBIT']['time_range']}")
```

### validate_recording()

Validate a recording directory.

**Signature:**
```python
def validate_recording(recording_dir: str | Path) -> dict[str, Any]:
    """Validate a recording directory."""
```

**Parameters:**
- **recording_dir** (`str | Path`): Path to recording directory

**Returns:**
- `dict[str, Any]`: Validation report with keys:
  - `valid` (`bool`): Overall validity
  - `issues` (`list[str]`): List of issues found
  - `checks` (`list[dict]`): Individual check results

**Validation Checks:**
1. Metadata file exists
2. Checksums file exists
3. All checksums match files
4. All data files are readable
5. Timestamps are monotonically increasing
6. No empty data files

**Example:**
```python
report = validate_recording("data/recordings/20251109-143022")

if report["valid"]:
    print("✅ Recording valid")
else:
    print(f"❌ Issues: {report['issues']}")
    for check in report["checks"]:
        if check["status"] == "fail":
            print(f"  - {check['check']}")
```

### generate_data_quality_report()

Generate comprehensive data quality report.

**Signature:**
```python
def generate_data_quality_report(
    recording_dir: str | Path,
    output_path: str | Path | None = None
) -> dict[str, Any]:
    """Generate comprehensive data quality report."""
```

**Parameters:**
- **recording_dir** (`str | Path`): Path to recording directory
- **output_path** (`str | Path | None`, default=`None`): Save report to JSON file

**Returns:**
- `dict[str, Any]`: Quality report including:
  - `validation`: Validation results
  - `statistics`: Recording statistics
  - `quality_score`: 0-100 score
  - `recommendations`: List of recommendations

**Example:**
```python
report = generate_data_quality_report(
    "data/recordings/20251109-143022",
    output_path="quality_report.json"
)

print(f"Quality Score: {report['quality_score']}/100")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

### load_recording()

Load and validate a recording directory.

**Signature:**
```python
def load_recording(recording_dir: str | Path) -> RecordingReader:
    """Load a recording directory."""
```

**Parameters:**
- **recording_dir** (`str | Path`): Path to recording directory

**Returns:**
- `RecordingReader`: Valid reader instance

**Raises:**
- `ValueError`: If recording is invalid

**Example:**
```python
try:
    reader = load_recording("data/recordings/20251109-143022")
    quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")
except ValueError as e:
    print(f"Cannot load recording: {e}")
```

### compare_recordings()

Compare two recordings.

**Signature:**
```python
def compare_recordings(
    dir1: str | Path,
    dir2: str | Path
) -> dict[str, Any]:
    """Compare two recordings."""
```

**Parameters:**
- **dir1** (`str | Path`): First recording directory
- **dir2** (`str | Path`): Second recording directory

**Returns:**
- `dict[str, Any]`: Comparison results including size and instruments

**Example:**
```python
comparison = compare_recordings(
    "data/recordings/hybrid-20251109",
    "data/recordings/native-20251109"
)

print(f"Hybrid: {comparison['size_comparison']['recording1_mb']:.2f} MB")
print(f"Native: {comparison['size_comparison']['recording2_mb']:.2f} MB")
```

---

## Data Models

### QuoteTick (Nautilus Native)

Quote tick data structure.

**Attributes:**
- `instrument_id` (`InstrumentId`): Trading pair
- `bid_price` (`Price`): Best bid price
- `ask_price` (`Price`): Best ask price
- `bid_size` (`Quantity`): Size at bid
- `ask_size` (`Quantity`): Size at ask
- `ts_event` (`int`): Event timestamp (nanoseconds)
- `ts_init` (`int`): Initialization timestamp (nanoseconds)

### OrderBookDelta (Nautilus Native)

Order book delta structure.

**Attributes:**
- `instrument_id` (`InstrumentId`): Trading pair
- `deltas` (`list[OrderBookDelta]`): Individual delta messages
- `ts_event` (`int`): Event timestamp (nanoseconds)

**Delta Contains:**
- `action` (`BookAction`): ADD, UPDATE, DELETE
- `order` (`OrderBookOrder`): Contains side, price, size, order_id

### OrderBook (Nautilus Native)

Maintained order book.

**Attributes:**
- `instrument_id` (`InstrumentId`): Trading pair
- `book_type` (`BookType`): L1, L2, L3
- Methods: `add_delta()`, `apply_delta()`, `reset()`

### Buffered Data Structure

Quote buffer (internal):
```python
{
    "SOLUSDT-SPOT.BYBIT": [
        {
            "timestamp": pd.Timestamp,
            "bid_price": float,
            "ask_price": float,
            "bid_size": float,
            "ask_size": float,
        },
        ...
    ]
}
```

Delta buffer (internal):
```python
{
    "SOLUSDT-SPOT.BYBIT": [
        {
            "timestamp": pd.Timestamp,
            "action": str,
            "side": str,
            "price": float,
            "size": float,
            "order_id": str,
        },
        ...
    ]
}
```

---

## Exceptions & Error Handling

### Configuration Exceptions

#### ValueError

Raised when configuration is invalid.

**Scenarios:**
- No instruments specified
- Invalid instrument ID format
- Flush interval <= 0
- Order book depth <= 0
- Run duration <= 0

**Example:**
```python
try:
    config = NativeDataRecorderConfig(instrument_ids=[])  # Empty
except ValueError as e:
    print(f"Config error: {e}")
```

### File & I/O Exceptions

#### FileNotFoundError

Raised when required files don't exist.

**Scenarios:**
- Recording directory not found
- Quote/delta files not found
- Metadata file missing
- Checksums file missing

**Example:**
```python
try:
    reader = RecordingReader("non/existent/path")
except FileNotFoundError as e:
    print(f"File error: {e}")
```

### Validation Exceptions

#### ValueError (from load_recording)

Raised when recording fails validation.

**Scenario:**
- Recording directory exists but validation fails

**Example:**
```python
try:
    reader = load_recording("corrupted/recording")
except ValueError as e:
    print(f"Invalid recording: {e}")
```

### Data Quality Logging

Non-fatal data quality issues are logged, not raised:

```python
# Invalid quote prices logged as WARNING
self.log.warning(f"Invalid quote prices: bid={tick.bid_price}, ask={tick.ask_price}")

# Crossed spread logged as WARNING
self.log.warning(f"Crossed spread: bid={tick.bid_price} >= ask={tick.ask_price}")

# Append failures logged as ERROR, fallback to new data
self.log.error(f"Error appending to {filepath}: {e}")
self.log.warning(f"Saving new data only to {filepath}")
```

---

## Type Hints Reference

### Basic Types

```python
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# String types
instrument_id: str  # e.g., "SOLUSDT-SPOT.BYBIT"
trader_id: str      # e.g., "RECORDER-001"
run_id: str         # e.g., "20251109-143022"

# Numeric types
price: float        # Quote price
size: float         # Order size
count: int          # Data count
timestamp: float    # Unix seconds

# Collections
instruments: List[str]
data_dict: Dict[str, Any]
```

### Nautilus Types

```python
from nautilus_trader.config import StrategyConfig, TradingNodeConfig
from nautilus_trader.model.data import QuoteTick, OrderBookDeltas
from nautilus_trader.model.identifiers import InstrumentId, TraderId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orderbook import OrderBook
from nautilus_trader.trading.strategy import Strategy
```

### Pandas Types

```python
import pandas as pd

df: pd.DataFrame     # Tabular data
ts: pd.Timestamp    # Timestamp with timezone
```

### Return Type Patterns

```python
# Builder methods
def add_instrument(self, instrument_id: str) -> "RecorderConfigBuilder":
    ...

# Building
def build(self) -> tuple[TradingNodeConfig, NativeDataRecorderConfig]:
    ...

# Reading data
def read_quotes(self, instrument_key: str) -> pd.DataFrame:
    ...

# Validation
def validate_recording(recording_dir: str | Path) -> dict[str, Any]:
    ...
```

---

## Complete Examples

### Example 1: Record SOLUSDT for 5 Minutes

```python
from native_recorder.config import create_quick_config
from native_recorder.strategy import NativeDataRecorderStrategy
from nautilus_trader.trading.node import TradingNode

# Create configuration
node_config, strategy_config = create_quick_config(
    instruments=["SOLUSDT-SPOT.BYBIT"],
    output_dir="./market_data",
    duration_seconds=300
)

# Create trading node
node = TradingNode.create(
    config=node_config,
    name="RECORDER-SOL"
)

# Add strategy
strategy = NativeDataRecorderStrategy(strategy_config)
node.add_strategy(strategy)

# Run
node.run()

# Results in:
# ./market_data/20251109-143022/
# ├── quote_ticks/
# │   └── SOLUSDT-SPOT.BYBIT/
# │       └── quote_ticks.parquet
# ├── session_metadata.json
# └── checksums.json
```

### Example 2: Record Multiple Symbols with Order Book

```python
from native_recorder.config import RecorderConfigBuilder
from native_recorder.strategy import NativeDataRecorderStrategy
from nautilus_trader.trading.node import TradingNode

# Build configuration
builder = RecorderConfigBuilder("RECORDER-MULTI")
node_config, strategy_config = (
    builder
    .add_instruments(["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"])
    .set_output_dir("/data/market_data")
    .set_flush_interval(30)
    .enable_orderbook(depth=100)
    .set_duration(3600)  # 1 hour
    .build()
)

# Run
node = TradingNode.create(node_config, name="RECORDER-MULTI")
node.add_strategy(NativeDataRecorderStrategy(strategy_config))
node.run()
```

### Example 3: Load and Analyze Recording

```python
from native_recorder.persistence import (
    load_recording,
    validate_recording,
    generate_data_quality_report
)

# Validate
recording_dir = "data/recordings/20251109-143022"
validation = validate_recording(recording_dir)

if not validation["valid"]:
    print(f"Invalid recording: {validation['issues']}")
    exit(1)

# Load
reader = load_recording(recording_dir)

# Analyze
quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")
print(f"Loaded {len(quotes)} quote ticks")
print(f"Time range: {quotes['timestamp'].min()} to {quotes['timestamp'].max()}")

# Generate report
report = generate_data_quality_report(
    recording_dir,
    output_path="quality_report.json"
)
print(f"Quality Score: {report['quality_score']}/100")
```

### Example 4: Configuration from YAML

```yaml
# config.yaml
trader_id: "RECORDER-PROD"

strategy:
  instruments:
    - "SOLUSDT-SPOT.BYBIT"
    - "BTCUSDT-SPOT.BYBIT"
    - "ETHUSDT-SPOT.BYBIT"
  output_dir: "/mnt/data/market_data"
  flush_interval_seconds: 60
  record_quotes: true
  record_orderbook: true
  orderbook_depth: 100
  run_duration_seconds: null  # Run forever

bybit:
  api_key: null
  api_secret: null
  testnet: false
```

```python
from native_recorder.config import load_config_from_yaml
from native_recorder.strategy import NativeDataRecorderStrategy
from nautilus_trader.trading.node import TradingNode

node_config, strategy_config = load_config_from_yaml("config.yaml")
node = TradingNode.create(node_config)
node.add_strategy(NativeDataRecorderStrategy(strategy_config))
node.run()
```

---

## Best Practices

### Configuration Best Practices

1. **Start Small**: Test with single instrument before multiple
   ```python
   # Good
   create_quick_config(["SOLUSDT-SPOT.BYBIT"], duration_seconds=300)

   # Less good for testing
   create_quick_config([... 10 instruments ...], duration_seconds=3600)
   ```

2. **Set Appropriate Flush Intervals**
   - Light load (few quotes/sec): 60 seconds OK
   - High load (1000s/sec): 10-30 seconds better
   ```python
   builder.set_flush_interval(30)  # More frequent for high volume
   ```

3. **Use Order Book Judiciously**
   - Order book recording is more compute-intensive
   - Only enable if needed for your analysis
   ```python
   # Only record quotes unless you need book
   if needs_orderbook:
       builder.enable_orderbook(depth=50)
   ```

4. **Set Reasonable Timeouts**
   - Exchange connections can be flaky
   - Allow 2-3 minute timeout for spotty connections
   ```python
   builder.connection_timeout = 180  # 3 minutes
   ```

### Data Storage Best Practices

1. **Monitor Disk Space**
   - Heavy recording can consume significant space
   - Quote recording: ~10-50 MB per hour per symbol
   - Order book recording: ~100-500 MB per hour per symbol

2. **Use Session Metadata**
   - Always check `session_metadata.json` before analysis
   - Verify `quote_count` and `delta_count` match expectations

3. **Validate Before Analyzing**
   ```python
   # Always validate first
   validation = validate_recording(recording_dir)
   if not validation["valid"]:
       print(f"Issues: {validation['issues']}")
       exit(1)
   ```

4. **Check Checksums**
   - Use for integrity verification
   - Compare checksums if transferring data
   ```python
   checksums = reader.get_checksums()
   for path, info in checksums.items():
       # Verify file hasn't been corrupted/modified
       pass
   ```

### Analysis Best Practices

1. **Use Statistics Method**
   ```python
   stats = reader.get_statistics()
   # Don't assume instruments exist - check stats first
   if "SOLUSDT-SPOT.BYBIT" not in stats["instruments"]["quote_ticks"]:
       print("No SOLUSDT quotes recorded")
   ```

2. **Handle Missing Data Gracefully**
   ```python
   try:
       quotes = reader.read_quotes("SYMBOL")
   except FileNotFoundError:
       print("Symbol not recorded")
       quotes = pd.DataFrame()
   ```

3. **Check Timestamp Ordering**
   ```python
   quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")
   if not quotes["timestamp"].is_monotonic_increasing:
       print("Warning: timestamps not monotonic")
   ```

### Error Handling Best Practices

1. **Catch Configuration Errors Early**
   ```python
   try:
       builder.validate()
   except ValueError as e:
       print(f"Fix config: {e}")
       exit(1)
   ```

2. **Handle Recording Load Errors**
   ```python
   try:
       reader = load_recording(recording_dir)
   except ValueError as e:
       # Show user the validation report
       validation = validate_recording(recording_dir)
       print(f"Issues: {validation['issues']}")
   ```

3. **Log Session Completions**
   ```python
   metadata = reader.get_metadata()
   print(f"Session {metadata['run_id']}:")
   print(f"  Duration: {metadata['duration_seconds']}s")
   print(f"  Quotes: {metadata['quote_count']}")
   print(f"  Deltas: {metadata['delta_count']}")
   ```

---

## Summary

The Native Data Recorder API provides:

- **Complete data capture**: Quotes, order book deltas, market microstructure
- **Native Nautilus integration**: Built on proven framework components
- **Flexible configuration**: Builder pattern, YAML support, quick configs
- **Data integrity**: Checksums, validation, quality reporting
- **Easy analysis**: Reader class, statistics, comparison utilities

For more information, see the main documentation in the parent directory.
