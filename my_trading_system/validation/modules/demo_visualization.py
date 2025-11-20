#!/usr/bin/env python3
"""
Visualization Module Demo Script

Trading Engines Project - Validation Framework
Location: my_trading_system/validation/modules/demo_visualization.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-19

Demonstrates the visualization module capabilities with sample data.

Usage:
    python demo_visualization.py

This will generate:
- price_timeseries.png: Bid/ask prices with trade execution overlay
- spread_distribution.png: Bid-ask spread histogram and box plot
- volume_profile.png: Volume by price level and time
- orderbook_heatmap.html: Interactive orderbook depth evolution

All outputs saved to: ./demo_visualizations/
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from my_trading_system.validation.modules import DataVisualizer, create_all_visualizations


def generate_sample_data(n_quotes=5000, n_trades=500, n_deltas=2000):
    """
    Generate sample market data for demonstration.

    Parameters
    ----------
    n_quotes : int
        Number of quote ticks to generate
    n_trades : int
        Number of trade ticks to generate
    n_deltas : int
        Number of orderbook deltas to generate

    Returns
    -------
    tuple
        (quotes_df, trades_df, deltas_df)
    """
    print(f"Generating sample data...")
    print(f"  - Quotes: {n_quotes:,} rows")
    print(f"  - Trades: {n_trades:,} rows")
    print(f"  - Deltas: {n_deltas:,} rows")

    # Generate realistic price walk
    base_price = 139.50
    price_walk = np.random.randn(n_quotes).cumsum() * 0.01

    quotes_df = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n_quotes, freq='1s', tz='UTC'),
        'bid_price': base_price + price_walk,
        'ask_price': base_price + 0.02 + price_walk + np.random.uniform(0, 0.01, n_quotes),
        'bid_size': np.random.uniform(10, 100, n_quotes),
        'ask_size': np.random.uniform(10, 100, n_quotes)
    })

    # Generate trades at mid-price
    trade_times = pd.date_range('2025-01-01', periods=n_trades, freq='10s', tz='UTC')
    trade_price_walk = np.random.randn(n_trades).cumsum() * 0.01

    trades_df = pd.DataFrame({
        'timestamp': trade_times,
        'price': base_price + 0.01 + trade_price_walk + np.random.uniform(-0.005, 0.005, n_trades),
        'size': np.random.uniform(1, 20, n_trades),
        'side': np.random.choice(['BUYER', 'SELLER'], n_trades)
    })

    # Generate orderbook deltas
    deltas_df = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n_deltas, freq='2.5s', tz='UTC'),
        'action': np.random.choice(['ADD', 'UPDATE', 'DELETE'], n_deltas, p=[0.5, 0.3, 0.2]),
        'side': np.random.choice(['BID', 'ASK'], n_deltas),
        'price': np.random.uniform(base_price - 0.5, base_price + 0.5, n_deltas),
        'size': np.random.uniform(1, 50, n_deltas),
        'order_id': np.arange(n_deltas)
    })

    print("✅ Sample data generated")
    return quotes_df, trades_df, deltas_df


def demo_individual_methods():
    """Demonstrate individual visualization methods."""
    print("\n" + "="*70)
    print("DEMO 1: Individual Visualization Methods")
    print("="*70 + "\n")

    # Generate sample data
    quotes_df, trades_df, deltas_df = generate_sample_data()

    # Initialize visualizer
    output_dir = Path('./demo_visualizations/individual')
    recording_dir = Path('.')

    visualizer = DataVisualizer(recording_dir, output_dir)

    print(f"\nGenerating visualizations...")
    print(f"Output directory: {output_dir.absolute()}\n")

    # 1. Price timeseries
    print("1. Generating price timeseries...")
    price_plot = visualizer.plot_price_timeseries(quotes_df, trades_df)
    print(f"   ✅ Saved: {price_plot}\n")

    # 2. Spread distribution
    print("2. Generating spread distribution...")
    spread_plot = visualizer.plot_spread_distribution(quotes_df)
    print(f"   ✅ Saved: {spread_plot}\n")

    # 3. Volume profile
    print("3. Generating volume profile...")
    volume_plot = visualizer.plot_volume_profile(trades_df)
    print(f"   ✅ Saved: {volume_plot}\n")

    # 4. Orderbook heatmap
    print("4. Generating orderbook heatmap...")
    heatmap_plot = visualizer.plot_orderbook_heatmap(deltas_df, sample_rate=50)
    print(f"   ✅ Saved: {heatmap_plot}\n")

    print("✅ All individual visualizations completed!")


def demo_convenience_function():
    """Demonstrate the convenience function for generating all charts."""
    print("\n" + "="*70)
    print("DEMO 2: Convenience Function (create_all_visualizations)")
    print("="*70 + "\n")

    # Generate sample data
    quotes_df, trades_df, deltas_df = generate_sample_data(
        n_quotes=10000,
        n_trades=1000,
        n_deltas=5000
    )

    # Use convenience function
    output_dir = Path('./demo_visualizations/convenience')
    recording_dir = Path('.')

    print(f"\nGenerating all visualizations using convenience function...")
    print(f"Output directory: {output_dir.absolute()}\n")

    import time
    start = time.time()

    charts = create_all_visualizations(
        quotes_df=quotes_df,
        trades_df=trades_df,
        deltas_df=deltas_df,
        output_dir=output_dir,
        recording_dir=recording_dir
    )

    elapsed = time.time() - start

    print("\n✅ All visualizations completed!")
    print(f"\n📊 Generated charts:")
    for name, path in charts.items():
        print(f"   - {name}: {path}")

    print(f"\n⚡ Total execution time: {elapsed:.2f} seconds")


def demo_large_dataset():
    """Demonstrate performance with large dataset."""
    print("\n" + "="*70)
    print("DEMO 3: Large Dataset Performance Test")
    print("="*70 + "\n")

    # Generate large dataset
    print("Generating large dataset (testing downsampling)...")
    quotes_df, trades_df, deltas_df = generate_sample_data(
        n_quotes=100000,
        n_trades=50000,
        n_deltas=200000
    )

    # Use convenience function
    output_dir = Path('./demo_visualizations/large_dataset')
    recording_dir = Path('.')

    print(f"\nGenerating visualizations with automatic downsampling...")
    print(f"Output directory: {output_dir.absolute()}\n")

    import time
    start = time.time()

    charts = create_all_visualizations(
        quotes_df=quotes_df,
        trades_df=trades_df,
        deltas_df=deltas_df,
        output_dir=output_dir,
        recording_dir=recording_dir
    )

    elapsed = time.time() - start

    print("\n✅ Large dataset visualizations completed!")
    print(f"\n📊 Generated charts:")
    for name, path in charts.items():
        file_size = Path(path).stat().st_size / 1024
        print(f"   - {name}: {file_size:.1f} KB")

    print(f"\n⚡ Total execution time: {elapsed:.2f} seconds")

    if elapsed < 60:
        print("✅ Performance requirement met: <60 seconds")
    else:
        print("⚠️  Performance exceeded target")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("VISUALIZATION MODULE DEMONSTRATION")
    print("Trading Engines Project - Validation Framework")
    print("="*70)

    try:
        # Demo 1: Individual methods
        demo_individual_methods()

        # Demo 2: Convenience function
        demo_convenience_function()

        # Demo 3: Large dataset
        demo_large_dataset()

        print("\n" + "="*70)
        print("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        print("="*70)
        print(f"\n📁 All outputs saved to: ./demo_visualizations/")
        print("\nYou can now:")
        print("  1. View PNG files with any image viewer")
        print("  2. Open HTML files in a web browser for interactive charts")
        print("  3. Embed these charts in validation reports")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
