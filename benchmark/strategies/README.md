# TestSingleMakerStrategy for Nautilus Trader

A simple market-making strategy implementation for the Nautilus Trader platform as part of the Quant Trading Platform Benchmark.

## Overview

TestSingleMakerStrategy is a basic market-making strategy that maintains one bid and one ask order around a moving average of the mid-price. The strategy updates orders when they are filled or when the market moves beyond a tolerance threshold.

### Key Features

- **Moving Average Mid-Price**: Uses a configurable rolling window (default: 5 minutes) to calculate the average mid-price
- **Dynamic Order Placement**: Places limit orders at MA ± spread (in basis points)
- **Smart Order Updates**: Cancels and replaces orders when mid-price moves more than a tolerance threshold
- **Position Management**: Respects configurable long/short position limits
- **Budget Control**: Tracks available capital and respects budget constraints

## Strategy Logic

### Core Workflow

1. **Market Data Update** (on orderbook delta or trade):
   - Calculate mid-price: `(best_bid + best_ask) / 2`
   - Update mid-price history (rolling window)
   - Calculate moving average of mid-prices
   - Check if existing orders need updating (mid moved >= tolerance)
   - Place new orders if needed

2. **Order Fill Event**:
   - Update position and cash balance
   - Clear filled order reference
   - Immediately place replacement order on same side (if within limits)

3. **Order Placement**:
   - **Bid Price**: `MA_mid * (1 - spread_bps / 10000)`
   - **Ask Price**: `MA_mid * (1 + spread_bps / 10000)`
   - Prices are rounded to exchange tick size

4. **Position Limits**:
   - Don't place bid if `position + order_size > max_long_position`
   - Don't place ask if `position - order_size < -max_short_position`
   - Don't place bid if insufficient cash balance

## Files

- `test_single_maker_strategy.py` - Strategy implementation
- `test_single_maker_config.yaml` - Configuration file with default parameters
- `run_backtest.py` - Backtest runner script
- `README.md` - This file

## Configuration Parameters

All parameters are configurable via `test_single_maker_config.yaml`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `instrument_id` | str | SOLUSDT-LINEAR.BYBIT | Instrument to trade |
| `spread_bps` | float | 10.0 | Spread around mid-price in basis points (10 bps = 0.1%) |
| `ma_window_minutes` | int | 5 | Moving average window size in minutes |
| `price_tolerance_bps` | float | 15.0 | Re-quote threshold in basis points |
| `order_size_base` | float | 1.0 | Order size in base currency (e.g., SOL) |
| `max_long_position` | float | 5.0 | Maximum long position in base currency |
| `max_short_position` | float | 5.0 | Maximum short position magnitude |
| `max_budget_quote` | float | 5000.0 | Maximum capital in quote currency (e.g., USDT) |
| `book_type` | str | L2_MBP | Order book type (L2_MBP recommended) |

## Installation & Setup

### Prerequisites

1. **Nautilus Trader installed**:
   ```bash
   # From the nautilus_trader directory
   pip install -e .
   ```

2. **Recorded market data**:
   ```bash
   # Record 6 hours of SOLUSDT data
   cd /Users/benjaminang/Desktop/Trading\ Engines
   python benchmark/nautilus_trader/native_recorder/run_6hr_recording.py
   ```

   This will create data in: `benchmark/data/nautilus_trader/6hr/`

### Directory Structure

```
benchmark/
├── data/
│   └── nautilus_trader/
│       └── 6hr/               # Recorded market data (Parquet files)
└── strategies/
    └── nautilus/
        ├── test_single_maker_strategy.py
        ├── test_single_maker_config.yaml
        ├── run_backtest.py
        └── README.md
```

## Usage

### Basic Backtest

From the `benchmark/strategies/nautilus/` directory:

```bash
python run_backtest.py
```

This will:
1. Load configuration from `test_single_maker_config.yaml`
2. Load recorded market data from `benchmark/data/nautilus_trader/6hr/`
3. Run the backtest simulation
4. Display performance reports

### Custom Configuration

You can create a custom config file and pass it as an argument:

```bash
python run_backtest.py my_custom_config.yaml
```

### Example Output

