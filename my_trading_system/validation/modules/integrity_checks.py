"""
Integrity Checks Module - Advanced Data Validation System

Trading Engines Project - Wave 1 Validation (Parallel Execution)
Location: my_trading_system/validation/modules/integrity_checks.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-19

Validates data integrity for market data recordings:
- Duplicate detection (exact and timestamp-based)
- Missing/invalid value identification
- Cross-validation between data types (quotes vs trades)

Designed for large datasets (4M+ records) with efficient vectorized operations.

Examples
--------
>>> from pathlib import Path
>>> checker = IntegrityChecker(Path("data/recordings/20251119-152837"))
>>>
>>> # Check for duplicates
>>> quotes_df = pd.read_parquet("quotes.parquet")
>>> dup_results = checker.detect_duplicates(quotes_df, "quotes")
>>> print(f"Found {dup_results['exact_duplicates_count']} exact duplicates")
>>>
>>> # Check missing values
>>> missing_results = checker.check_missing_values(quotes_df, "quotes")
>>> print(f"Total invalid records: {missing_results['total_invalid_count']}")
>>>
>>> # Cross-validate quotes and trades
>>> trades_df = pd.read_parquet("trades.parquet")
>>> cross_results = checker.cross_validate_data_types(quotes_df, trades_df)
>>> print(f"Trades outside spread: {cross_results['trades_outside_spread_percentage']:.2f}%")
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta


class IntegrityChecker:
    """
    Data integrity validation for market data recordings.

    Performs comprehensive integrity checks on market data including:
    - Duplicate detection (exact matches and timestamp collisions)
    - Missing value detection (null, NaN, zero, negative prices/sizes)
    - Cross-validation between quotes and trades

    Parameters
    ----------
    recording_dir : Path
        Path to the recording directory containing parquet files

    Attributes
    ----------
    recording_dir : Path
        Recording directory path

    Examples
    --------
    >>> checker = IntegrityChecker(Path("data/recordings/20251119-152837"))
    >>>
    >>> # Load data
    >>> quotes_df = pd.read_parquet("quotes.parquet")
    >>> trades_df = pd.read_parquet("trades.parquet")
    >>>
    >>> # Run integrity checks
    >>> dup_check = checker.detect_duplicates(quotes_df, "quotes")
    >>> missing_check = checker.check_missing_values(trades_df, "trades")
    >>> cross_check = checker.cross_validate_data_types(quotes_df, trades_df)
    """

    def __init__(self, recording_dir: Path):
        """
        Initialize the IntegrityChecker.

        Parameters
        ----------
        recording_dir : Path
            Path to recording directory
        """
        self.recording_dir = Path(recording_dir)

    def detect_duplicates(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """
        Detect duplicate entries in market data.

        Performs three types of duplicate detection:
        1. Exact duplicates (all columns match)
        2. Timestamp duplicates (same timestamp, different data)
        3. Trade ID duplicates (for trades only, if trade_id exists)

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to check for duplicates
        data_type : str
            Type of data: "quotes", "trades", or "deltas"

        Returns
        -------
        dict
            Dictionary containing:
            - exact_duplicates_count : int
                Number of exact duplicate rows
            - timestamp_duplicates_count : int
                Number of timestamp duplicates
            - trade_id_duplicates_count : int
                Number of trade_id duplicates (trades only)
            - duplicate_records : list[dict]
                Sample duplicate records (max 100 for performance)
            - duplicate_percentage : float
                Percentage of total records that are duplicates

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'timestamp': [pd.Timestamp('2025-11-19 12:00:00'),
        ...                   pd.Timestamp('2025-11-19 12:00:01'),
        ...                   pd.Timestamp('2025-11-19 12:00:00')],  # Duplicate timestamp
        ...     'price': [100.0, 101.0, 100.0]  # Exact duplicate
        ... })
        >>> results = checker.detect_duplicates(df, 'quotes')
        >>> print(f"Exact duplicates: {results['exact_duplicates_count']}")
        Exact duplicates: 1
        """
        results = {
            'exact_duplicates_count': 0,
            'timestamp_duplicates_count': 0,
            'trade_id_duplicates_count': 0,
            'duplicate_records': [],
            'duplicate_percentage': 0.0
        }

        if df.empty:
            return results

        total_records = len(df)

        # 1. Detect exact duplicates (all columns match)
        exact_dups_mask = df.duplicated(keep='first')
        exact_dups_count = exact_dups_mask.sum()
        results['exact_duplicates_count'] = int(exact_dups_count)

        # Get sample of exact duplicates (limit to 100 records)
        if exact_dups_count > 0:
            exact_dup_rows = df[exact_dups_mask].head(100)
            results['duplicate_records'].extend(
                exact_dup_rows.to_dict('records')
            )

        # 2. Detect timestamp duplicates (same timestamp, potentially different data)
        if 'timestamp' in df.columns:
            ts_dups_mask = df.duplicated(subset=['timestamp'], keep=False)
            # Subtract exact duplicates to avoid double counting
            ts_only_dups = ts_dups_mask & ~exact_dups_mask
            ts_dups_count = ts_only_dups.sum()
            results['timestamp_duplicates_count'] = int(ts_dups_count)

        # 3. Detect trade_id duplicates (for trades only)
        if data_type == 'trades' and 'trade_id' in df.columns:
            trade_id_dups_mask = df.duplicated(subset=['trade_id'], keep='first')
            trade_id_dups_count = trade_id_dups_mask.sum()
            results['trade_id_duplicates_count'] = int(trade_id_dups_count)

            # Add sample trade_id duplicates
            if trade_id_dups_count > 0:
                trade_id_dup_rows = df[trade_id_dups_mask].head(50)
                results['duplicate_records'].extend(
                    trade_id_dup_rows.to_dict('records')
                )

        # Calculate overall duplicate percentage
        total_duplicates = exact_dups_count + ts_dups_count
        if data_type == 'trades' and 'trade_id' in df.columns:
            total_duplicates += results['trade_id_duplicates_count']

        results['duplicate_percentage'] = (total_duplicates / total_records * 100) if total_records > 0 else 0.0

        # Limit duplicate_records to 100 total
        results['duplicate_records'] = results['duplicate_records'][:100]

        return results

    def check_missing_values(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """
        Check for null/NaN/missing values and invalid data.

        Validates data quality by checking for:
        - Null/NaN values in any column
        - Zero or negative prices (invalid for market data)
        - Zero or negative sizes/quantities

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        data_type : str
            Type of data: "quotes", "trades", or "deltas"

        Returns
        -------
        dict
            Dictionary containing:
            - missing_values : dict[str, dict]
                Per-column missing value counts and percentages
                Format: {column: {'count': int, 'percentage': float}}
            - invalid_prices : dict[str, dict]
                Invalid price counts (zero/negative)
                Format: {column: {'zero_count': int, 'negative_count': int}}
            - invalid_sizes : dict[str, dict]
                Invalid size counts (zero/negative)
                Format: {column: {'zero_count': int, 'negative_count': int}}
            - total_invalid_count : int
                Total number of invalid records across all checks

        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'price': [100.0, np.nan, 0.0, -10.0],
        ...     'size': [1.0, 2.0, 0.0, 1.0],
        ...     'timestamp': [pd.Timestamp('2025-11-19')] * 4
        ... })
        >>> results = checker.check_missing_values(df, 'trades')
        >>> print(results['invalid_prices'])
        {'price': {'zero_count': 1, 'negative_count': 1}}
        """
        results = {
            'missing_values': {},
            'invalid_prices': {},
            'invalid_sizes': {},
            'total_invalid_count': 0
        }

        if df.empty:
            return results

        total_records = len(df)
        total_invalid = 0

        # 1. Check for null/NaN values in all columns
        null_counts = df.isnull().sum()
        for column, count in null_counts.items():
            if count > 0:
                results['missing_values'][column] = {
                    'count': int(count),
                    'percentage': float(count / total_records * 100)
                }
                total_invalid += count

        # 2. Check for invalid prices (zero or negative)
        # Price columns vary by data type
        price_columns = []
        if data_type == 'quotes':
            price_columns = ['bid_price', 'ask_price']
        elif data_type == 'trades':
            price_columns = ['price']
        elif data_type == 'deltas':
            price_columns = ['price']

        for col in price_columns:
            if col in df.columns:
                # Check for zero prices
                zero_mask = df[col] == 0.0
                zero_count = zero_mask.sum()

                # Check for negative prices
                negative_mask = df[col] < 0.0
                negative_count = negative_mask.sum()

                if zero_count > 0 or negative_count > 0:
                    results['invalid_prices'][col] = {
                        'zero_count': int(zero_count),
                        'negative_count': int(negative_count)
                    }
                    # Don't double-count null values already counted above
                    non_null_zero = zero_mask & ~df[col].isnull()
                    non_null_negative = negative_mask & ~df[col].isnull()
                    total_invalid += int(non_null_zero.sum() + non_null_negative.sum())

        # 3. Check for invalid sizes (zero or negative)
        size_columns = []
        if data_type == 'quotes':
            size_columns = ['bid_size', 'ask_size']
        elif data_type == 'trades':
            size_columns = ['size']
        elif data_type == 'deltas':
            size_columns = ['size']

        for col in size_columns:
            if col in df.columns:
                # Zero size can be valid for CLEAR deltas, but check anyway
                zero_mask = df[col] == 0.0
                zero_count = zero_mask.sum()

                # Negative size is always invalid
                negative_mask = df[col] < 0.0
                negative_count = negative_mask.sum()

                if zero_count > 0 or negative_count > 0:
                    results['invalid_sizes'][col] = {
                        'zero_count': int(zero_count),
                        'negative_count': int(negative_count)
                    }
                    # Don't double-count nulls
                    non_null_zero = zero_mask & ~df[col].isnull()
                    non_null_negative = negative_mask & ~df[col].isnull()
                    total_invalid += int(non_null_zero.sum() + non_null_negative.sum())

        results['total_invalid_count'] = total_invalid

        return results

    def cross_validate_data_types(self, quotes_df: pd.DataFrame, trades_df: pd.DataFrame,
                                  tolerance_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Validate consistency between quotes and trades data.

        Performs temporal cross-validation to ensure trades align with market quotes:
        1. Checks time range alignment between datasets
        2. Validates trade prices fall within bid-ask spread
        3. Identifies anomalous trades outside normal spread

        Uses pandas merge_asof for efficient temporal joins with nearest quote
        within the specified time window.

        Parameters
        ----------
        quotes_df : pd.DataFrame
            Quote ticks DataFrame with columns: timestamp, bid_price, ask_price, bid_size, ask_size
        trades_df : pd.DataFrame
            Trade ticks DataFrame with columns: timestamp, price, size, side, trade_id
        tolerance_seconds : float, default=1.0
            Maximum time difference (in seconds) for matching trades to quotes

        Returns
        -------
        dict
            Dictionary containing:
            - time_alignment : dict
                Start/end times for quotes and trades
                Format: {
                    'quotes_start': str, 'quotes_end': str,
                    'trades_start': str, 'trades_end': str
                }
            - trades_within_spread_count : int
                Number of trades within bid-ask spread
            - trades_outside_spread_count : int
                Number of trades outside bid-ask spread
            - trades_outside_spread_percentage : float
                Percentage of trades outside spread
            - anomalous_trades : list[dict]
                Sample of anomalous trades (max 50 records)
                Each record includes: trade data + matched quote + deviation
            - time_range_overlap_seconds : float
                Overlap duration between quotes and trades in seconds

        Examples
        --------
        >>> quotes_df = pd.DataFrame({
        ...     'timestamp': pd.date_range('2025-11-19 12:00:00', periods=100, freq='1s'),
        ...     'bid_price': [99.0] * 100,
        ...     'ask_price': [101.0] * 100,
        ...     'bid_size': [10.0] * 100,
        ...     'ask_size': [10.0] * 100
        ... })
        >>> trades_df = pd.DataFrame({
        ...     'timestamp': pd.date_range('2025-11-19 12:00:05', periods=10, freq='5s'),
        ...     'price': [100.0] * 10,  # All within spread
        ...     'size': [1.0] * 10,
        ...     'side': ['BUY'] * 10,
        ...     'trade_id': [str(i) for i in range(10)]
        ... })
        >>> results = checker.cross_validate_data_types(quotes_df, trades_df)
        >>> print(f"Within spread: {results['trades_within_spread_count']}")
        Within spread: 10
        """
        results = {
            'time_alignment': {},
            'trades_within_spread_count': 0,
            'trades_outside_spread_count': 0,
            'trades_outside_spread_percentage': 0.0,
            'anomalous_trades': [],
            'time_range_overlap_seconds': 0.0
        }

        # Handle empty DataFrames
        if quotes_df.empty or trades_df.empty:
            return results

        # 1. Time range alignment check
        quotes_start = quotes_df['timestamp'].min()
        quotes_end = quotes_df['timestamp'].max()
        trades_start = trades_df['timestamp'].min()
        trades_end = trades_df['timestamp'].max()

        results['time_alignment'] = {
            'quotes_start': str(quotes_start),
            'quotes_end': str(quotes_end),
            'trades_start': str(trades_start),
            'trades_end': str(trades_end)
        }

        # Calculate overlap
        overlap_start = max(quotes_start, trades_start)
        overlap_end = min(quotes_end, trades_end)
        if overlap_end > overlap_start:
            overlap_duration = (overlap_end - overlap_start).total_seconds()
            results['time_range_overlap_seconds'] = float(overlap_duration)

        # 2. Cross-validate trades against quotes using merge_asof
        # merge_asof requires sorted DataFrames
        quotes_sorted = quotes_df.sort_values('timestamp').copy()
        trades_sorted = trades_df.sort_values('timestamp').copy()

        # Perform merge_asof: for each trade, find nearest quote within tolerance
        # direction='nearest' finds closest quote (past or future)
        # tolerance controls maximum time difference
        tolerance_td = pd.Timedelta(seconds=tolerance_seconds)

        merged = pd.merge_asof(
            trades_sorted,
            quotes_sorted,
            on='timestamp',
            direction='nearest',
            tolerance=tolerance_td,
            suffixes=('_trade', '_quote')
        )

        # Filter out trades that couldn't be matched (NaN bid_price means no quote within tolerance)
        matched = merged[merged['bid_price'].notna()].copy()

        if matched.empty:
            return results

        # 3. Check if trade prices fall within bid-ask spread
        # Allow small tolerance (1 tick = 0.001 for crypto)
        tick_tolerance = 0.001

        # Trade is valid if: bid_price - tolerance <= trade_price <= ask_price + tolerance
        within_spread = (
            (matched['price'] >= matched['bid_price'] - tick_tolerance) &
            (matched['price'] <= matched['ask_price'] + tick_tolerance)
        )

        trades_within = within_spread.sum()
        trades_outside = (~within_spread).sum()

        results['trades_within_spread_count'] = int(trades_within)
        results['trades_outside_spread_count'] = int(trades_outside)
        results['trades_outside_spread_percentage'] = float(
            trades_outside / len(matched) * 100 if len(matched) > 0 else 0.0
        )

        # 4. Extract anomalous trades (outside spread)
        if trades_outside > 0:
            anomalous = matched[~within_spread].head(50).copy()

            # Calculate deviation from spread
            # For trades above ask: deviation = price - ask_price
            # For trades below bid: deviation = bid_price - price
            anomalous['spread_deviation'] = np.where(
                anomalous['price'] > anomalous['ask_price'],
                anomalous['price'] - anomalous['ask_price'],
                anomalous['bid_price'] - anomalous['price']
            )

            # Convert to dict, including relevant columns
            anomalous_records = anomalous[[
                'timestamp', 'price', 'size', 'side', 'trade_id',
                'bid_price', 'ask_price', 'spread_deviation'
            ]].to_dict('records')

            results['anomalous_trades'] = anomalous_records

        return results


