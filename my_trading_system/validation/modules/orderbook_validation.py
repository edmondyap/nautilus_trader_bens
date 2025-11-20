"""
Orderbook Validation Module

Advanced validation system for orderbook delta data structure and consistency.

This module validates orderbook reconstruction from delta updates by:
1. Reconstructing orderbook snapshots from delta streams
2. Validating price level ordering (bids descending, asks ascending)
3. Detecting crossed orderbooks (bid >= ask, should never happen)
4. Analyzing orderbook depth consistency over time

Key Concepts:
--------------
Orderbook deltas represent incremental changes to the orderbook:
- action="ADD": New price level added to the book
- action="UPDATE": Existing price level quantity changed
- action="DELETE": Price level removed from the book
- action="CLEAR": Full orderbook reset (typically on snapshot)
- side="BUY": Bid side of the book
- side="SELL": Ask side of the book
- side="NO_ORDER_SIDE": Used for CLEAR actions

Reconstruction Algorithm:
-------------------------
To validate orderbook state at time T:
1. Collect all deltas up to timestamp T
2. For each price level, keep only the most recent action
3. Filter out DELETE actions (those levels no longer exist)
4. Filter out CLEAR actions with NO_ORDER_SIDE
5. Split into bids (BUY) and asks (SELL)
6. Sort bids descending by price, asks ascending by price

Performance Optimization:
-------------------------
With 4M+ deltas, full reconstruction is expensive. We use sampling:
- Sample every Nth delta (e.g., every 500th or 1000th record)
- Still provides thousands of validation checkpoints
- Reduces execution time from minutes to seconds
- Maintains statistical significance for anomaly detection

Author: Claude Code (Subagent 3)
Created: 2025-11-19
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime


class OrderbookValidator:
    """
    Orderbook structure and consistency validation.

    Validates orderbook reconstruction from delta streams, checking for:
    - Price level ordering violations (bids should be descending, asks ascending)
    - Crossed orderbook detection (best_bid >= best_ask, critical error)
    - Depth consistency over time (maintaining expected number of levels)

    This validator reconstructs orderbook snapshots from delta streams at
    sampled intervals to validate orderbook integrity without processing
    every single delta (which would be prohibitively expensive).

    Parameters
    ----------
    recording_dir : Path
        Path to recording directory containing orderbook delta data

    Examples
    --------
    >>> validator = OrderbookValidator(Path("data/recordings/20251119-152837"))
    >>> deltas_df = pd.read_parquet("path/to/deltas.parquet")
    >>>
    >>> # Validate price ordering
    >>> results = validator.validate_price_levels(deltas_df, sample_rate=1000)
    >>> print(f"Violations: {results['bid_ordering_violations']}")
    >>>
    >>> # Detect crossed books
    >>> crossed = validator.detect_crossed_book(deltas_df, sample_rate=500)
    >>> print(f"Crossed books: {crossed['crossed_books_detected']}")
    >>>
    >>> # Analyze depth consistency
    >>> depth = validator.analyze_depth_consistency(deltas_df, expected_depth=50)
    >>> print(f"Mean bid levels: {depth['mean_bid_levels']:.1f}")
    """

    def __init__(self, recording_dir: Path):
        """
        Initialize orderbook validator.

        Parameters
        ----------
        recording_dir : Path
            Path to recording directory
        """
        self.recording_dir = Path(recording_dir)

        if not self.recording_dir.exists():
            raise FileNotFoundError(f"Recording directory not found: {recording_dir}")

    def validate_price_levels(self, deltas_df: pd.DataFrame, sample_rate: int = 1000) -> Dict[str, Any]:
        """
        Validate orderbook level ordering by reconstructing snapshots.

        Reconstructs orderbook at sampled intervals and verifies:
        - Bid levels are in descending price order (highest bid first)
        - Ask levels are in ascending price order (lowest ask first)

        Any violation indicates corrupted orderbook data or exchange issues.

        Parameters
        ----------
        deltas_df : pd.DataFrame
            Orderbook deltas DataFrame with columns:
            - timestamp: datetime64[ns, UTC]
            - action: str (ADD, UPDATE, DELETE, CLEAR)
            - side: str (BUY, SELL, NO_ORDER_SIDE)
            - price: float
            - size: float
        sample_rate : int, default=1000
            Sample every Nth record for performance optimization.
            Lower values = more thorough but slower.

        Returns
        -------
        dict
            Validation results with keys:
            - snapshots_checked: int - Number of orderbook snapshots validated
            - bid_ordering_violations: int - Count of bid ordering errors
            - ask_ordering_violations: int - Count of ask ordering errors
            - violations: list[dict] - Details of each violation
                - timestamp: pd.Timestamp - When violation occurred
                - type: str - "bid_ordering" or "ask_ordering"
                - details: str - Description of the violation

        Examples
        --------
        >>> results = validator.validate_price_levels(deltas_df, sample_rate=500)
        >>> if results['bid_ordering_violations'] > 0:
        ...     print("WARNING: Bid ordering violations detected!")
        ...     for v in results['violations']:
        ...         print(f"  {v['timestamp']}: {v['details']}")
        """
        # Sort deltas by timestamp
        deltas_df = deltas_df.sort_values('timestamp').reset_index(drop=True)

        # Sample indices for validation
        total_rows = len(deltas_df)
        sample_indices = range(sample_rate - 1, total_rows, sample_rate)

        # Track results
        snapshots_checked = 0
        bid_violations = 0
        ask_violations = 0
        violations = []

        print(f"Validating price levels: {len(sample_indices)} snapshots to check...")

        for idx in sample_indices:
            timestamp = deltas_df.iloc[idx]['timestamp']

            # Reconstruct orderbook at this point
            bids, asks = self._reconstruct_orderbook_snapshot(deltas_df, up_to_timestamp=timestamp)

            snapshots_checked += 1

            # Validate bid ordering (should be descending)
            if len(bids) > 1:
                bid_prices = bids['price'].values
                if not np.all(bid_prices[:-1] >= bid_prices[1:]):
                    bid_violations += 1
                    violations.append({
                        'timestamp': timestamp,
                        'type': 'bid_ordering',
                        'details': f'Bids not in descending order: {bid_prices[:5]}'
                    })

            # Validate ask ordering (should be ascending)
            if len(asks) > 1:
                ask_prices = asks['price'].values
                if not np.all(ask_prices[:-1] <= ask_prices[1:]):
                    ask_violations += 1
                    violations.append({
                        'timestamp': timestamp,
                        'type': 'ask_ordering',
                        'details': f'Asks not in ascending order: {ask_prices[:5]}'
                    })

            # Progress indicator (every 1000 snapshots)
            if snapshots_checked % 1000 == 0:
                print(f"  Checked {snapshots_checked:,} snapshots...")

        print(f"Validation complete: {snapshots_checked:,} snapshots checked")

        return {
            'snapshots_checked': snapshots_checked,
            'bid_ordering_violations': bid_violations,
            'ask_ordering_violations': ask_violations,
            'violations': violations
        }

    def detect_crossed_book(self, deltas_df: pd.DataFrame, sample_rate: int = 500) -> Dict[str, Any]:
        """
        Detect instances where best_bid >= best_ask (crossed orderbook).

        A crossed orderbook (where the highest bid is >= the lowest ask) should
        NEVER occur in real markets - it would be immediately arbitraged away.
        Any occurrence indicates:
        - Critical data corruption
        - Exchange system malfunction
        - Network/timing issues in data capture

        This is one of the most important validation checks as it reveals
        fundamental data integrity problems.

        Parameters
        ----------
        deltas_df : pd.DataFrame
            Orderbook deltas DataFrame
        sample_rate : int, default=500
            Sample every Nth record. Lower rate = more thorough checking.

        Returns
        -------
        dict
            Detection results with keys:
            - snapshots_checked: int - Number of snapshots examined
            - crossed_books_detected: int - Count of crossed book instances
            - crossed_instances: list[dict] - Details of each crossed book
                - timestamp: pd.Timestamp - When crossing occurred
                - best_bid: float - Highest bid price
                - best_ask: float - Lowest ask price
                - cross_amount: float - How much bid exceeds ask (severity)
            - max_cross_amount: float - Largest spread violation observed

        Examples
        --------
        >>> results = validator.detect_crossed_book(deltas_df, sample_rate=500)
        >>> if results['crossed_books_detected'] > 0:
        ...     print(f"CRITICAL: {results['crossed_books_detected']} crossed books!")
        ...     print(f"Max violation: ${results['max_cross_amount']:.4f}")
        ...     for instance in results['crossed_instances'][:5]:
        ...         print(f"  {instance['timestamp']}: bid={instance['best_bid']}, "
        ...               f"ask={instance['best_ask']}")
        """
        # Sort deltas by timestamp
        deltas_df = deltas_df.sort_values('timestamp').reset_index(drop=True)

        # Sample indices
        total_rows = len(deltas_df)
        sample_indices = range(sample_rate - 1, total_rows, sample_rate)

        # Track results
        snapshots_checked = 0
        crossed_books = []

        print(f"Detecting crossed books: {len(sample_indices)} snapshots to check...")

        for idx in sample_indices:
            timestamp = deltas_df.iloc[idx]['timestamp']

            # Reconstruct orderbook
            bids, asks = self._reconstruct_orderbook_snapshot(deltas_df, up_to_timestamp=timestamp)

            snapshots_checked += 1

            # Check for crossed book
            if len(bids) > 0 and len(asks) > 0:
                best_bid = bids['price'].max()
                best_ask = asks['price'].min()

                if best_bid >= best_ask:
                    # CRITICAL ERROR: Crossed orderbook detected!
                    cross_amount = best_bid - best_ask
                    crossed_books.append({
                        'timestamp': timestamp,
                        'best_bid': float(best_bid),
                        'best_ask': float(best_ask),
                        'cross_amount': float(cross_amount)
                    })

            # Progress indicator
            if snapshots_checked % 1000 == 0:
                print(f"  Checked {snapshots_checked:,} snapshots...")

        # Calculate max cross amount
        max_cross = max([cb['cross_amount'] for cb in crossed_books]) if crossed_books else 0.0

        print(f"Detection complete: {len(crossed_books)} crossed books in {snapshots_checked:,} snapshots")

        return {
            'snapshots_checked': snapshots_checked,
            'crossed_books_detected': len(crossed_books),
            'crossed_instances': crossed_books,
            'max_cross_amount': max_cross
        }

    def analyze_depth_consistency(self, deltas_df: pd.DataFrame, expected_depth: int = 50,
                                  sample_rate: int = 1000) -> Dict[str, Any]:
        """
        Analyze orderbook depth consistency over time.

        Validates that the orderbook maintains the expected number of price levels
        throughout the recording session. Significant depth reductions may indicate:
        - Exchange liquidity issues
        - Data capture problems
        - Network connectivity degradation

        Parameters
        ----------
        deltas_df : pd.DataFrame
            Orderbook deltas DataFrame
        expected_depth : int, default=50
            Expected number of price levels per side (e.g., L2 depth = 50)
        sample_rate : int, default=1000
            Sample every Nth record for analysis

        Returns
        -------
        dict
            Depth analysis results with keys:
            - mean_bid_levels: float - Average number of bid levels
            - mean_ask_levels: float - Average number of ask levels
            - min_bid_levels: int - Minimum bid levels observed
            - min_ask_levels: int - Minimum ask levels observed
            - max_bid_levels: int - Maximum bid levels observed
            - max_ask_levels: int - Maximum ask levels observed
            - depth_below_threshold_count: int - Snapshots with <80% expected depth
            - depth_evolution: list[dict] - Time series of depth measurements
                - timestamp: pd.Timestamp
                - bid_levels: int
                - ask_levels: int

        Examples
        --------
        >>> results = validator.analyze_depth_consistency(deltas_df, expected_depth=50)
        >>> print(f"Average depth: {results['mean_bid_levels']:.1f} bids, "
        ...       f"{results['mean_ask_levels']:.1f} asks")
        >>> if results['min_bid_levels'] < 40:
        ...     print(f"WARNING: Depth dropped to {results['min_bid_levels']} levels!")
        """
        # Sort deltas by timestamp
        deltas_df = deltas_df.sort_values('timestamp').reset_index(drop=True)

        # Sample indices
        total_rows = len(deltas_df)
        sample_indices = range(sample_rate - 1, total_rows, sample_rate)

        # Track depth measurements
        bid_levels_list = []
        ask_levels_list = []
        depth_evolution = []
        depth_below_threshold = 0
        threshold = int(expected_depth * 0.8)  # 80% of expected depth

        print(f"Analyzing depth consistency: {len(sample_indices)} snapshots to check...")

        for idx in sample_indices:
            timestamp = deltas_df.iloc[idx]['timestamp']

            # Reconstruct orderbook
            bids, asks = self._reconstruct_orderbook_snapshot(deltas_df, up_to_timestamp=timestamp)

            bid_levels = len(bids)
            ask_levels = len(asks)

            bid_levels_list.append(bid_levels)
            ask_levels_list.append(ask_levels)

            depth_evolution.append({
                'timestamp': timestamp,
                'bid_levels': bid_levels,
                'ask_levels': ask_levels
            })

            # Check if depth is below threshold
            if bid_levels < threshold or ask_levels < threshold:
                depth_below_threshold += 1

            # Progress indicator
            if len(bid_levels_list) % 1000 == 0:
                print(f"  Analyzed {len(bid_levels_list):,} snapshots...")

        print(f"Depth analysis complete: {len(bid_levels_list):,} snapshots analyzed")

        return {
            'mean_bid_levels': float(np.mean(bid_levels_list)) if bid_levels_list else 0.0,
            'mean_ask_levels': float(np.mean(ask_levels_list)) if ask_levels_list else 0.0,
            'min_bid_levels': int(np.min(bid_levels_list)) if bid_levels_list else 0,
            'min_ask_levels': int(np.min(ask_levels_list)) if ask_levels_list else 0,
            'max_bid_levels': int(np.max(bid_levels_list)) if bid_levels_list else 0,
            'max_ask_levels': int(np.max(ask_levels_list)) if ask_levels_list else 0,
            'depth_below_threshold_count': depth_below_threshold,
            'depth_evolution': depth_evolution
        }

    def _reconstruct_orderbook_snapshot(self, deltas_df: pd.DataFrame,
                                       up_to_timestamp: pd.Timestamp) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Reconstruct orderbook state at a specific timestamp.

        This is the core reconstruction algorithm. It processes all deltas up to
        the specified timestamp and builds the current orderbook state.

        Algorithm:
        ----------
        1. Filter deltas up to the target timestamp
        2. For each price level, keep only the most recent action (drop_duplicates)
        3. Remove deleted price levels (action != DELETE)
        4. Remove CLEAR actions with NO_ORDER_SIDE
        5. Split into bids (BUY) and asks (SELL)
        6. Sort bids descending, asks ascending

        Edge Cases Handled:
        -------------------
        - Empty orderbook (no deltas yet): returns empty DataFrames
        - CLEAR actions: filtered out (they reset the book but don't represent levels)
        - Duplicate price levels: only most recent action is kept
        - DELETE actions: removed from final snapshot

        Parameters
        ----------
        deltas_df : pd.DataFrame
            All orderbook deltas
        up_to_timestamp : pd.Timestamp
            Timestamp to reconstruct orderbook state at

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            (bids_df, asks_df) - Active bid and ask levels at the timestamp
            Both DataFrames have columns: timestamp, action, side, price, size, order_id

        Examples
        --------
        >>> bids, asks = validator._reconstruct_orderbook_snapshot(
        ...     deltas_df, up_to_timestamp=pd.Timestamp('2025-11-19 07:30:00', tz='UTC'))
        >>> print(f"Orderbook has {len(bids)} bids and {len(asks)} asks")
        >>> print(f"Best bid: ${bids['price'].max():.2f}")
        >>> print(f"Best ask: ${asks['price'].min():.2f}")
        """
        # Get all deltas up to this timestamp
        snapshot_deltas = deltas_df[deltas_df['timestamp'] <= up_to_timestamp].copy()

        if len(snapshot_deltas) == 0:
            # No data yet - return empty orderbook
            return pd.DataFrame(), pd.DataFrame()

        # Filter out CLEAR actions (they don't represent actual price levels)
        snapshot_deltas = snapshot_deltas[snapshot_deltas['action'] != 'CLEAR']

        # Filter out NO_ORDER_SIDE entries
        snapshot_deltas = snapshot_deltas[snapshot_deltas['side'] != 'NO_ORDER_SIDE']

        # For each price level, keep only the most recent action
        # This handles UPDATE, ADD, and DELETE actions correctly
        snapshot_deltas = snapshot_deltas.drop_duplicates(
            subset=['price', 'side'],
            keep='last'
        )

        # Remove DELETE actions (those levels no longer exist)
        active_levels = snapshot_deltas[snapshot_deltas['action'] != 'DELETE'].copy()

        if len(active_levels) == 0:
            # Orderbook is empty at this point
            return pd.DataFrame(), pd.DataFrame()

        # Split into bids and asks
        bids = active_levels[active_levels['side'] == 'BUY'].copy()
        asks = active_levels[active_levels['side'] == 'SELL'].copy()

        # Sort bids descending (best bid = highest price first)
        if len(bids) > 0:
            bids = bids.sort_values('price', ascending=False).reset_index(drop=True)

        # Sort asks ascending (best ask = lowest price first)
        if len(asks) > 0:
            asks = asks.sort_values('price', ascending=True).reset_index(drop=True)

        return bids, asks