```
================================================================================
TestSingleMakerStrategy Backtest
================================================================================
Instrument: SOLUSDT-LINEAR.BYBIT
Spread: 10.0 bps
MA Window: 5 minutes
Price Tolerance: 15.0 bps
Order Size: 1.0 (base)
Max Long Position: 5.0
Max Short Position: 5.0
Max Budget: 5000.0 (quote)
================================================================================

Loading data from: benchmark/data/nautilus_trader/6hr/
Loaded instrument: SOLUSDT-LINEAR.BYBIT
Loaded 1234567 order book deltas
Loaded 45678 trades

Starting backtest...
================================================================================
[Strategy logs will appear here...]
================================================================================
Backtest completed in 12.34 seconds
================================================================================

ACCOUNT REPORT
[Shows starting/ending balance, PnL, etc.]

ORDER FILLS REPORT
[Shows all order fills with timestamps, prices, quantities]

POSITIONS REPORT
[Shows position changes over time]

PERFORMANCE SUMMARY
Starting Balance: 5000.00 USDT
Ending Balance: 5042.35 USDT
Total PnL: 42.35
PnL %: 0.85%
Total Fills: 18
Buy Fills: 9
Sell Fills: 9
```

## Parameter Tuning

### Adjusting Spread

To make the strategy more/less aggressive:

```yaml
# Tighter spread (more aggressive, more fills)
spread_bps: 5.0

# Wider spread (less aggressive, fewer fills, better per-trade profit)
spread_bps: 20.0
```

### Adjusting MA Window

To make the strategy more/less reactive:

```yaml
# Shorter window (more reactive to recent prices)
ma_window_minutes: 2

# Longer window (smoother, less reactive)
ma_window_minutes: 10
```

### Adjusting Price Tolerance

To update orders more/less frequently:

```yaml
# Lower tolerance (update orders more frequently)
price_tolerance_bps: 5.0

# Higher tolerance (update orders less frequently)
price_tolerance_bps: 25.0
```

## Development & Testing

### Running with Test Data

For quick development testing, you can use a smaller data sample:

1. Record 10 minutes of data instead of 6 hours:
   ```bash
   python benchmark/nautilus_trader/native_recorder/run_2min_test.py
   ```

2. Update `test_single_maker_config.yaml`:
   ```yaml
   backtest:
     data_path: benchmark/data/nautilus_trader/test/
   ```

### Debugging

Enable debug logging in the config:

```yaml
logging:
  log_level: DEBUG
  log_events: true
```

### Common Issues

**Issue**: "No instruments found in catalog"
- **Solution**: Ensure you have recorded data using the data recorder script

**Issue**: "No order book deltas found"
- **Solution**: Check that the data path in config matches your recorded data location

**Issue**: "Orders not being placed"
- **Solution**: Check that MA window has accumulated enough data (needs at least ma_window_minutes of market data)

**Issue**: "Position limits reached immediately"
- **Solution**: Increase `max_long_position` and `max_short_position` in config

## Performance Benchmarking

To compare Nautilus Trader against other platforms:

1. **Record the same time period** across all platforms
2. **Use identical parameters** (spread, MA window, etc.)
3. **Measure**:
   - Backtest execution time
   - Total PnL
   - Number of fills
   - Win rate
   - Max drawdown
4. **Document** in the platform comparison matrix

### Expected Performance

For 6 hours of SOLUSDT data with default parameters:

- **Execution Time**: 10-30 seconds
- **Total Trades**: 10-50 (depending on market volatility)
- **PnL**: Expected positive but small (this is a test strategy)
- **Win Rate**: ~50% (market-making typically neutral)

## Advanced Usage

### Live Trading (Paper Trading)

**WARNING**: This is a test strategy with no alpha advantage. Do not use with real money!

To run in paper trading mode (not implemented in this basic version):

1. Set up Bybit testnet credentials
2. Modify the runner to use live engine instead of backtest engine
3. Monitor carefully and use kill switches

### Parameter Optimization

To find optimal parameters:

1. Create a grid search script (see benchmark workflow doc)
2. Test parameter combinations:
   - spread_bps: [5.0, 10.0, 15.0, 20.0]
   - ma_window_minutes: [2, 5, 10]
   - price_tolerance_bps: [5.0, 10.0, 15.0, 20.0]
3. Rank by Sharpe ratio or total PnL
4. Validate best parameters on out-of-sample data

## Contributing

This strategy is part of the Quant Trading Platform Benchmark project. To contribute:

1. Follow the coding style (Black formatter, type hints)
2. Add comprehensive logging for debugging
3. Document any changes in this README
4. Test thoroughly with recorded data

## References

- [Quant Workflow Benchmark Spec](../../../exploration/quant_workflow_benchmark.md) - Full strategy specification
- [Nautilus Trader Documentation](https://nautilustrader.io/docs/) - Platform documentation
- [Project CLAUDE.md](../../../CLAUDE.md) - Overall project goals and structure

## License

Part of the Quant Trading Platform Evaluation project.

---

**Last Updated**: 2025-11-09
**Version**: 1.0
**Author**: Claude Code (AI Assistant)
