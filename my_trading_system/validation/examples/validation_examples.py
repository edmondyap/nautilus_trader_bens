"""
Usage Examples for Advanced Validation System

This file demonstrates common workflows and integration patterns.

Run individual examples:
    python validation_examples.py

Author: Claude Code (Subagent 8)
Created: 2025-11-19
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from my_trading_system.validation.advanced_validation import AdvancedDataValidator


def example_1_basic_validation():
    """Example 1: Basic validation of a recording."""
    print("=" * 80)
    print("Example 1: Basic Validation")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")

    validator = AdvancedDataValidator(recording_dir, verbose=True)
    results = validator.run_all_validations()

    print(f"\nQuality Score: {results['quality_score']['score']}/100")
    print(f"Grade: {results['quality_score']['grade']}")
    print(f"Execution Time: {results['execution_time']:.1f}s")


def example_2_fast_validation():
    """Example 2: Fast validation for CI/CD."""
    print("=" * 80)
    print("Example 2: Fast Validation (CI/CD)")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")

    validator = AdvancedDataValidator(recording_dir, verbose=False, sample_rate=10000)
    results = validator.run_all_validations(
        skip_visualizations=True
    )

    score = results['quality_score']['score']

    if score >= 70:
        print(f"PASS: Data quality acceptable ({score}/100)")
        return 0
    else:
        print(f"FAIL: Data quality below threshold ({score}/100)")
        return 1


def example_3_custom_output():
    """Example 3: Custom output directory."""
    print("=" * 80)
    print("Example 3: Custom Output Directory")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")
    output_dir = Path("/tmp/validation_results")

    validator = AdvancedDataValidator(recording_dir, output_dir=output_dir, verbose=True)
    results = validator.run_all_validations()

    print(f"\nResults saved to: {output_dir}")
    print(f"  - {output_dir}/results.json")
    print(f"  - {output_dir}/*.png (charts)")
    print(f"  - {output_dir}/*.html (interactive charts)")


def example_4_python_api():
    """Example 4: Using validation results in Python code."""
    print("=" * 80)
    print("Example 4: Python API Usage")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")

    validator = AdvancedDataValidator(recording_dir, verbose=False, sample_rate=10000)
    results = validator.run_all_validations(skip_visualizations=True)

    # Access specific results
    score = results['quality_score']['score']
    negative_spreads = results['statistical_results']['spreads']['negative_spreads_count']
    crossed_books = results['orderbook_results']['crossed_books']['crossed_books_detected']

    print(f"Score: {score}/100")
    print(f"Negative Spreads: {negative_spreads}")
    print(f"Crossed Books: {crossed_books}")

    # Make decision based on results
    if negative_spreads > 0:
        print("\nCRITICAL: Negative spreads detected - re-record required")
        return 1
    elif score < 70:
        print("\nWARNING: Quality below threshold - review recommended")
        return 1
    else:
        print("\nPASS: Data quality acceptable")
        return 0


def example_5_detailed_inspection():
    """Example 5: Detailed inspection of validation results."""
    print("=" * 80)
    print("Example 5: Detailed Results Inspection")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")

    validator = AdvancedDataValidator(recording_dir, verbose=False, sample_rate=10000)
    results = validator.run_all_validations(skip_visualizations=True)

    # Statistical Analysis
    print("\nStatistical Analysis:")
    gaps = results['statistical_results']['gaps']
    print(f"  Large gaps: {gaps['num_large_gaps']}")
    print(f"  Max gap: {gaps['max_gap_ms']:.2f}ms")
    print(f"  Mean interval: {gaps['mean_interval_ms']:.2f}ms")

    spreads = results['statistical_results']['spreads']
    print(f"\n  Mean spread: {spreads['mean_spread_bps']:.2f} bps")
    print(f"  Negative spreads: {spreads['negative_spreads_count']}")
    print(f"  Wide spreads: {spreads['wide_spreads_count']}")

    outliers = results['statistical_results']['outliers']
    print(f"\n  Z-score outliers: {outliers['z_outliers_count']}")
    print(f"  Price jumps: {outliers['price_jumps_count']}")

    # Integrity Checks
    print("\nIntegrity Checks:")
    duplicates = results['integrity_results']['duplicates']
    print(f"  Exact duplicates: {duplicates['exact_duplicates_count']}")
    print(f"  Timestamp duplicates: {duplicates['timestamp_duplicates_count']}")

    missing = results['integrity_results']['missing_values']
    print(f"  Invalid records: {missing['total_invalid_count']}")

    # Orderbook Validation
    print("\nOrderbook Validation:")
    crossed = results['orderbook_results']['crossed_books']
    print(f"  Crossed books: {crossed['crossed_books_detected']}")
    print(f"  Snapshots checked: {crossed['snapshots_checked']}")

    # Quality Score
    print("\nQuality Score:")
    quality = results['quality_score']
    print(f"  Score: {quality['score']}/100")
    print(f"  Grade: {quality['grade']}")
    print(f"  Critical issues: {quality['critical_issues']}")
    print(f"  High issues: {quality['high_issues']}")
    print(f"  Medium issues: {quality['medium_issues']}")
    print(f"  Low issues: {quality['low_issues']}")

    # Recommendations
    print("\nRecommendations:")
    recommendations = quality['detailed_report']['recommendations']
    for rec in recommendations:
        print(f"  - {rec}")


def example_6_batch_validation():
    """Example 6: Batch validation of multiple recordings."""
    print("=" * 80)
    print("Example 6: Batch Validation")
    print("=" * 80)

    recordings_dir = Path("../../../data/recordings")

    # Find all recording directories
    recording_dirs = [d for d in recordings_dir.iterdir() if d.is_dir() and d.name.startswith("2025")]

    print(f"Found {len(recording_dirs)} recordings to validate\n")

    results_summary = []

    for recording_dir in recording_dirs:
        print(f"Validating: {recording_dir.name}")

        try:
            validator = AdvancedDataValidator(recording_dir, verbose=False, sample_rate=10000)
            results = validator.run_all_validations(skip_visualizations=True)

            score = results['quality_score']['score']
            grade = results['quality_score']['grade']

            results_summary.append({
                'recording': recording_dir.name,
                'score': score,
                'grade': grade,
                'status': 'PASS' if score >= 70 else 'FAIL'
            })

            print(f"  Score: {score}/100 (Grade: {grade})\n")

        except Exception as e:
            print(f"  ERROR: {e}\n")
            results_summary.append({
                'recording': recording_dir.name,
                'score': 0,
                'grade': 'F',
                'status': 'ERROR'
            })

    # Print summary
    print("\n" + "=" * 80)
    print("Batch Validation Summary")
    print("=" * 80)

    for result in results_summary:
        status_symbol = "✓" if result['status'] == 'PASS' else "✗"
        print(f"{status_symbol} {result['recording']}: {result['score']}/100 (Grade: {result['grade']})")

    # Overall statistics
    pass_count = sum(1 for r in results_summary if r['status'] == 'PASS')
    fail_count = sum(1 for r in results_summary if r['status'] == 'FAIL')
    error_count = sum(1 for r in results_summary if r['status'] == 'ERROR')

    print(f"\nTotal: {len(results_summary)} recordings")
    print(f"  Passed: {pass_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Errors: {error_count}")


def example_7_incremental_validation():
    """Example 7: Incremental validation (statistical only)."""
    print("=" * 80)
    print("Example 7: Incremental Validation (Statistical Only)")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")

    # Create validator
    validator = AdvancedDataValidator(recording_dir, verbose=True, sample_rate=10000)

    # Load data once
    print("Loading data...")
    quotes_df, trades_df, deltas_df = validator._load_data()
    print(f"Loaded {len(quotes_df):,} quotes, {len(deltas_df):,} deltas")

    # Run only statistical analysis
    print("\nRunning statistical analysis...")
    statistical_results = validator._run_statistical_analysis(quotes_df, trades_df, deltas_df)

    # Check for critical issues
    negative_spreads = statistical_results['spreads']['negative_spreads_count']

    if negative_spreads > 0:
        print(f"\nCRITICAL: {negative_spreads} negative spreads detected!")
        print("Stopping validation - data unusable")
        return 1

    print("\nNo critical issues found in statistical analysis")
    print("Proceeding with full validation...")

    # Run full validation
    results = validator.run_all_validations(skip_visualizations=True)
    print(f"\nFinal Score: {results['quality_score']['score']}/100")


def example_8_custom_thresholds():
    """Example 8: Custom quality thresholds."""
    print("=" * 80)
    print("Example 8: Custom Quality Thresholds")
    print("=" * 80)

    recording_dir = Path("../../../data/recordings/20251119-152837")

    validator = AdvancedDataValidator(recording_dir, verbose=False, sample_rate=10000)
    results = validator.run_all_validations(skip_visualizations=True)

    # Custom thresholds for acceptance
    CUSTOM_THRESHOLDS = {
        'min_score': 80,  # Higher than default 70
        'max_negative_spreads': 0,
        'max_crossed_books': 0,
        'max_large_gaps': 5,
        'max_outliers': 50,
        'max_duplicates': 10
    }

    score = results['quality_score']['score']
    negative_spreads = results['statistical_results']['spreads']['negative_spreads_count']
    crossed_books = results['orderbook_results']['crossed_books']['crossed_books_detected']
    large_gaps = results['statistical_results']['gaps']['num_large_gaps']
    outliers = results['statistical_results']['outliers']['z_outliers_count']
    duplicates = results['integrity_results']['duplicates']['exact_duplicates_count']

    print(f"Score: {score}/100 (threshold: {CUSTOM_THRESHOLDS['min_score']})")
    print(f"Negative spreads: {negative_spreads} (max: {CUSTOM_THRESHOLDS['max_negative_spreads']})")
    print(f"Crossed books: {crossed_books} (max: {CUSTOM_THRESHOLDS['max_crossed_books']})")
    print(f"Large gaps: {large_gaps} (max: {CUSTOM_THRESHOLDS['max_large_gaps']})")
    print(f"Outliers: {outliers} (max: {CUSTOM_THRESHOLDS['max_outliers']})")
    print(f"Duplicates: {duplicates} (max: {CUSTOM_THRESHOLDS['max_duplicates']})")

    # Check custom criteria
    passes = (
        score >= CUSTOM_THRESHOLDS['min_score'] and
        negative_spreads <= CUSTOM_THRESHOLDS['max_negative_spreads'] and
        crossed_books <= CUSTOM_THRESHOLDS['max_crossed_books'] and
        large_gaps <= CUSTOM_THRESHOLDS['max_large_gaps'] and
        outliers <= CUSTOM_THRESHOLDS['max_outliers'] and
        duplicates <= CUSTOM_THRESHOLDS['max_duplicates']
    )

    if passes:
        print("\nPASS: Data meets custom quality standards")
        return 0
    else:
        print("\nFAIL: Data does not meet custom quality standards")
        return 1


if __name__ == '__main__':
    # Run all examples
    examples = [
        ("Basic Validation", example_1_basic_validation),
        ("Fast Validation", example_2_fast_validation),
        ("Custom Output", example_3_custom_output),
        ("Python API", example_4_python_api),
        ("Detailed Inspection", example_5_detailed_inspection),
        ("Batch Validation", example_6_batch_validation),
        ("Incremental Validation", example_7_incremental_validation),
        ("Custom Thresholds", example_8_custom_thresholds),
    ]

    print("Advanced Validation System - Usage Examples")
    print("=" * 80)
    print()

    for i, (name, func) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print()
    print("Run all examples? (y/n): ", end='')

    choice = input().strip().lower()

    if choice == 'y':
        for name, func in examples:
            try:
                func()
                print("\n")
            except Exception as e:
                print(f"\nERROR running {name}: {e}\n")
    else:
        print("\nTo run individual examples, call them directly:")
        print("  python -c 'from validation_examples import example_1_basic_validation; example_1_basic_validation()'")
