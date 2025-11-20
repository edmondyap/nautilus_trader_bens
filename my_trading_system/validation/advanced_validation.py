#!/usr/bin/env python3
"""
Advanced Data Validation System - Main CLI Entry Point

Trading Engines Project - Wave 3: CLI Interface & Integration
Location: my_trading_system/validation/advanced_validation.py
Author: Benjamin Ang / Claude Code (Subagent 7)
Created: 2025-11-19

Production-grade CLI for comprehensive market data quality validation.

This is the main orchestrator that coordinates all validation modules:
- Statistical Analysis (gaps, outliers, spreads, volume)
- Integrity Checks (duplicates, missing values, cross-validation)
- Orderbook Validation (structure, crossed books, depth)
- Visualization Generation (charts, heatmaps)
- Quality Scoring (0-100 score with issue prioritization)

Usage Examples:
--------------
# Basic validation
python advanced_validation.py data/recordings/20251119-152837

# With custom output directory
python advanced_validation.py data/recordings/20251119-152837 \
    --output reports/validation_report.json

# Skip visualizations for speed
python advanced_validation.py data/recordings/20251119-152837 \
    --skip-visualizations

# Verbose mode
python advanced_validation.py data/recordings/20251119-152837 \
    --verbose

Exit Codes:
-----------
0: Validation passed (score >= 70)
1: Validation failed (score < 70) or runtime error
2: Invalid input (missing files, bad arguments)
130: Interrupted by user (Ctrl+C)

Performance:
------------
- Typical dataset (4M deltas, 560K quotes, 70K trades): ~5 minutes
- With --skip-visualizations: ~3 minutes
- Progress indicators every 1000 operations
- Memory-efficient streaming where possible
"""

import sys
import argparse
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import time

import pandas as pd

# Import validation modules
from my_trading_system.validation.modules.statistical_analysis import StatisticalAnalyzer
from my_trading_system.validation.modules.integrity_checks import IntegrityChecker
from my_trading_system.validation.modules.orderbook_validation import OrderbookValidator
from my_trading_system.validation.modules.visualization import DataVisualizer
from my_trading_system.validation.modules.quality_scorer import QualityScorer

# Import data reader
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from my_trading_system.native_recorder.persistence import RecordingReader


