"""
Statistical Analysis Module for Market Data Quality Validation.

This module provides comprehensive statistical analysis methods for validating
the quality of recorded market data from NautilusTrader. It focuses on detecting
anomalies, gaps, and quality issues in quotes, trades, and orderbook deltas.

Usage Example:
    >>> from pathlib import Path
    >>> import pandas as pd
    >>>
    >>> analyzer = StatisticalAnalyzer(Path("data/recordings/20251119-152837"))
    >>>
    >>> # Load quotes data
    >>> quotes_df = pd.read_parquet("quote_ticks.parquet")
    >>>
    >>> # Analyze data quality
    >>> gap_results = analyzer.analyze_gaps(quotes_df, "quotes")
    >>> spread_results = analyzer.analyze_spreads(quotes_df)
    >>> outlier_results = analyzer.detect_price_outliers(quotes_df)
    >>>
    >>> print(f"Max gap: {gap_results['max_gap_ms']:.2f}ms")
    >>> print(f"Mean spread: {spread_results['mean_spread_bps']:.2f} bps")

Author: Claude Code (Subagent 1)
Created: 2025-11-19
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List


class StatisticalAnalyzer:
    """
    Statistical analysis for market data quality validation.

    This class provides methods for comprehensive statistical analysis of market
    data including temporal gap detection, price outlier identification, bid-ask
    spread analysis, and volume profiling.

    The analyzer is designed to work with NautilusTrader parquet data files which
    use datetime64[ns, UTC] timestamps and standard market data schemas.

    Parameters
    ----------
    recording_dir : Path
        Path to the recording directory containing market data files

    Attributes
    ----------
    recording_dir : Path
        Recording directory path

    Examples
    --------
    >>> analyzer = StatisticalAnalyzer(Path("data/recordings/20251119-152837"))
    >>>
    >>> # Load and analyze quotes
    >>> quotes = pd.read_parquet("quote_ticks.parquet")
    >>> results = analyzer.analyze_gaps(quotes, "quotes", max_expected_gap_ms=1000)
    >>>
    >>> if results['num_large_gaps'] > 0:
    ...     print(f"Found {results['num_large_gaps']} large gaps")
    ...     for gap in results['large_gaps'][:5]:
    ...         print(f"  {gap['timestamp']}: {gap['gap_ms']:.2f}ms")
    """

    def __init__(self, recording_dir: Path):
        """
        Initialize the statistical analyzer.

        Parameters
        ----------
        recording_dir : Path
            Path to recording directory containing market data

        Raises
        ------
        FileNotFoundError
            If recording directory does not exist
        """
        self.recording_dir = Path(recording_dir)

        if not self.recording_dir.exists():
            raise FileNotFoundError(f"Recording directory not found: {recording_dir}")

    def analyze_gaps(
        self,
        df: pd.DataFrame,
        data_type: str,
        max_expected_gap_ms: float = 1000
    ) -> Dict[str, Any]:
        """
        Detect temporal gaps in market data streams.

        Analyzes the time intervals between successive data points to identify
        potential data loss, connection issues, or market inactivity. Uses
        vectorized operations for efficient processing of large datasets.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with 'timestamp' column (datetime64[ns, UTC])
        data_type : str
            Type of data: "quotes", "trades", or "deltas"
        max_expected_gap_ms : float, default=1000
            Threshold in milliseconds for flagging large gaps

        Returns
        -------
        dict
            Dictionary containing:
                - mean_interval_ms: Average time between updates
                - median_interval_ms: Median time between updates
                - std_interval_ms: Standard deviation of intervals
                - max_gap_ms: Largest gap detected
                - num_large_gaps: Count of gaps exceeding threshold
                - large_gaps: List of dicts with 'timestamp' and 'gap_ms' (max 100)
                - p95_interval_ms: 95th percentile interval
                - p99_interval_ms: 99th percentile interval

        Raises
        ------
        ValueError
            If DataFrame is empty or missing 'timestamp' column

        Examples
        --------
        >>> results = analyzer.analyze_gaps(quotes_df, "quotes", max_expected_gap_ms=500)
        >>> print(f"Mean interval: {results['mean_interval_ms']:.2f}ms")
        >>> print(f"Large gaps found: {results['num_large_gaps']}")
        """
        # Validate input
        if df.empty:
            raise ValueError("DataFrame is empty")

        if 'timestamp' not in df.columns:
            raise ValueError("DataFrame must have 'timestamp' column")

        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            raise ValueError("'timestamp' column must be datetime64 type")

        # Calculate intervals between successive timestamps (vectorized)
        intervals = df['timestamp'].diff()

        # Convert to milliseconds (intervals are timedelta64[ns])
        intervals_ms = intervals.dt.total_seconds() * 1000

        # Remove first NaN value from diff
        intervals_ms = intervals_ms.iloc[1:]

        # Calculate statistics
        mean_interval = float(intervals_ms.mean())
        median_interval = float(intervals_ms.median())
        std_interval = float(intervals_ms.std())
        max_gap = float(intervals_ms.max())

        # Calculate percentiles
        p95_interval = float(intervals_ms.quantile(0.95))
        p99_interval = float(intervals_ms.quantile(0.99))

        # Find large gaps
        large_gap_mask = intervals_ms > max_expected_gap_ms
        num_large_gaps = int(large_gap_mask.sum())

        # Extract large gaps with timestamps (limit to 100 for memory efficiency)
        large_gaps = []
        if num_large_gaps > 0:
            large_gap_indices = intervals_ms[large_gap_mask].index

            # Limit to 100 largest gaps
            largest_gaps_indices = intervals_ms[large_gap_mask].nlargest(min(100, num_large_gaps)).index

            for idx in largest_gaps_indices:
                large_gaps.append({
                    'timestamp': str(df.loc[idx, 'timestamp']),
                    'gap_ms': float(intervals_ms.loc[idx]),
                    'previous_timestamp': str(df.loc[idx-1, 'timestamp']) if idx > 0 else None
                })

        return {
            'data_type': data_type,
            'total_records': len(df),
            'mean_interval_ms': mean_interval,
            'median_interval_ms': median_interval,
            'std_interval_ms': std_interval,
            'max_gap_ms': max_gap,
            'p95_interval_ms': p95_interval,
            'p99_interval_ms': p99_interval,
            'num_large_gaps': num_large_gaps,
            'large_gaps': large_gaps,
            'threshold_ms': max_expected_gap_ms
        }

    def detect_price_outliers(
        self,
        df: pd.DataFrame,
        z_threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect price anomalies using Z-score and IQR methods.

        Identifies outliers in price data using two complementary methods:
        1. Z-score: Detects extreme deviations from mean
        2. IQR: Detects values outside 1.5 * IQR from quartiles
        3. Price jumps: Detects successive price changes >5%

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with 'price' or 'bid_price'/'ask_price' columns
        z_threshold : float, default=3.0
            Z-score threshold for outlier detection (typically 2.5-3.5)

        Returns
        -------
        dict
            Dictionary containing:
                - z_outliers_count: Number of Z-score outliers
                - iqr_outliers_count: Number of IQR outliers
                - price_jumps_count: Number of large price changes
                - z_outliers: List of outlier records (max 100)
                - price_jumps: List of jumps with timestamp and percentage
                - price_stats: Dict with mean, std, min, max, median
                - outlier_percentage: Percentage of total records

        Raises
        ------
        ValueError
            If DataFrame is empty or missing price columns

        Examples
        --------
        >>> results = analyzer.detect_price_outliers(quotes_df, z_threshold=3.0)
        >>> print(f"Z-score outliers: {results['z_outliers_count']}")
        >>> print(f"Price jumps: {results['price_jumps_count']}")
        >>>
        >>> # Examine specific outliers
        >>> for outlier in results['z_outliers'][:5]:
        ...     print(f"{outlier['timestamp']}: ${outlier['price']} (z={outlier['z_score']:.2f})")
        """
        # Validate input
        if df.empty:
            raise ValueError("DataFrame is empty")

        # Determine which price column to use
        price_col = None
        if 'price' in df.columns:
            price_col = 'price'
        elif 'bid_price' in df.columns:
            # For quotes, use mid-price
            if 'ask_price' in df.columns:
                prices = (df['bid_price'] + df['ask_price']) / 2
            else:
                prices = df['bid_price']
        elif 'ask_price' in df.columns:
            prices = df['ask_price']
        else:
            raise ValueError("DataFrame must have 'price', 'bid_price', or 'ask_price' column")

        # Get price series
        if price_col:
            prices = df[price_col]

        # Calculate price statistics
        price_mean = float(prices.mean())
        price_std = float(prices.std())
        price_min = float(prices.min())
        price_max = float(prices.max())
        price_median = float(prices.median())

        # Z-score outlier detection
        z_scores = np.abs((prices - price_mean) / price_std)
        z_outlier_mask = z_scores > z_threshold
        z_outliers_count = int(z_outlier_mask.sum())

        # IQR outlier detection
        q1 = prices.quantile(0.25)
        q3 = prices.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        iqr_outlier_mask = (prices < lower_bound) | (prices > upper_bound)
        iqr_outliers_count = int(iqr_outlier_mask.sum())

        # Extract Z-score outliers (limit to 100)
        z_outliers = []
        if z_outliers_count > 0:
            outlier_indices = z_scores[z_outlier_mask].nlargest(min(100, z_outliers_count)).index

            for idx in outlier_indices:
                z_outliers.append({
                    'timestamp': str(df.loc[idx, 'timestamp']) if 'timestamp' in df.columns else str(idx),
                    'price': float(prices.loc[idx]),
                    'z_score': float(z_scores.loc[idx]),
                    'deviation_from_mean': float(prices.loc[idx] - price_mean)
                })

        # Detect price jumps (>5% successive change)
        price_changes = prices.pct_change().abs()
        price_jump_mask = price_changes > 0.05
        price_jumps_count = int(price_jump_mask.sum())

        # Extract price jumps (limit to 100)
        price_jumps = []
        if price_jumps_count > 0:
            jump_indices = price_changes[price_jump_mask].nlargest(min(100, price_jumps_count)).index

            for idx in jump_indices:
                if idx > 0:  # Skip first row
                    price_jumps.append({
                        'timestamp': str(df.loc[idx, 'timestamp']) if 'timestamp' in df.columns else str(idx),
                        'previous_price': float(prices.loc[idx-1]),
                        'current_price': float(prices.loc[idx]),
                        'change_percentage': float(price_changes.loc[idx] * 100)
                    })

        return {
            'total_records': len(df),
            'z_outliers_count': z_outliers_count,
            'iqr_outliers_count': iqr_outliers_count,
            'price_jumps_count': price_jumps_count,
            'outlier_percentage': (z_outliers_count / len(df)) * 100 if len(df) > 0 else 0,
            'z_outliers': z_outliers,
            'price_jumps': price_jumps,
            'price_stats': {
                'mean': price_mean,
                'std': price_std,
                'min': price_min,
                'max': price_max,
                'median': price_median,
                'range': price_max - price_min
            },
            'thresholds': {
                'z_threshold': z_threshold,
                'iqr_lower_bound': float(lower_bound),
                'iqr_upper_bound': float(upper_bound)
            }
        }

    def analyze_spreads(self, quotes_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze bid-ask spread characteristics for market quality assessment.

        Examines the bid-ask spread to identify:
        - Normal spread statistics (mean, median, std)
        - Abnormal conditions (negative spreads = CRITICAL)
        - Market quality indicators (wide spreads, volatility)
        - Temporal evolution (hourly aggregation)

        Parameters
        ----------
        quotes_df : pd.DataFrame
            DataFrame with 'bid_price' and 'ask_price' columns

        Returns
        -------
        dict
            Dictionary containing:
                - mean_spread_bps: Mean spread in basis points
                - median_spread_bps: Median spread in basis points
                - std_spread_bps: Standard deviation in basis points
                - min_spread: Minimum spread
                - max_spread: Maximum spread
                - negative_spreads_count: Critical data errors (ask < bid)
                - zero_spreads_count: Count of zero spreads
                - wide_spreads_count: Spreads > 50 bps
                - spread_evolution: Dict of hourly statistics
                - percentiles: p1, p5, p25, p50, p75, p95, p99

        Raises
        ------
        ValueError
            If DataFrame is empty or missing required columns

        Examples
        --------
        >>> results = analyzer.analyze_spreads(quotes_df)
        >>>
        >>> if results['negative_spreads_count'] > 0:
        ...     print(f"CRITICAL: {results['negative_spreads_count']} negative spreads detected!")
        >>>
        >>> print(f"Mean spread: {results['mean_spread_bps']:.2f} bps")
        >>> print(f"Wide spreads (>50 bps): {results['wide_spreads_count']}")
        """
        # Validate input
        if quotes_df.empty:
            raise ValueError("DataFrame is empty")

        if 'bid_price' not in quotes_df.columns or 'ask_price' not in quotes_df.columns:
            raise ValueError("DataFrame must have 'bid_price' and 'ask_price' columns")

        # Calculate spreads
        spreads = quotes_df['ask_price'] - quotes_df['bid_price']

        # Calculate mid-price for basis points calculation
        mid_prices = (quotes_df['bid_price'] + quotes_df['ask_price']) / 2

        # Spreads in basis points (1 bp = 0.01%)
        spreads_bps = (spreads / mid_prices) * 10000

        # Basic statistics
        mean_spread_bps = float(spreads_bps.mean())
        median_spread_bps = float(spreads_bps.median())
        std_spread_bps = float(spreads_bps.std())
        min_spread = float(spreads.min())
        max_spread = float(spreads.max())

        # Percentiles
        percentiles = {
            'p1': float(spreads_bps.quantile(0.01)),
            'p5': float(spreads_bps.quantile(0.05)),
            'p25': float(spreads_bps.quantile(0.25)),
            'p50': float(spreads_bps.quantile(0.50)),
            'p75': float(spreads_bps.quantile(0.75)),
            'p95': float(spreads_bps.quantile(0.95)),
            'p99': float(spreads_bps.quantile(0.99))
        }

        # Detect anomalies
        negative_spreads_count = int((spreads < 0).sum())
        zero_spreads_count = int((spreads == 0).sum())
        wide_spreads_count = int((spreads_bps > 50).sum())

        # Temporal evolution (hourly aggregation)
        spread_evolution = {}
        if 'timestamp' in quotes_df.columns:
            # Create a copy for temporal analysis
            temp_df = quotes_df.copy()
            temp_df['spread_bps'] = spreads_bps
            temp_df['hour'] = temp_df['timestamp'].dt.floor('h')

            # Group by hour
            hourly_stats = temp_df.groupby('hour')['spread_bps'].agg([
                'mean', 'median', 'std', 'min', 'max', 'count'
            ]).to_dict('index')

            # Convert to serializable format
            spread_evolution = {
                str(hour): {
                    'mean_bps': float(stats_dict['mean']),
                    'median_bps': float(stats_dict['median']),
                    'std_bps': float(stats_dict['std']) if not pd.isna(stats_dict['std']) else 0.0,
                    'min_bps': float(stats_dict['min']),
                    'max_bps': float(stats_dict['max']),
                    'count': int(stats_dict['count'])
                }
                for hour, stats_dict in hourly_stats.items()
            }

        return {
            'total_quotes': len(quotes_df),
            'mean_spread_bps': mean_spread_bps,
            'median_spread_bps': median_spread_bps,
            'std_spread_bps': std_spread_bps,
            'min_spread': min_spread,
            'max_spread': max_spread,
            'negative_spreads_count': negative_spreads_count,
            'zero_spreads_count': zero_spreads_count,
            'wide_spreads_count': wide_spreads_count,
            'percentiles': percentiles,
            'spread_evolution': spread_evolution,
            'quality_flags': {
                'has_negative_spreads': negative_spreads_count > 0,
                'high_zero_spreads': (zero_spreads_count / len(quotes_df)) > 0.01,
                'high_wide_spreads': (wide_spreads_count / len(quotes_df)) > 0.05
            }
        }

    def analyze_volume(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze trade volume characteristics and patterns.

        Examines trade volume distribution and patterns to understand:
        - Volume statistics (total, mean, median)
        - Size distribution (percentiles)
        - Temporal patterns (15-minute buckets)
        - Buy/sell imbalance (if side information available)

        Parameters
        ----------
        trades_df : pd.DataFrame
            DataFrame with 'size' column (and optionally 'side' column)

        Returns
        -------
        dict
            Dictionary containing:
                - total_volume: Sum of all trade sizes
                - mean_trade_size: Average trade size
                - median_trade_size: Median trade size
                - std_trade_size: Standard deviation
                - max_trade_size: Largest trade
                - min_trade_size: Smallest trade
                - percentiles: p1, p5, p25, p50, p75, p95, p99
                - volume_by_time: Dict with 15-minute bucket aggregations
                - buy_sell_ratio: Ratio of buy to sell volume (if available)
                - trade_count: Total number of trades

        Raises
        ------
        ValueError
            If DataFrame is empty or missing 'size' column

        Examples
        --------
        >>> results = analyzer.analyze_volume(trades_df)
        >>> print(f"Total volume: {results['total_volume']:,.0f}")
        >>> print(f"Mean trade size: {results['mean_trade_size']:.4f}")
        >>>
        >>> if 'buy_sell_ratio' in results:
        ...     ratio = results['buy_sell_ratio']
        ...     print(f"Buy/sell ratio: {ratio:.2f} ({'buy' if ratio > 1 else 'sell'} pressure)")
        """
        # Validate input
        if trades_df.empty:
            raise ValueError("DataFrame is empty")

        if 'size' not in trades_df.columns:
            raise ValueError("DataFrame must have 'size' column")

        # Basic volume statistics
        total_volume = float(trades_df['size'].sum())
        mean_trade_size = float(trades_df['size'].mean())
        median_trade_size = float(trades_df['size'].median())
        std_trade_size = float(trades_df['size'].std())
        max_trade_size = float(trades_df['size'].max())
        min_trade_size = float(trades_df['size'].min())
        trade_count = len(trades_df)

        # Percentiles
        percentiles = {
            'p1': float(trades_df['size'].quantile(0.01)),
            'p5': float(trades_df['size'].quantile(0.05)),
            'p25': float(trades_df['size'].quantile(0.25)),
            'p50': float(trades_df['size'].quantile(0.50)),
            'p75': float(trades_df['size'].quantile(0.75)),
            'p95': float(trades_df['size'].quantile(0.95)),
            'p99': float(trades_df['size'].quantile(0.99))
        }

        # Temporal volume analysis (15-minute buckets)
        volume_by_time = {}
        if 'timestamp' in trades_df.columns:
            temp_df = trades_df.copy()
            temp_df['time_bucket'] = temp_df['timestamp'].dt.floor('15min')

            # Aggregate by time bucket
            time_buckets = temp_df.groupby('time_bucket')['size'].agg([
                'sum', 'mean', 'count'
            ]).to_dict('index')

            # Convert to serializable format
            volume_by_time = {
                str(bucket): {
                    'total_volume': float(stats_dict['sum']),
                    'mean_trade_size': float(stats_dict['mean']),
                    'trade_count': int(stats_dict['count'])
                }
                for bucket, stats_dict in time_buckets.items()
            }

        # Buy/sell analysis (if side column exists)
        result = {
            'trade_count': trade_count,
            'total_volume': total_volume,
            'mean_trade_size': mean_trade_size,
            'median_trade_size': median_trade_size,
            'std_trade_size': std_trade_size,
            'max_trade_size': max_trade_size,
            'min_trade_size': min_trade_size,
            'percentiles': percentiles,
            'volume_by_time': volume_by_time
        }

        # Add buy/sell analysis if side column exists
        if 'side' in trades_df.columns:
            # NautilusTrader uses 'BUYER' and 'SELLER' strings
            buy_mask = trades_df['side'] == 'BUYER'
            sell_mask = trades_df['side'] == 'SELLER'

            buy_volume = float(trades_df[buy_mask]['size'].sum())
            sell_volume = float(trades_df[sell_mask]['size'].sum())

            buy_count = int(buy_mask.sum())
            sell_count = int(sell_mask.sum())

            # Calculate ratio (avoid division by zero)
            buy_sell_ratio = buy_volume / sell_volume if sell_volume > 0 else float('inf')

            result['buy_sell_analysis'] = {
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'buy_count': buy_count,
                'sell_count': sell_count,
                'buy_sell_ratio': buy_sell_ratio,
                'net_volume': buy_volume - sell_volume,
                'buy_percentage': (buy_volume / total_volume * 100) if total_volume > 0 else 0,
                'sell_percentage': (sell_volume / total_volume * 100) if total_volume > 0 else 0
            }

        return result


# Convenience function for quick analysis
def quick_analysis(recording_dir: Path, instrument: str = "SOLUSDT-SPOT.BYBIT") -> Dict[str, Any]:
    """
    Perform quick statistical analysis on all data types for an instrument.

    This convenience function loads data and runs all analysis methods,
    returning a comprehensive quality report.

    Parameters
    ----------
    recording_dir : Path
        Path to recording directory
    instrument : str, default="SOLUSDT-SPOT.BYBIT"
        Instrument identifier

    Returns
    -------
    dict
        Comprehensive analysis results with keys:
            - quotes_gaps
            - quotes_spreads
            - quotes_outliers
            - trades_gaps
            - trades_volume
            - trades_outliers
            - deltas_gaps

    Examples
    --------
    >>> from pathlib import Path
    >>> results = quick_analysis(Path("data/recordings/20251119-152837"))
    >>>
    >>> # Check for critical issues
    >>> if results['quotes_spreads']['negative_spreads_count'] > 0:
    ...     print("CRITICAL: Negative spreads detected!")
    >>>
    >>> # Summary statistics
    >>> print(f"Quotes: {results['quotes_gaps']['total_records']:,}")
    >>> print(f"Trades: {results['trades_volume']['trade_count']:,}")
    >>> print(f"Mean spread: {results['quotes_spreads']['mean_spread_bps']:.2f} bps")
    """
    analyzer = StatisticalAnalyzer(recording_dir)
    results = {}

    # Analyze quotes
    try:
        quotes_file = recording_dir / "quote_ticks" / instrument / "quote_ticks.parquet"
        quotes_df = pd.read_parquet(quotes_file)

        results['quotes_gaps'] = analyzer.analyze_gaps(quotes_df, "quotes")
        results['quotes_spreads'] = analyzer.analyze_spreads(quotes_df)
        results['quotes_outliers'] = analyzer.detect_price_outliers(quotes_df)
    except Exception as e:
        results['quotes_error'] = str(e)

    # Analyze trades
    try:
        trades_file = recording_dir / "trade_ticks" / instrument / "trade_ticks.parquet"
        trades_df = pd.read_parquet(trades_file)

        results['trades_gaps'] = analyzer.analyze_gaps(trades_df, "trades")
        results['trades_volume'] = analyzer.analyze_volume(trades_df)
        results['trades_outliers'] = analyzer.detect_price_outliers(trades_df)
    except Exception as e:
        results['trades_error'] = str(e)

    # Analyze deltas
    try:
        deltas_file = recording_dir / "order_book_deltas" / instrument / "order_book_deltas.parquet"
        deltas_df = pd.read_parquet(deltas_file)

        results['deltas_gaps'] = analyzer.analyze_gaps(deltas_df, "deltas", max_expected_gap_ms=100)
    except Exception as e:
        results['deltas_error'] = str(e)

    return results
