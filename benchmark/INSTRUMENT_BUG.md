# Nautilus Trader Bybit Instrument Provider Bug

## Issue
Nautilus Trader's Bybit instrument provider does NOT load major USDT-margined LINEAR perpetuals (SOLUSDT, BTCUSDT, etc.)

## Root Cause
- Bybit API returns 644 LINEAR perpetual instruments
- Nautilus only loads 500 LINEAR instruments
- **Missing instruments include**: `SOLUSDT`, `BTCUSDT` (major USDT-margined perpetuals)
- **Present instruments include**: `SOLPERP`, `BTCPERP` (USDC-margined perpetuals)

## Evidence
```bash
# Bybit API confirms SOLUSDT exists as LinearPerpetual
curl "https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=SOLUSDT"
# Returns: "symbol": "SOLUSDT", "contractType": "LinearPerpetual"

# Nautilus cache inspection
# Total LINEAR instruments: 500
# BTCUSDT-LINEAR.BYBIT: NOT FOUND ❌
# SOLUSDT-LINEAR.BYBIT: NOT FOUND ❌
# BTCPERP-LINEAR.BYBIT: FOUND ✅
# SOLPERP-LINEAR.BYBIT: FOUND ✅
```

## Workaround
Use USDC-margined perpetuals instead of USDT-margined:
- ~~`SOLUSDT-LINEAR.BYBIT`~~ → `SOLPERP-LINEAR.BYBIT` ✅
- ~~`BTCUSDT-LINEAR.BYBIT`~~ → `BTCPERP-LINEAR.BYBIT` ✅

## Impact on Benchmark
For fair comparison with other platforms, we're using:
- **LEAN**: SOLUSDT (USDT-margined linear) + SOLUSD (inverse)
- **QTE**: SOLUSDT (USDT-margined linear) + SOLUSD (inverse)
- **Nautilus**: SOLPERP (USDC-margined linear) + SOLUSD (inverse) ⚠️

Note: SOLPERP uses USDC as quote currency instead of USDT, which may affect funding rate dynamics and liquidity.

## Upstream Issue
This appears to be a bug in `nautilus_trader.adapters.bybit.providers.BybitInstrumentProvider`.
The provider should load ALL instruments from Bybit's API, not filter out major USDT perpetuals.

**Location**: `nautilus_trader/adapters/bybit/providers.py`
**Created**: 2025-11-09
**Status**: Not reported upstream yet

## Date Discovered
2025-11-09 (during benchmark setup)
