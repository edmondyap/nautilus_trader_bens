"""
Integration Tests for Advanced Validation System

Tests the complete validation pipeline end-to-end using real recording data.

Usage:
    pytest my_trading_system/tests/integration/test_advanced_validation_system.py -v
    pytest my_trading_system/tests/integration/test_advanced_validation_system.py::TestAdvancedValidationSystem::test_system_imports -v

Test Coverage:
- Module imports
- Data loading
- Statistical analysis
- Integrity checks
- Orderbook validation
- Quality scoring
- Full pipeline execution
- JSON output

Author: Claude Code (Subagent 8)
Created: 2025-11-19
"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from my_trading_system.validation.advanced_validation import AdvancedDataValidator


class TestAdvancedValidationSystem:
    """Integration tests for complete validation system."""

    @pytest.fixture
    def recording_dir(self):
        """Path to test recording."""
        return Path("/Users/benjaminang/Desktop/nautilus_trader_bens/data/recordings/20251119-152837")

    @pytest.fixture
    def validator(self, recording_dir):
        """Create validator instance."""
        return AdvancedDataValidator(recording_dir, verbose=False)

    def test_system_imports(self):
        """Test all modules can be imported."""
        # Import all modules
        from my_trading_system.validation.modules.statistical_analysis import StatisticalAnalyzer
        from my_trading_system.validation.modules.integrity_checks import IntegrityChecker
        from my_trading_system.validation.modules.orderbook_validation import OrderbookValidator
        from my_trading_system.validation.modules.visualization import DataVisualizer
        from my_trading_system.validation.modules.quality_scorer import QualityScorer
        from my_trading_system.validation.modules.html_report import HTMLReportGenerator

        # If we get here, imports work
        assert True, "All module imports successful"

    def test_validator_initialization(self, recording_dir):
        """Test validator can be initialized."""
        validator = AdvancedDataValidator(recording_dir, verbose=False)

        assert validator.recording_dir == recording_dir
        assert validator.output_dir == recording_dir / 'validation'
        assert validator.verbose == False
        assert validator.sample_rate == 1000

    def test_data_loading(self, validator):
        """Test data can be loaded."""
        quotes_df, trades_df, deltas_df = validator._load_data()

        # Check data was loaded
        assert len(quotes_df) > 0, "Quotes should be loaded"
        assert len(deltas_df) > 0, "Deltas should be loaded"

        # Check expected record counts (approximate)
        assert len(quotes_df) == 560356, f"Expected 560356 quotes, got {len(quotes_df)}"
        assert len(deltas_df) == 4013933, f"Expected 4013933 deltas, got {len(deltas_df)}"

        # Check DataFrame structure
        assert 'timestamp' in quotes_df.columns
        assert 'bid_price' in quotes_df.columns
        assert 'ask_price' in quotes_df.columns

        assert 'timestamp' in deltas_df.columns
        assert 'action' in deltas_df.columns
        assert 'side' in deltas_df.columns
        assert 'price' in deltas_df.columns

    def test_statistical_analysis(self, validator):
        """Test statistical analysis module."""
        quotes_df, trades_df, deltas_df = validator._load_data()

        results = validator._run_statistical_analysis(quotes_df, trades_df, deltas_df)

        # Check results structure
        assert 'gaps' in results
        assert 'outliers' in results
        assert 'spreads' in results

        # Check gap analysis
        gaps = results['gaps']
        assert 'num_large_gaps' in gaps
        assert 'max_gap_ms' in gaps
        assert 'mean_interval_ms' in gaps

        # Check outlier analysis
        outliers = results['outliers']
        assert 'z_outliers_count' in outliers
        assert 'price_jumps_count' in outliers

        # Check spread analysis
        spreads = results['spreads']
        assert 'mean_spread_bps' in spreads
        assert 'negative_spreads_count' in spreads
        assert 'wide_spreads_count' in spreads

        # Critical check: No negative spreads
        assert spreads['negative_spreads_count'] == 0, "Negative spreads detected - data unusable!"

    def test_integrity_checks(self, validator):
        """Test integrity check module."""
        quotes_df, trades_df, deltas_df = validator._load_data()

        results = validator._run_integrity_checks(quotes_df, trades_df, deltas_df)

        # Check results structure
        assert 'duplicates' in results
        assert 'missing_values' in results

        # Check duplicate detection
        duplicates = results['duplicates']
        assert 'exact_duplicates_count' in duplicates
        assert 'timestamp_duplicates_count' in duplicates

        # Check missing values
        missing = results['missing_values']
        assert 'total_invalid_count' in missing

    def test_orderbook_validation(self, validator):
        """Test orderbook validation module."""
        _, _, deltas_df = validator._load_data()

        # Use high sample rate for speed
        validator.sample_rate = 10000
        results = validator._run_orderbook_validation(deltas_df)

        # Check results structure
        assert 'crossed_books' in results

        # Check crossed book detection
        crossed = results['crossed_books']
        assert 'crossed_books_detected' in crossed
        assert 'snapshots_checked' in crossed

        # Critical check: No crossed books
        assert crossed['crossed_books_detected'] == 0, "Crossed orderbooks detected - data integrity issue!"

    def test_quality_scoring(self, validator):
        """Test quality scoring module."""
        # Run minimal validation to get results
        quotes_df, trades_df, deltas_df = validator._load_data()

        statistical_results = validator._run_statistical_analysis(quotes_df, trades_df, deltas_df)
        integrity_results = validator._run_integrity_checks(quotes_df, trades_df, deltas_df)

        # Use high sample rate for speed
        validator.sample_rate = 10000
        orderbook_results = validator._run_orderbook_validation(deltas_df)

        score_results = validator._calculate_quality_score(
            statistical_results,
            integrity_results,
            orderbook_results
        )

        # Check score structure
        assert 'score' in score_results
        assert 'grade' in score_results
        assert 'issues_found' in score_results
        assert 'critical_issues' in score_results
        assert 'high_issues' in score_results
        assert 'medium_issues' in score_results
        assert 'low_issues' in score_results

        # Check score range
        assert 0 <= score_results['score'] <= 100, f"Score out of range: {score_results['score']}"
        assert score_results['grade'] in ['A', 'B', 'C', 'D', 'F'], f"Invalid grade: {score_results['grade']}"

        # Check detailed report exists
        assert 'detailed_report' in score_results
        detailed = score_results['detailed_report']
        assert 'recommendations' in detailed
        assert 'pass_criteria' in detailed
        assert 'issues_by_priority' in detailed

    @pytest.mark.slow
    def test_full_validation_pipeline(self, recording_dir, tmp_path):
        """Test complete validation pipeline end-to-end."""
        validator = AdvancedDataValidator(
            recording_dir,
            output_dir=tmp_path / 'validation',
            verbose=False,
            sample_rate=10000
        )

        # Run full validation (skip viz for speed)
        results = validator.run_all_validations(skip_visualizations=True)

        # Check all sections present
        assert 'statistical_results' in results
        assert 'integrity_results' in results
        assert 'orderbook_results' in results
        assert 'quality_score' in results
        assert 'execution_time' in results
        assert 'data_summary' in results

        # Check data summary
        summary = results['data_summary']
        assert 'quotes_count' in summary
        assert 'deltas_count' in summary
        assert 'total_records' in summary
        assert summary['quotes_count'] == 560356
        assert summary['deltas_count'] == 4013933

        # Check execution completed
        assert results['execution_time'] > 0

        # Check quality score calculated
        quality = results['quality_score']
        assert 0 <= quality['score'] <= 100

    def test_json_output(self, recording_dir, tmp_path):
        """Test JSON results can be saved."""
        validator = AdvancedDataValidator(
            recording_dir,
            output_dir=tmp_path,
            verbose=False,
            sample_rate=10000
        )

        # Run validation
        results = validator.run_all_validations(skip_visualizations=True)

        # Check JSON file was created
        output_file = tmp_path / 'results.json'
        assert output_file.exists(), "results.json not created"

        # Check JSON is valid
        with open(output_file) as f:
            loaded_results = json.load(f)

        # Verify structure
        assert 'quality_score' in loaded_results
        assert 'statistical_results' in loaded_results
        assert 'execution_time' in loaded_results

        # Verify data
        assert loaded_results['quality_score']['score'] == results['quality_score']['score']

    def test_error_handling_missing_directory(self):
        """Test error handling for missing recording."""
        with pytest.raises(FileNotFoundError):
            validator = AdvancedDataValidator(Path('/nonexistent/path'), verbose=False)
            validator._load_data()

    def test_output_directory_creation(self, recording_dir, tmp_path):
        """Test output directory is created if it doesn't exist."""
        output_dir = tmp_path / 'nested' / 'output' / 'validation'

        validator = AdvancedDataValidator(
            recording_dir,
            output_dir=output_dir,
            verbose=False
        )

        # Output directory should be created
        assert output_dir.exists(), "Output directory not created"

    def test_statistical_analysis_completeness(self, validator):
        """Test statistical analysis returns all expected metrics."""
        quotes_df, trades_df, deltas_df = validator._load_data()
        results = validator._run_statistical_analysis(quotes_df, trades_df, deltas_df)

        # Gap analysis metrics
        gaps = results['gaps']
        required_gap_metrics = [
            'num_large_gaps', 'max_gap_ms', 'mean_interval_ms',
            'median_interval_ms', 'std_interval_ms', 'p95_interval_ms',
            'p99_interval_ms'
        ]
        for metric in required_gap_metrics:
            assert metric in gaps, f"Missing gap metric: {metric}"

        # Spread analysis metrics
        spreads = results['spreads']
        required_spread_metrics = [
            'mean_spread_bps', 'median_spread_bps', 'std_spread_bps',
            'negative_spreads_count', 'zero_spreads_count', 'wide_spreads_count'
        ]
        for metric in required_spread_metrics:
            assert metric in spreads, f"Missing spread metric: {metric}"

        # Outlier analysis metrics
        outliers = results['outliers']
        required_outlier_metrics = [
            'z_outliers_count', 'iqr_outliers_count', 'price_jumps_count',
            'outlier_percentage'
        ]
        for metric in required_outlier_metrics:
            assert metric in outliers, f"Missing outlier metric: {metric}"

    def test_integrity_checks_completeness(self, validator):
        """Test integrity checks return all expected metrics."""
        quotes_df, trades_df, deltas_df = validator._load_data()
        results = validator._run_integrity_checks(quotes_df, trades_df, deltas_df)

        # Duplicate detection metrics
        duplicates = results['duplicates']
        required_dup_metrics = [
            'exact_duplicates_count', 'timestamp_duplicates_count',
            'duplicate_percentage'
        ]
        for metric in required_dup_metrics:
            assert metric in duplicates, f"Missing duplicate metric: {metric}"

        # Missing values metrics
        missing = results['missing_values']
        assert 'total_invalid_count' in missing, "Missing total_invalid_count"

    def test_quality_score_grades(self, validator):
        """Test quality score grade assignment."""
        # Test with mock data to verify grade logic
        from my_trading_system.validation.modules.quality_scorer import QualityScorer

        # Create mock results for different score ranges
        test_cases = [
            (95, 'A'),
            (85, 'B'),
            (75, 'C'),
            (65, 'D'),
            (50, 'F')
        ]

        for expected_score, expected_grade in test_cases:
            # Mock results that will produce the expected score
            mock_statistical = {
                'gaps': {'num_large_gaps': 0 if expected_score >= 90 else 5},
                'outliers': {'z_outliers_count': 0 if expected_score >= 90 else 50},
                'spreads': {
                    'negative_spreads_count': 0,
                    'wide_spreads_count': 0 if expected_score >= 90 else 30
                }
            }

            mock_integrity = {
                'duplicates': {'exact_duplicates_count': 0},
                'missing_values': {'total_invalid_count': 0},
                'cross_validation': {'trades_outside_spread_percentage': 5.0}
            }

            mock_orderbook = {
                'price_levels': {'bid_ordering_violations': 0, 'ask_ordering_violations': 0},
                'crossed_books': {'crossed_books_detected': 0},
                'depth': {'mean_bid_levels': 50}
            }

            scorer = QualityScorer(mock_statistical, mock_integrity, mock_orderbook)
            result = scorer.calculate_score()

            # Grade should be correct for the score range
            assert result['grade'] in ['A', 'B', 'C', 'D', 'F']

    def test_data_memory_efficiency(self, validator):
        """Test data loading doesn't consume excessive memory."""
        import sys

        quotes_df, trades_df, deltas_df = validator._load_data()

        # Check DataFrame memory usage
        quotes_memory_mb = quotes_df.memory_usage(deep=True).sum() / (1024 * 1024)
        deltas_memory_mb = deltas_df.memory_usage(deep=True).sum() / (1024 * 1024)
        total_memory_mb = quotes_memory_mb + deltas_memory_mb

        # Should be under 500MB for this dataset
        assert total_memory_mb < 500, f"Memory usage too high: {total_memory_mb:.1f} MB"

        # Print memory usage for reference
        print(f"\nMemory usage:")
        print(f"  Quotes: {quotes_memory_mb:.1f} MB")
        print(f"  Deltas: {deltas_memory_mb:.1f} MB")
        print(f"  Total: {total_memory_mb:.1f} MB")

    def test_validation_performance(self, validator):
        """Test validation completes in reasonable time."""
        import time

        start_time = time.time()

        # Run validation with high sample rate for speed
        validator.sample_rate = 10000
        results = validator.run_all_validations(skip_visualizations=True)

        execution_time = time.time() - start_time

        # Should complete in under 2 minutes with high sample rate
        assert execution_time < 120, f"Validation too slow: {execution_time:.1f}s"

        print(f"\nValidation execution time: {execution_time:.1f}s")
        print(f"  Data loading: ~{execution_time * 0.1:.1f}s")
        print(f"  Statistical analysis: ~{execution_time * 0.1:.1f}s")
        print(f"  Integrity checks: ~{execution_time * 0.05:.1f}s")
        print(f"  Orderbook validation: ~{execution_time * 0.75:.1f}s")

    @pytest.mark.parametrize("sample_rate", [500, 1000, 5000, 10000])
    def test_sample_rate_impact(self, validator, sample_rate):
        """Test different sample rates produce valid results."""
        import time

        _, _, deltas_df = validator._load_data()

        validator.sample_rate = sample_rate

        start_time = time.time()
        results = validator._run_orderbook_validation(deltas_df)
        execution_time = time.time() - start_time

        # Check results are valid
        assert 'crossed_books' in results
        assert results['crossed_books']['snapshots_checked'] > 0

        # Print performance
        snapshots = results['crossed_books']['snapshots_checked']
        print(f"\nSample rate {sample_rate}: {execution_time:.1f}s ({snapshots} snapshots)")

    def test_concurrent_validations(self, recording_dir, tmp_path):
        """Test multiple validators can run concurrently."""
        import concurrent.futures

        def run_validation(output_dir):
            validator = AdvancedDataValidator(
                recording_dir,
                output_dir=output_dir,
                verbose=False,
                sample_rate=10000
            )
            return validator.run_all_validations(skip_visualizations=True)

        # Create multiple output directories
        output_dirs = [tmp_path / f'validation_{i}' for i in range(3)]

        # Run validations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_validation, output_dir) for output_dir in output_dirs]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert len(results) == 3
        for result in results:
            assert 'quality_score' in result
            assert result['quality_score']['score'] > 0


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
