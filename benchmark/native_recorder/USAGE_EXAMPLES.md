# Configuration Management - Usage Examples

This document demonstrates how to use the configuration management system for the Nautilus Trader native data recorder.

## Method 1: Builder API (Programmatic)

### Basic Recording Session

```python
from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder

# Create builder
builder = RecorderConfigBuilder(trader_id="MY-RECORDER-001")

# Configure
builder.add_instrument("SOLUSDT-SPOT.BYBIT")
builder.set_output_dir("data/my_recordings")
builder.set_duration(300)  # 5 minutes

# Build configs
node_config, strategy_config = builder.build()

# Use with TradingNode
from nautilus_trader.trading.node import TradingNode

node = TradingNode(config=node_config)
# ... (rest of implementation)
```

### Multi-Symbol with Order Book

```python
from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder

builder = RecorderConfigBuilder()
builder.add_instruments([
    "SOLUSDT-SPOT.BYBIT",
    "BTCUSDT-SPOT.BYBIT",
    "ETHUSDT-SPOT.BYBIT"
])
builder.set_output_dir("data/multi_symbol")
builder.enable_orderbook(depth=100)  # Enable with 100 levels
builder.set_flush_interval(30)  # Write every 30 seconds
builder.set_duration(600)  # 10 minutes

node_config, strategy_config = builder.build()
```

### Fluent API Chaining

```python
from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder

node_config, strategy_config = (
    RecorderConfigBuilder("PRODUCTION-RECORDER")
    .add_instruments(["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"])
    .set_output_dir("/var/data/recordings")
    .enable_orderbook(depth=50)
    .set_flush_interval(60)
    .set_duration(1800)  # 30 minutes
    .build()
)
```

---

## Method 2: YAML Configuration Files

### Load from Template

```python
from benchmark.nautilus_trader.native_recorder.config import load_config_from_yaml

# Load single-symbol config
node_config, strategy_config = load_config_from_yaml(
    "benchmark/nautilus_trader/config_templates/bybit_spot_recording.yaml"
)

# Load multi-symbol config
node_config, strategy_config = load_config_from_yaml(
    "benchmark/nautilus_trader/config_templates/bybit_multi_recording.yaml"
)

# Load orderbook config
node_config, strategy_config = load_config_from_yaml(
    "benchmark/nautilus_trader/config_templates/bybit_spot_with_orderbook.yaml"
)
```

### Custom YAML File

Create `my_config.yaml`:
```yaml
trader_id: "MY-RECORDER-001"

strategy:
  instruments:
    - "SOLUSDT-SPOT.BYBIT"
    - "AVAXUSDT-SPOT.BYBIT"
  output_dir: "data/custom_recordings"
  flush_interval_seconds: 45
  record_quotes: true
  record_orderbook: true
  orderbook_depth: 75
  run_duration_seconds: 900  # 15 minutes

bybit:
  api_key: null
  api_secret: null
  testnet: false
```

Load it:
```python
from benchmark.nautilus_trader.native_recorder.config import load_config_from_yaml

node_config, strategy_config = load_config_from_yaml("my_config.yaml")
```

---

## Method 3: Quick Config Helper

### Simplest Usage

```python
from benchmark.nautilus_trader.native_recorder.config import create_quick_config

# Record SOLUSDT for 5 minutes
node_config, strategy_config = create_quick_config(
    instruments=["SOLUSDT-SPOT.BYBIT"],
    duration_seconds=300
)
```

### Multiple Symbols

```python
from benchmark.nautilus_trader.native_recorder.config import create_quick_config

node_config, strategy_config = create_quick_config(
    instruments=["SOLUSDT-SPOT.BYBIT", "BTCUSDT-SPOT.BYBIT"],
    output_dir="data/multi",
    duration_seconds=600  # 10 minutes
)
```

### With Order Book

```python
from benchmark.nautilus_trader.native_recorder.config import create_quick_config

node_config, strategy_config = create_quick_config(
    instruments=["SOLUSDT-SPOT.BYBIT"],
    with_orderbook=True,
    duration_seconds=300
)
```

---

## Configuration Validation

All methods include automatic validation:

```python
from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder

builder = RecorderConfigBuilder()

# This will raise ValueError: Must specify at least one instrument
try:
    node_config, strategy_config = builder.build()
except ValueError as e:
    print(f"Validation error: {e}")

# This will raise ValueError: Invalid instrument ID
builder.add_instrument("INVALID")
try:
    node_config, strategy_config = builder.build()
except ValueError as e:
    print(f"Validation error: {e}")  # "must include .BYBIT venue"
```

---

## Complete Example: Recording Session

```python
from benchmark.nautilus_trader.native_recorder.config import create_quick_config
from nautilus_trader.trading.node import TradingNode
from benchmark.nautilus_trader.native_recorder.strategy import NativeDataRecorderStrategy
import asyncio

async def run_recording_session():
    # Create configuration
    node_config, strategy_config = create_quick_config(
        instruments=["SOLUSDT-SPOT.BYBIT"],
        output_dir="data/recordings",
        duration_seconds=300,  # 5 minutes
        with_orderbook=False
    )

    # Initialize trading node
    node = TradingNode(config=node_config)

    # Create and add strategy
    strategy = NativeDataRecorderStrategy(config=strategy_config)
    node.trader.add_strategy(strategy)

    # Build and run
    await node.build()
    await node.run()

    print("Recording session started!")
    print(f"Recording {strategy_config.instrument_ids}")
    print(f"Output: {strategy_config.output_dir}")
    print(f"Duration: {strategy_config.run_duration_seconds}s")

# Run
asyncio.run(run_recording_session())
```

---

## Choosing the Right Method

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Builder API** | Complex configs, programmatic use | Full control, type hints, validation | More verbose |
| **YAML Files** | Repeatable configs, production | Easy to edit, version control | Requires file management |
| **Quick Config** | Quick tests, one-liners | Simplest API | Limited customization |

---

## Advanced: Bybit Credentials

For authenticated data (if needed):

```python
from benchmark.nautilus_trader.native_recorder.config import RecorderConfigBuilder

builder = RecorderConfigBuilder()
builder.add_instrument("SOLUSDT-SPOT.BYBIT")
builder.set_bybit_credentials(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    testnet=False  # Use live data
)

node_config, strategy_config = builder.build()
```

Or in YAML:
```yaml
bybit:
  api_key: "YOUR_API_KEY"
  api_secret: "YOUR_API_SECRET"
  testnet: false
```

**Note**: Credentials are NOT required for public market data recording (quotes, orderbook).

---

## Tips

1. **Start Simple**: Use `create_quick_config()` for initial testing
2. **Move to YAML**: Use templates for production/repeatable configs
3. **Use Builder**: For dynamic configuration based on runtime conditions
4. **Validate Early**: All methods validate on `build()` - catch errors early
5. **Check Output**: Verify parquet files are being created in `output_dir`
6. **Monitor Duration**: `run_duration_seconds=null` means run forever (manual stop)

---

## See Also

- `config.py` - Configuration implementation
- `strategy.py` - Strategy implementation
- `../config_templates/README.md` - YAML template documentation
