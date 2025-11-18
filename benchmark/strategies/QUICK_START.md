# Quick Start Guide - TestSingleMakerStrategy

## TL;DR - Run in 3 Steps

### 1. Record Data (if you haven't already)

```bash
cd /Users/benjaminang/Desktop/Trading\ Engines
python benchmark/nautilus_trader/native_recorder/run_6hr_recording.py
```

Wait for 6 hours of recording to complete.

### 2. Navigate to Strategy Directory

```bash
cd /Users/benjaminang/Desktop/Trading\ Engines/benchmark/strategies/nautilus
```

### 3. Run Backtest

```bash
python3 run_backtest.py
```

That's it! The backtest will run and display results.

---

## What You'll See

1. **Configuration Summary**: Shows all strategy parameters
2. **Data Loading**: Confirms data is loaded from catalog
3. **Backtest Progress**: Strategy logs as it runs
4. **Performance Reports**:
   - Account Report (balance, PnL)
   - Order Fills Report (all trades)
   - Positions Report (position changes)
   - Performance Summary (key metrics)

---

## Common Commands

### Run with Custom Config

```bash
python3 run_backtest.py my_config.yaml
```

### Check Strategy is Valid

```bash
python3 -c "from test_single_maker_strategy import TestSingleMakerStrategy; print('OK')"
```

### View Configuration

```bash
cat test_single_maker_config.yaml
```

### Edit Configuration

```bash
nano test_single_maker_config.yaml
# or
vim test_single_maker_config.yaml
# or use your preferred editor
```

---

## Key Configuration Parameters to Tweak

Edit `test_single_maker_config.yaml`:

```yaml
strategy:
  spread_bps: 10.0              # ← Order spread (lower = more fills)
  ma_window_minutes: 5          # ← MA smoothing (lower = more reactive)
  price_tolerance_bps: 15.0     # ← Re-quote threshold (lower = more updates)
  order_size_base: 1.0          # ← Trade size in SOL
  max_long_position: 5.0        # ← Max long position
  max_short_position: 5.0       # ← Max short position
  max_budget_quote: 5000.0      # ← Max capital in USDT
```

---

## Troubleshooting

### "No instruments found in catalog"

**Fix**: Run the data recorder first:
```bash
python benchmark/nautilus_trader/native_recorder/run_6hr_recording.py
```

### "Data path does not exist"

**Fix**: Update `data_path` in `test_single_maker_config.yaml`:
```yaml
backtest:
  data_path: benchmark/data/nautilus_trader/6hr/  # ← Adjust if needed
```

### "Module not found"

**Fix**: Make sure Nautilus Trader is installed:
```bash
cd nautilus_trader
pip install -e .
```

### Orders not being placed

**Fix**: The strategy needs to accumulate MA window data first (5 minutes by default). This is normal during the first few minutes of the backtest.

---

## Next Steps

1. **Read Full README**: See `README.md` for detailed documentation
2. **Review Strategy Code**: See `test_single_maker_strategy.py`
3. **Optimize Parameters**: Try different spreads, MA windows, etc.
4. **Compare Platforms**: Run same test on QTE and compare results

---

## File Structure

```
benchmark/strategies/nautilus/
├── test_single_maker_strategy.py    # Strategy implementation
├── test_single_maker_config.yaml    # Configuration (edit this!)
├── run_backtest.py                  # Backtest runner
├── README.md                        # Full documentation
└── QUICK_START.md                   # This file
```

---

**Need Help?** Check the full README.md or the benchmark spec at:
`exploration/quant_workflow_benchmark.md`