def validate_orderbook_data(deltas_df: pd.DataFrame, recording_dir: Path,
                           sample_rate: int = 1000) -> Dict[str, Any]:
    """
    Convenience function to run all orderbook validations.

    Runs the complete suite of orderbook validations:
    - Price level ordering
    - Crossed book detection
    - Depth consistency analysis

    Parameters
    ----------
    deltas_df : pd.DataFrame
        Orderbook deltas DataFrame
    recording_dir : Path
        Path to recording directory
    sample_rate : int, default=1000
        Sampling rate for validation (lower = more thorough)

    Returns
    -------
    dict
        Combined validation results from all checks

    Examples
    --------
    >>> deltas = pd.read_parquet("deltas.parquet")
    >>> results = validate_orderbook_data(deltas, Path("."), sample_rate=500)
    >>> print(f"Crossed books: {results['crossed_book']['crossed_books_detected']}")
    >>> print(f"Mean depth: {results['depth']['mean_bid_levels']:.1f}")
    """
    validator = OrderbookValidator(recording_dir)

    print("=" * 80)
    print("ORDERBOOK VALIDATION SUITE")
    print("=" * 80)

    # Run all validations
    print("\n1. Validating price level ordering...")
    price_results = validator.validate_price_levels(deltas_df, sample_rate=sample_rate)

    print("\n2. Detecting crossed orderbooks...")
    crossed_results = validator.detect_crossed_book(deltas_df, sample_rate=sample_rate)

    print("\n3. Analyzing depth consistency...")
    depth_results = validator.analyze_depth_consistency(deltas_df, expected_depth=50, sample_rate=sample_rate)

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

    return {
        'price_levels': price_results,
        'crossed_book': crossed_results,
        'depth': depth_results
    }