# Example usage and testing
if __name__ == '__main__':
    """
    Test the IntegrityChecker with sample data.
    """
    print("=== IntegrityChecker Module Test ===\n")

    # Create sample data for testing
    print("1. Testing duplicate detection...")
    sample_with_dupes = pd.DataFrame({
        'timestamp': pd.to_datetime([
            '2025-11-19 12:00:00',
            '2025-11-19 12:00:01',
            '2025-11-19 12:00:00',  # Duplicate timestamp
            '2025-11-19 12:00:02',
            '2025-11-19 12:00:01'   # Exact duplicate
        ], utc=True),
        'price': [100.0, 101.0, 100.0, 102.0, 101.0],
        'size': [1.0, 2.0, 1.0, 3.0, 2.0]
    })

    checker = IntegrityChecker(Path('.'))
    dup_results = checker.detect_duplicates(sample_with_dupes, 'quotes')
    print(f"   Exact duplicates: {dup_results['exact_duplicates_count']}")
    print(f"   Timestamp duplicates: {dup_results['timestamp_duplicates_count']}")
    print(f"   Duplicate percentage: {dup_results['duplicate_percentage']:.2f}%")

    # Test missing values
    print("\n2. Testing missing value detection...")
    sample_with_nulls = pd.DataFrame({
        'timestamp': pd.to_datetime(['2025-11-19 12:00:00'] * 5, utc=True),
        'price': [100.0, np.nan, 0.0, -10.0, 101.0],
        'size': [1.0, 2.0, 0.0, 1.0, np.nan]
    })

    missing_results = checker.check_missing_values(sample_with_nulls, 'trades')
    print(f"   Missing values: {missing_results['missing_values']}")
    print(f"   Invalid prices: {missing_results['invalid_prices']}")
    print(f"   Invalid sizes: {missing_results['invalid_sizes']}")
    print(f"   Total invalid count: {missing_results['total_invalid_count']}")

    # Test cross-validation
    print("\n3. Testing cross-validation...")
    quotes_sample = pd.DataFrame({
        'timestamp': pd.date_range('2025-11-19 12:00:00', periods=100, freq='1s', tz='UTC'),
        'bid_price': [99.0] * 100,
        'ask_price': [101.0] * 100,
        'bid_size': [10.0] * 100,
        'ask_size': [10.0] * 100
    })

    trades_sample = pd.DataFrame({
        'timestamp': pd.date_range('2025-11-19 12:00:05', periods=10, freq='5s', tz='UTC'),
        'price': [100.0, 100.5, 99.5, 102.0, 100.0, 98.0, 100.0, 101.0, 99.0, 100.0],  # Some outside spread
        'size': [1.0] * 10,
        'side': ['BUY'] * 10,
        'trade_id': [str(i) for i in range(10)]
    })

    cross_results = checker.cross_validate_data_types(quotes_sample, trades_sample)
    print(f"   Trades within spread: {cross_results['trades_within_spread_count']}")
    print(f"   Trades outside spread: {cross_results['trades_outside_spread_count']}")
    print(f"   Outside spread percentage: {cross_results['trades_outside_spread_percentage']:.2f}%")
    print(f"   Time overlap (seconds): {cross_results['time_range_overlap_seconds']:.1f}")
    print(f"   Anomalous trades count: {len(cross_results['anomalous_trades'])}")

    print("\n=== All tests completed successfully! ===")
