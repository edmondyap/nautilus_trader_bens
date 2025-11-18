# Nautilus Trader Data Recorder - Configuration Templates

This directory contains YAML configuration templates for the Nautilus Trader native data recorder.

## Available Templates

### 1. `bybit_spot_recording.yaml`
**Use Case**: Single-symbol SPOT market data recording (quotes only)

**Features**:
- Records quote ticks (bid/ask) for one instrument
- No order book data
- Configurable session duration
- Default 60-second flush interval

**Example Usage**:
```python
from benchmark.nautilus_trader.native_recorder.config import load_config_from_yaml

node_config, strategy_config = load_config_from_yaml(
    "benchmark/nautilus_trader/config_templates/bybit_spot_recording.yaml"
)
```

---

### 2. `bybit_multi_recording.yaml`
**Use Case**: Multi-symbol SPOT market data recording

**Features**:
- Records quote ticks for multiple instruments simultaneously
- Default: SOL, BTC, ETH (USDT pairs)
- 10-minute recording session
- Efficient parallel data collection

**Example Usage**:
```python
from benchmark.nautilus_trader.native_recorder.config import load_config_from_yaml

node_config, strategy_config = load_config_from_yaml(
    "benchmark/nautilus_trader/config_templates/bybit_multi_recording.yaml"
)
```

---

### 3. `bybit_spot_with_orderbook.yaml`
**Use Case**: SPOT recording with L2 order book deltas

**Features**:
- Records both quote ticks AND order book deltas
- 50-level order book depth
- Higher data volume
- Useful for market microstructure analysis

**Example Usage**:
```python
from benchmark.nautilus_trader.native_recorder.config import load_config_from_yaml

node_config, strategy_config = load_config_from_yaml(
    "benchmark/nautilus_trader/config_templates/bybit_spot_with_orderbook.yaml"
)
```

---

## Configuration Parameters

### Strategy Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `instruments` | list[str] | Required | Instrument IDs (must include `.BYBIT` venue) |
| `output_dir` | str | `"data/recordings"` | Output directory for parquet files |
| `flush_interval_seconds` | int | `60` | Write to parquet every N seconds |
| `record_quotes` | bool | `true` | Record quote ticks (bid/ask) |
| `record_orderbook` | bool | `false` | Record order book deltas |
| `orderbook_depth` | int | `50` | Order book depth levels |
| `connection_timeout_seconds` | int | `120` | Connection monitoring timeout |
| `run_duration_seconds` | int\|null | `null` | Auto-stop after N seconds (null = run forever) |

### Bybit Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str\|null | `null` | Bybit API key (not required for public data) |
| `api_secret` | str\|null | `null` | Bybit API secret |
| `testnet` | bool | `false` | Use testnet vs live data |

---

## Customizing Templates

### Example: Change Instrument

```yaml
strategy:
  instruments:
    - "BTCUSDT-SPOT.BYBIT"  # Changed from SOLUSDT
```

### Example: Add More Instruments

```yaml
strategy:
  instruments:
    - "SOLUSDT-SPOT.BYBIT"
    - "BTCUSDT-SPOT.BYBIT"
    - "ETHUSDT-SPOT.BYBIT"
    - "BNBUSDT-SPOT.BYBIT"  # Added
```

### Example: Enable Order Book

```yaml
strategy:
  record_orderbook: true
  orderbook_depth: 100  # Increased depth
```

### Example: Set Recording Duration

```yaml
strategy:
  run_duration_seconds: 1800  # 30 minutes
```

---

## Instrument ID Format

All instrument IDs must follow this format:
```
{BASE}{QUOTE}-{PRODUCT_TYPE}.{VENUE}
```

Examples:
- `SOLUSDT-SPOT.BYBIT`
- `BTCUSDT-SPOT.BYBIT`
- `ETHUSDT-SPOT.BYBIT`

---

## Output Files

Recorded data will be saved as parquet files in the `output_dir`:

```
data/recordings/
├── quote_ticks/
│   ├── SOLUSDT-SPOT.BYBIT_2025-11-09.parquet
│   └── BTCUSDT-SPOT.BYBIT_2025-11-09.parquet
└── order_book_deltas/
    └── SOLUSDT-SPOT.BYBIT_2025-11-09.parquet
```

---

## See Also

- `../native_recorder/config.py` - Python configuration builder
- `../native_recorder/strategy.py` - Strategy implementation
- `../../NAUTILUS_API_RESEARCH.md` - API research documentation