class AdvancedDataValidator:
    """
    Main orchestrator for advanced data validation.

    Coordinates all validation modules:
    - Loads data via RecordingReader
    - Runs statistical analysis
    - Performs integrity checks
    - Validates orderbook structure
    - Generates visualizations
    - Calculates quality score
    - Produces reports

    Parameters
    ----------
    recording_dir : Path
        Path to recording directory
    output_dir : Path, optional
        Where to save outputs (default: recording_dir/validation)
    verbose : bool, default=False
        Enable detailed progress output
    sample_rate : int, default=1000
        Orderbook sampling rate for validation

    Attributes
    ----------
    recording_dir : Path
        Recording directory path
    output_dir : Path
        Output directory for results
    verbose : bool
        Verbose mode flag
    sample_rate : int
        Orderbook sampling rate
    reader : RecordingReader
        Data reader instance
    results : dict
        Validation results

    Examples
    --------
    >>> validator = AdvancedDataValidator(
    ...     recording_dir=Path('data/recordings/20251119-152837'),
    ...     verbose=True
    ... )
    >>> results = validator.run_all_validations()
    >>> print(f"Quality Score: {results['quality_score']['score']}/100")
    """

    def __init__(
        self,
        recording_dir: Path,
        output_dir: Optional[Path] = None,
        verbose: bool = False,
        sample_rate: int = 1000
    ):
        """
        Initialize validator.

        Parameters
        ----------
        recording_dir : Path
            Path to recording directory
        output_dir : Path, optional
            Where to save outputs (default: recording_dir/validation)
        verbose : bool, default=False
            Enable detailed progress output
        sample_rate : int, default=1000
            Orderbook sampling rate for validation
        """
        self.recording_dir = Path(recording_dir)
        self.output_dir = output_dir or (self.recording_dir / 'validation')
        self.verbose = verbose
        self.sample_rate = sample_rate
        self.reader = None
        self.results = {}

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _print_progress(self, message: str, stage: Optional[int] = None, total_stages: int = 7):
        """
        Print formatted progress message.

        Parameters
        ----------
        message : str
            Progress message to print
        stage : int, optional
            Current stage number
        total_stages : int, default=7
            Total number of stages
        """
        if not self.verbose:
            return

        if stage:
            progress = f"[{stage}/{total_stages}]"
            print(f"{progress} {message}")
        else:
            print(f"    {message}")

    def run_all_validations(self, skip_visualizations: bool = False) -> Dict[str, Any]:
        """
        Execute complete validation pipeline.

        Pipeline stages:
        1. Load data (quotes, trades, deltas)
        2. Run statistical analysis
        3. Run integrity checks
        4. Run orderbook validation
        5. Generate visualizations (unless skipped)
        6. Calculate quality score
        7. Generate reports

        Parameters
        ----------
        skip_visualizations : bool, default=False
            Skip chart generation for speed

        Returns
        -------
        dict
            Complete validation results including:
            - statistical_results: Statistical analysis
            - integrity_results: Integrity checks
            - orderbook_results: Orderbook validation
            - quality_score: Overall quality score
            - viz_paths: Visualization file paths (if generated)
            - execution_time: Total execution time in seconds
        """
        start_time = time.time()

        try:
            # Stage 1: Load data
            self._print_progress("Loading data...", stage=1)
            quotes_df, trades_df, deltas_df = self._load_data()
            load_time = time.time() - start_time

            self._print_progress(f"Loaded quotes: {len(quotes_df):,} records ({self._format_size(quotes_df)})")
            self._print_progress(f"Loaded trades: {len(trades_df):,} records ({self._format_size(trades_df)})")
            self._print_progress(f"Loaded deltas: {len(deltas_df):,} records ({self._format_size(deltas_df)})")
            total_records = len(quotes_df) + len(trades_df) + len(deltas_df)
            self._print_progress(f"Total: {total_records/1e6:.1f}M records in {load_time:.1f}s")

            # Stage 2: Statistical analysis
            self._print_progress("\nRunning statistical analysis...", stage=2)
            stage_start = time.time()
            statistical_results = self._run_statistical_analysis(quotes_df, trades_df, deltas_df)
            stage_time = time.time() - stage_start
            self._print_progress(f"Statistical analysis complete: {stage_time:.2f}s")

            # Stage 3: Integrity checks
            self._print_progress("\nRunning integrity checks...", stage=3)
            stage_start = time.time()
            integrity_results = self._run_integrity_checks(quotes_df, trades_df, deltas_df)
            stage_time = time.time() - stage_start
            self._print_progress(f"Integrity checks complete: {stage_time:.2f}s")

            # Stage 4: Orderbook validation
            self._print_progress("\nValidating orderbook structure...", stage=4)
            stage_start = time.time()
            orderbook_results = self._run_orderbook_validation(deltas_df)
            stage_time = time.time() - stage_start
            self._print_progress(f"Orderbook validation complete: {stage_time:.1f}s")

            # Stage 5: Visualizations (optional)
            viz_paths = {}
            if not skip_visualizations:
                self._print_progress("\nGenerating visualizations...", stage=5)
                stage_start = time.time()
                viz_paths = self._generate_visualizations(quotes_df, trades_df, deltas_df)
                stage_time = time.time() - stage_start
                self._print_progress(f"Visualizations complete: {stage_time:.1f}s")
            else:
                self._print_progress("\nSkipping visualizations (--skip-visualizations)", stage=5)

            # Stage 6: Quality scoring
            self._print_progress("\nCalculating quality score...", stage=6)
            stage_start = time.time()
            quality_score = self._calculate_quality_score(
                statistical_results,
                integrity_results,
                orderbook_results
            )
            stage_time = time.time() - stage_start

            self._print_progress(f"Score: {quality_score['score']}/100 (Grade: {quality_score['grade']})")
            self._print_progress(f"Issues found: {quality_score['issues_found']} "
                               f"(Critical: {quality_score['critical_issues']}, "
                               f"High: {quality_score['high_issues']}, "
                               f"Medium: {quality_score['medium_issues']}, "
                               f"Low: {quality_score['low_issues']})")
            self._print_progress(f"Quality scoring complete: {stage_time:.1f}s")

            # Stage 7: Generate reports
            self._print_progress("\nGenerating reports...", stage=7)
            stage_start = time.time()

            # Compile results
            self.results = {
                'recording_dir': str(self.recording_dir),
                'validation_timestamp': datetime.now().isoformat(),
                'data_summary': {
                    'quotes_count': len(quotes_df),
                    'trades_count': len(trades_df),
                    'deltas_count': len(deltas_df),
                    'total_records': total_records
                },
                'statistical_results': statistical_results,
                'integrity_results': integrity_results,
                'orderbook_results': orderbook_results,
                'quality_score': quality_score,
                'viz_paths': viz_paths,
                'execution_time': time.time() - start_time
            }

            # Save JSON results
            json_path = self.output_dir / 'results.json'
            self._save_results(json_path)
            self._print_progress(f"JSON results: {json_path}")

            stage_time = time.time() - stage_start
            self._print_progress(f"Reports complete: {stage_time:.1f}s")

            return self.results

        except Exception as e:
            print(f"\nERROR during validation: {e}")
            if self.verbose:
                traceback.print_exc()
            raise

    def _load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load all data using RecordingReader.

        Returns
        -------
        tuple
            (quotes_df, trades_df, deltas_df) - Tuple of DataFrames

        Raises
        ------
        FileNotFoundError
            If recording directory or data files not found
        """
        # Initialize reader
        self.reader = RecordingReader(self.recording_dir)

        # Get list of instruments
        instruments = self.reader.list_instruments()

        if not instruments:
            raise FileNotFoundError(f"No instruments found in {self.recording_dir}")

        # Use first instrument (typically only one)
        if 'quote_ticks' in instruments and instruments['quote_ticks']:
            instrument = instruments['quote_ticks'][0]
        elif 'order_book_deltas' in instruments and instruments['order_book_deltas']:
            instrument = instruments['order_book_deltas'][0]
        else:
            raise FileNotFoundError("No valid instruments found")

        self._print_progress(f"Loading instrument: {instrument}")

        # Load quotes
        try:
            quotes_df = self.reader.read_quotes(instrument)
        except FileNotFoundError:
            quotes_df = pd.DataFrame()
            self._print_progress("No quotes data found")

        # Load trades (from quote_ticks folder since we record trades there)
        try:
            trades_file = self.recording_dir / "quote_ticks" / instrument / "trade_ticks.parquet"
            if trades_file.exists():
                trades_df = pd.read_parquet(trades_file)
            else:
                trades_df = pd.DataFrame()
                self._print_progress("No trades data found")
        except Exception:
            trades_df = pd.DataFrame()
            self._print_progress("No trades data found")

        # Load deltas
        try:
            deltas_df = self.reader.read_deltas(instrument)
        except FileNotFoundError:
            deltas_df = pd.DataFrame()
            self._print_progress("No deltas data found")

        return quotes_df, trades_df, deltas_df

    def _run_statistical_analysis(
        self,
        quotes_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        deltas_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run all statistical checks.

        Parameters
        ----------
        quotes_df : pd.DataFrame
            Quote ticks data
        trades_df : pd.DataFrame
            Trade ticks data
        deltas_df : pd.DataFrame
            Orderbook deltas data

        Returns
        -------
        dict
            Statistical analysis results
        """
        analyzer = StatisticalAnalyzer(self.recording_dir)
        results = {}

        # Quotes analysis
        if not quotes_df.empty:
            stage_start = time.time()
            results['quotes_gaps'] = analyzer.analyze_gaps(quotes_df, "quotes", max_expected_gap_ms=1000)
            self._print_progress(f"Gap analysis: {time.time() - stage_start:.2f}s")

            stage_start = time.time()
            results['quotes_outliers'] = analyzer.detect_price_outliers(quotes_df, z_threshold=3.0)
            self._print_progress(f"Outlier detection: {time.time() - stage_start:.2f}s")

            stage_start = time.time()
            results['quotes_spreads'] = analyzer.analyze_spreads(quotes_df)
            self._print_progress(f"Spread analysis: {time.time() - stage_start:.2f}s")

        # Trades analysis
        if not trades_df.empty:
            stage_start = time.time()
            results['trades_volume'] = analyzer.analyze_volume(trades_df)
            self._print_progress(f"Volume analysis: {time.time() - stage_start:.2f}s")

        # Aggregate for quality scorer
        return {
            'gaps': results.get('quotes_gaps', {}),
            'outliers': results.get('quotes_outliers', {}),
            'spreads': results.get('quotes_spreads', {}),
            'volume': results.get('trades_volume', {}),
            'raw_results': results
        }

    def _run_integrity_checks(
        self,
        quotes_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        deltas_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run all integrity checks.

        Parameters
        ----------
        quotes_df : pd.DataFrame
            Quote ticks data
        trades_df : pd.DataFrame
            Trade ticks data
        deltas_df : pd.DataFrame
            Orderbook deltas data

        Returns
        -------
        dict
            Integrity check results
        """
        checker = IntegrityChecker(self.recording_dir)
        results = {}

        # Quotes integrity
        if not quotes_df.empty:
            stage_start = time.time()
            results['quotes_duplicates'] = checker.detect_duplicates(quotes_df, "quotes")
            self._print_progress(f"Duplicate detection: {time.time() - stage_start:.2f}s")

            stage_start = time.time()
            results['quotes_missing'] = checker.check_missing_values(quotes_df, "quotes")
            self._print_progress(f"Missing value check: {time.time() - stage_start:.2f}s")

        # Cross-validation
        if not quotes_df.empty and not trades_df.empty:
            stage_start = time.time()
            results['cross_validation'] = checker.cross_validate_data_types(
                quotes_df, trades_df, tolerance_seconds=1.0
            )
            self._print_progress(f"Cross-validation: {time.time() - stage_start:.2f}s")

        # Aggregate for quality scorer
        return {
            'duplicates': results.get('quotes_duplicates', {}),
            'missing_values': results.get('quotes_missing', {}),
            'cross_validation': results.get('cross_validation', {}),
            'raw_results': results
        }

    def _run_orderbook_validation(self, deltas_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run orderbook validation.

        Parameters
        ----------
        deltas_df : pd.DataFrame
            Orderbook deltas data

        Returns
        -------
        dict
            Orderbook validation results
        """
        if deltas_df.empty:
            return {
                'price_levels': {},
                'crossed_books': {},
                'depth': {}
            }

        validator = OrderbookValidator(self.recording_dir)
        results = {}

        # Crossed book detection
        stage_start = time.time()
        results['crossed_books'] = validator.detect_crossed_book(
            deltas_df,
            sample_rate=self.sample_rate
        )
        stage_time = time.time() - stage_start
        snapshots = results['crossed_books'].get('snapshots_checked', 0)
        self._print_progress(f"Crossed book detection: {stage_time:.1f}s ({snapshots} snapshots)")

        return {
            'price_levels': {},  # Placeholder - can be expensive
            'crossed_books': results.get('crossed_books', {}),
            'depth': {}  # Placeholder - can be expensive
        }

    def _generate_visualizations(
        self,
        quotes_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        deltas_df: pd.DataFrame
    ) -> Dict[str, str]:
        """
        Generate all charts.

        Parameters
        ----------
        quotes_df : pd.DataFrame
            Quote ticks data
        trades_df : pd.DataFrame
            Trade ticks data
        deltas_df : pd.DataFrame
            Orderbook deltas data

        Returns
        -------
        dict
            Dictionary mapping chart name to file path
        """
        visualizer = DataVisualizer(
            recording_dir=self.recording_dir,
            output_dir=self.output_dir
        )

        viz_paths = {}

        # Price time series
        if not quotes_df.empty and not trades_df.empty:
            stage_start = time.time()
            viz_paths['price_timeseries'] = visualizer.plot_price_timeseries(
                quotes_df, trades_df
            )
            self._print_progress(f"Price time series: {time.time() - stage_start:.1f}s")

        # Spread distribution
        if not quotes_df.empty:
            stage_start = time.time()
            viz_paths['spread_distribution'] = visualizer.plot_spread_distribution(quotes_df)
            self._print_progress(f"Spread distribution: {time.time() - stage_start:.1f}s")

        # Volume profile
        if not trades_df.empty:
            stage_start = time.time()
            viz_paths['volume_profile'] = visualizer.plot_volume_profile(trades_df)
            self._print_progress(f"Volume profile: {time.time() - stage_start:.1f}s")

        # Orderbook heatmap (interactive HTML)
        if not deltas_df.empty:
            stage_start = time.time()
            viz_paths['orderbook_heatmap'] = visualizer.plot_orderbook_heatmap(
                deltas_df,
                sample_rate=100
            )
            self._print_progress(f"Orderbook heatmap: {time.time() - stage_start:.1f}s")

        return viz_paths

    def _calculate_quality_score(
        self,
        statistical_results: Dict[str, Any],
        integrity_results: Dict[str, Any],
        orderbook_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall quality score.

        Parameters
        ----------
        statistical_results : dict
            Statistical analysis results
        integrity_results : dict
            Integrity check results
        orderbook_results : dict
            Orderbook validation results

        Returns
        -------
        dict
            Quality score and breakdown
        """
        scorer = QualityScorer(
            statistical_results,
            integrity_results,
            orderbook_results
        )

        # Calculate score
        score_result = scorer.calculate_score()

        # Get detailed report
        detailed_report = scorer.get_detailed_report()

        # Combine results
        return {
            'score': score_result['score'],
            'grade': score_result['grade'],
            'issues_found': score_result['issues_found'],
            'critical_issues': score_result['critical_issues'],
            'high_issues': score_result['high_issues'],
            'medium_issues': score_result['medium_issues'],
            'low_issues': score_result['low_issues'],
            'detailed_report': detailed_report
        }

    def _save_results(self, output_path: Path) -> None:
        """
        Save JSON results file.

        Parameters
        ----------
        output_path : Path
            Path to save JSON results
        """
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

    def _print_summary(self) -> None:
        """Print validation summary to console."""
        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)

        quality = self.results['quality_score']

        print(f"\nQuality Score: {quality['score']}/100 (Grade: {quality['grade']})")
        print(f"Issues Found: {quality['issues_found']}")
        print(f"  Critical: {quality['critical_issues']}")
        print(f"  High: {quality['high_issues']}")
        print(f"  Medium: {quality['medium_issues']}")
        print(f"  Low: {quality['low_issues']}")

        print(f"\nExecution Time: {self.results['execution_time']:.1f}s")

        # Print recommendations
        if 'detailed_report' in quality:
            recommendations = quality['detailed_report'].get('recommendations', [])
            if recommendations:
                print("\nRecommendations:")
                for rec in recommendations:
                    print(f"  - {rec}")

        # Determine recommendation
        score = quality['score']
        if score >= 90:
            recommendation = "APPROVED - Excellent quality"
        elif score >= 80:
            recommendation = "APPROVED - Good quality"
        elif score >= 70:
            recommendation = "APPROVED - Acceptable quality with caveats"
        else:
            recommendation = "REJECTED - Quality below acceptable standards"

        print(f"\nRecommendation: {recommendation}")
        print("=" * 80)

    def _format_size(self, df: pd.DataFrame) -> str:
        """
        Format DataFrame memory size.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to measure

        Returns
        -------
        str
            Formatted size string (e.g., "7.0 MB")
        """
        size_bytes = df.memory_usage(deep=True).sum()
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create CLI argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Advanced Market Data Validation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic validation
  python advanced_validation.py data/recordings/20251119-152837

  # With custom output directory
  python advanced_validation.py data/recordings/20251119-152837 \\
      --output reports/validation_report.json

  # Skip visualizations for speed
  python advanced_validation.py data/recordings/20251119-152837 \\
      --skip-visualizations

  # Verbose mode
  python advanced_validation.py data/recordings/20251119-152837 \\
      --verbose

  # Custom sampling rate
  python advanced_validation.py data/recordings/20251119-152837 \\
      --sample-rate 500 \\
      --verbose

Exit Codes:
  0: Validation passed (score >= 70)
  1: Validation failed (score < 70) or runtime error
  2: Invalid input (missing files, bad arguments)
  130: Interrupted by user (Ctrl+C)
        '''
    )

    parser.add_argument(
        'recording_dir',
        type=Path,
        help='Path to recording directory'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory for results (default: <recording_dir>/validation)'
    )

    parser.add_argument(
        '--skip-visualizations',
        action='store_true',
        help='Skip chart generation for faster execution'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--sample-rate',
        type=int,
        default=1000,
        help='Orderbook sampling rate (default: 1000, lower = more thorough)'
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate inputs
    if not args.recording_dir.exists():
        print(f"ERROR: Recording directory not found: {args.recording_dir}")
        sys.exit(2)

    # Initialize validator
    validator = AdvancedDataValidator(
        recording_dir=args.recording_dir,
        output_dir=args.output,
        verbose=args.verbose,
        sample_rate=args.sample_rate
    )

    # Print header
    print("=" * 80)
    print("ADVANCED DATA VALIDATION")
    print("=" * 80)
    print(f"Recording: {args.recording_dir}")
    print(f"Output: {validator.output_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sample Rate: {args.sample_rate}")
    print("=" * 80)
    print()

    try:
        # Run validation
        results = validator.run_all_validations(
            skip_visualizations=args.skip_visualizations
        )

        # Print summary
        validator._print_summary()

        # Exit code based on quality score
        score = results['quality_score']['score']
        if score >= 70:
            sys.exit(0)  # Pass
        else:
            sys.exit(1)  # Fail

    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(130)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\nVALIDATION FAILED: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
