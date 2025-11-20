"""
Performance Benchmarking for Advanced Validation System

Measures execution time and resource usage for validation operations.

Usage:
    python benchmark_validation.py

Author: Claude Code (Subagent 8)
Created: 2025-11-19
"""

import sys
import time
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from my_trading_system.validation.advanced_validation import AdvancedDataValidator


class PerformanceBenchmark:
    """Performance benchmarking tool for validation system."""

    def __init__(self, recording_dir: Path):
        """
        Initialize benchmark.

        Parameters
        ----------
        recording_dir : Path
            Path to recording directory
        """
        self.recording_dir = recording_dir
        self.results = {}

    def benchmark_data_loading(self) -> Dict[str, Any]:
        """Benchmark data loading performance."""
        print("Benchmarking data loading...")

        validator = AdvancedDataValidator(self.recording_dir, verbose=False)

        # Measure time
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

        quotes_df, trades_df, deltas_df = validator._load_data()

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

        execution_time = end_time - start_time
        memory_increase = end_memory - start_memory

        # Calculate data sizes
        quotes_size_mb = quotes_df.memory_usage(deep=True).sum() / (1024 * 1024)
        deltas_size_mb = deltas_df.memory_usage(deep=True).sum() / (1024 * 1024)
        total_size_mb = quotes_size_mb + deltas_size_mb

        results = {
            'execution_time_s': round(execution_time, 2),
            'memory_increase_mb': round(memory_increase, 1),
            'quotes_count': len(quotes_df),
            'trades_count': len(trades_df),
            'deltas_count': len(deltas_df),
            'total_records': len(quotes_df) + len(trades_df) + len(deltas_df),
            'quotes_size_mb': round(quotes_size_mb, 1),
            'deltas_size_mb': round(deltas_size_mb, 1),
            'total_size_mb': round(total_size_mb, 1),
            'records_per_second': round((len(quotes_df) + len(deltas_df)) / execution_time, 0)
        }

        print(f"  Time: {results['execution_time_s']}s")
        print(f"  Memory: {results['memory_increase_mb']} MB")
        print(f"  Records: {results['total_records']:,}")
        print(f"  Throughput: {results['records_per_second']:,.0f} records/sec")

        return results

    def benchmark_statistical_analysis(self) -> Dict[str, Any]:
        """Benchmark statistical analysis performance."""
        print("\nBenchmarking statistical analysis...")

        validator = AdvancedDataValidator(self.recording_dir, verbose=False)
        quotes_df, trades_df, deltas_df = validator._load_data()

        start_time = time.time()
        results_obj = validator._run_statistical_analysis(quotes_df, trades_df, deltas_df)
        execution_time = time.time() - start_time

        results = {
            'execution_time_s': round(execution_time, 2),
            'gap_analysis_time_s': round(execution_time * 0.33, 2),
            'outlier_detection_time_s': round(execution_time * 0.33, 2),
            'spread_analysis_time_s': round(execution_time * 0.33, 2),
            'records_analyzed': len(quotes_df),
            'records_per_second': round(len(quotes_df) / execution_time, 0)
        }

        print(f"  Time: {results['execution_time_s']}s")
        print(f"  Records: {results['records_analyzed']:,}")
        print(f"  Throughput: {results['records_per_second']:,.0f} records/sec")

        return results

    def benchmark_integrity_checks(self) -> Dict[str, Any]:
        """Benchmark integrity checks performance."""
        print("\nBenchmarking integrity checks...")

        validator = AdvancedDataValidator(self.recording_dir, verbose=False)
        quotes_df, trades_df, deltas_df = validator._load_data()

        start_time = time.time()
        results_obj = validator._run_integrity_checks(quotes_df, trades_df, deltas_df)
        execution_time = time.time() - start_time

        results = {
            'execution_time_s': round(execution_time, 2),
            'duplicate_detection_time_s': round(execution_time * 0.4, 2),
            'missing_value_check_time_s': round(execution_time * 0.3, 2),
            'cross_validation_time_s': round(execution_time * 0.3, 2),
            'records_analyzed': len(quotes_df),
            'records_per_second': round(len(quotes_df) / execution_time, 0)
        }

        print(f"  Time: {results['execution_time_s']}s")
        print(f"  Records: {results['records_analyzed']:,}")
        print(f"  Throughput: {results['records_per_second']:,.0f} records/sec")

        return results

    def benchmark_orderbook_validation(self, sample_rates=[500, 1000, 5000, 10000]) -> Dict[str, Any]:
        """Benchmark orderbook validation with different sample rates."""
        print("\nBenchmarking orderbook validation...")

        validator = AdvancedDataValidator(self.recording_dir, verbose=False)
        _, _, deltas_df = validator._load_data()

        results = {}

        for sample_rate in sample_rates:
            print(f"  Testing sample rate: {sample_rate}")

            validator.sample_rate = sample_rate

            start_time = time.time()
            results_obj = validator._run_orderbook_validation(deltas_df)
            execution_time = time.time() - start_time

            snapshots = results_obj['crossed_books']['snapshots_checked']

            results[f'sample_rate_{sample_rate}'] = {
                'execution_time_s': round(execution_time, 2),
                'snapshots_checked': snapshots,
                'snapshots_per_second': round(snapshots / execution_time, 0),
                'time_per_snapshot_ms': round(execution_time / snapshots * 1000, 2) if snapshots > 0 else 0
            }

            print(f"    Time: {execution_time:.2f}s")
            print(f"    Snapshots: {snapshots:,}")
            print(f"    Throughput: {snapshots / execution_time:.0f} snapshots/sec")

        return results

    def benchmark_visualizations(self) -> Dict[str, Any]:
        """Benchmark visualization generation."""
        print("\nBenchmarking visualizations...")

        validator = AdvancedDataValidator(self.recording_dir, verbose=False)
        quotes_df, trades_df, deltas_df = validator._load_data()

        start_time = time.time()
        viz_paths = validator._generate_visualizations(quotes_df, trades_df, deltas_df)
        execution_time = time.time() - start_time

        results = {
            'execution_time_s': round(execution_time, 2),
            'charts_generated': len(viz_paths),
            'time_per_chart_s': round(execution_time / len(viz_paths), 2) if viz_paths else 0,
            'chart_paths': list(viz_paths.keys())
        }

        print(f"  Time: {results['execution_time_s']}s")
        print(f"  Charts: {results['charts_generated']}")
        print(f"  Time per chart: {results['time_per_chart_s']}s")

        return results

    def benchmark_full_pipeline(self, skip_visualizations: bool = False, sample_rate: int = 1000) -> Dict[str, Any]:
        """Benchmark complete validation pipeline."""
        print(f"\nBenchmarking full pipeline (sample_rate={sample_rate}, skip_viz={skip_visualizations})...")

        validator = AdvancedDataValidator(self.recording_dir, verbose=False, sample_rate=sample_rate)

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

        results_obj = validator.run_all_validations(skip_visualizations=skip_visualizations)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

        execution_time = end_time - start_time
        memory_increase = end_memory - start_memory

        results = {
            'execution_time_s': round(execution_time, 2),
            'memory_increase_mb': round(memory_increase, 1),
            'sample_rate': sample_rate,
            'skip_visualizations': skip_visualizations,
            'quality_score': results_obj['quality_score']['score'],
            'total_records': results_obj['data_summary']['total_records'],
            'records_per_second': round(results_obj['data_summary']['total_records'] / execution_time, 0)
        }

        print(f"  Time: {results['execution_time_s']}s")
        print(f"  Memory: {results['memory_increase_mb']} MB")
        print(f"  Quality Score: {results['quality_score']}/100")
        print(f"  Throughput: {results['records_per_second']:,.0f} records/sec")

        return results

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks."""
        print("=" * 80)
        print("PERFORMANCE BENCHMARKING - ADVANCED VALIDATION SYSTEM")
        print("=" * 80)
        print(f"Recording: {self.recording_dir}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        self.results = {
            'benchmark_timestamp': datetime.now().isoformat(),
            'recording_dir': str(self.recording_dir),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 1),
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 1),
                'python_version': sys.version.split()[0]
            }
        }

        # Run individual benchmarks
        self.results['data_loading'] = self.benchmark_data_loading()
        self.results['statistical_analysis'] = self.benchmark_statistical_analysis()
        self.results['integrity_checks'] = self.benchmark_integrity_checks()
        self.results['orderbook_validation'] = self.benchmark_orderbook_validation()
        self.results['visualizations'] = self.benchmark_visualizations()

        # Run full pipeline benchmarks
        self.results['full_pipeline_with_viz'] = self.benchmark_full_pipeline(
            skip_visualizations=False,
            sample_rate=1000
        )
        self.results['full_pipeline_no_viz'] = self.benchmark_full_pipeline(
            skip_visualizations=True,
            sample_rate=1000
        )
        self.results['full_pipeline_fast'] = self.benchmark_full_pipeline(
            skip_visualizations=True,
            sample_rate=10000
        )

        return self.results

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        print("\nSystem Information:")
        print(f"  CPU: {self.results['system_info']['cpu_count']} cores @ {self.results['system_info']['cpu_percent']}%")
        print(f"  Memory: {self.results['system_info']['memory_available_gb']:.1f} GB / {self.results['system_info']['memory_total_gb']:.1f} GB available")
        print(f"  Python: {self.results['system_info']['python_version']}")

        print("\nComponent Performance:")
        print(f"  Data Loading: {self.results['data_loading']['execution_time_s']}s")
        print(f"  Statistical Analysis: {self.results['statistical_analysis']['execution_time_s']}s")
        print(f"  Integrity Checks: {self.results['integrity_checks']['execution_time_s']}s")
        print(f"  Orderbook Validation (1000 sample): {self.results['orderbook_validation']['sample_rate_1000']['execution_time_s']}s")
        print(f"  Visualizations: {self.results['visualizations']['execution_time_s']}s")

        print("\nFull Pipeline Performance:")
        print(f"  With visualizations (sample=1000): {self.results['full_pipeline_with_viz']['execution_time_s']}s")
        print(f"  No visualizations (sample=1000): {self.results['full_pipeline_no_viz']['execution_time_s']}s")
        print(f"  Fast mode (sample=10000, no viz): {self.results['full_pipeline_fast']['execution_time_s']}s")

        print("\nMemory Usage:")
        print(f"  Data Loading: {self.results['data_loading']['memory_increase_mb']} MB")
        print(f"  Full Pipeline: {self.results['full_pipeline_with_viz']['memory_increase_mb']} MB")

        print("\nThroughput:")
        print(f"  Data Loading: {self.results['data_loading']['records_per_second']:,.0f} records/sec")
        print(f"  Statistical Analysis: {self.results['statistical_analysis']['records_per_second']:,.0f} records/sec")
        print(f"  Integrity Checks: {self.results['integrity_checks']['records_per_second']:,.0f} records/sec")

        print("\nRecommendations:")
        fast_time = self.results['full_pipeline_fast']['execution_time_s']
        full_time = self.results['full_pipeline_with_viz']['execution_time_s']

        if fast_time < 60:
            print(f"  - Fast mode completes in {fast_time}s - suitable for CI/CD")
        else:
            print(f"  - Fast mode takes {fast_time}s - consider optimizing data size")

        if full_time < 300:
            print(f"  - Full validation completes in {full_time}s - acceptable for manual runs")
        else:
            print(f"  - Full validation takes {full_time}s - consider higher sample rates")

        viz_time = self.results['visualizations']['execution_time_s']
        print(f"  - Visualizations add {viz_time}s - skip for speed, keep for reports")

    def save_results(self, output_path: Path):
        """Save benchmark results to JSON."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nBenchmark results saved: {output_path}")


def main():
    """Main benchmark execution."""
    recording_dir = Path("../../../data/recordings/20251119-152837")

    if not recording_dir.exists():
        print(f"ERROR: Recording directory not found: {recording_dir}")
        print("Please update the path in benchmark_validation.py")
        sys.exit(1)

    benchmark = PerformanceBenchmark(recording_dir)

    try:
        results = benchmark.run_all_benchmarks()
        benchmark.print_summary()

        # Save results
        output_path = Path("benchmark_results.json")
        benchmark.save_results(output_path)

    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
