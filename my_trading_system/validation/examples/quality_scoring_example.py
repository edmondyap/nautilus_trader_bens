"""
Quality Scoring Example - How to Use the QualityScorer

This example demonstrates how to aggregate Wave 1 validation results
and generate a comprehensive quality score.

Usage:
    python quality_scoring_example.py

Author: Benjamin Ang / Claude Code
Created: 2025-11-19
"""

from pathlib import Path
from my_trading_system.validation.modules import QualityScorer


def main():
    """
    Example workflow for quality scoring.
    """
    print("=" * 80)
    print("QUALITY SCORING WORKFLOW EXAMPLE")
    print("=" * 80)

    # Step 1: Collect results from Wave 1 validators
    # In practice, these would come from:
    # - StatisticalAnalyzer.analyze_gaps(), .analyze_spreads(), .detect_price_outliers()
    # - IntegrityChecker.detect_duplicates(), .check_missing_values(), .cross_validate_data_types()
    # - OrderbookValidator.validate_price_levels(), .detect_crossed_book(), .analyze_depth_consistency()

    print("\nStep 1: Collecting Wave 1 validation results...")
    print("-" * 80)

    statistical_results = {
        'gaps': {
            'num_large_gaps': 5,
            'max_gap_ms': 2500,
            'mean_interval_ms': 100
        },
        'outliers': {
            'z_outliers_count': 75,
            'iqr_outliers_count': 80,
            'price_jumps_count': 15
        },
        'spreads': {
            'negative_spreads_count': 0,  # Good!
            'zero_spreads_count': 0,
            'wide_spreads_count': 30,
            'mean_spread_bps': 6.5
        },
        'volume': {
            'total_volume': 3500000,
            'trade_count': 8000
        }
    }

    integrity_results = {
        'duplicates': {
            'exact_duplicates_count': 10,
            'timestamp_duplicates_count': 0
        },
        'missing_values': {
            'total_invalid_count': 0  # Good!
        },
        'cross_validation': {
            'trades_within_spread_count': 7200,
            'trades_outside_spread_count': 800,
            'trades_outside_spread_percentage': 10.0
        }
    }

    orderbook_results = {
        'price_levels': {
            'snapshots_checked': 4000,
            'bid_ordering_violations': 0,  # Good!
            'ask_ordering_violations': 0
        },
        'crossed_books': {
            'snapshots_checked': 4000,
            'crossed_books_detected': 0,  # Good!
            'max_cross_amount': 0.0
        },
        'depth': {
            'mean_bid_levels': 50.5,
            'mean_ask_levels': 50.3,
            'min_bid_levels': 47
        }
    }

    print("  Statistical analysis results collected")
    print("  Integrity check results collected")
    print("  Orderbook validation results collected")

    # Step 2: Initialize QualityScorer
    print("\nStep 2: Initializing Quality Scorer...")
    print("-" * 80)

    scorer = QualityScorer(
        statistical_results,
        integrity_results,
        orderbook_results
    )
    print("  QualityScorer initialized")

    # Step 3: Calculate composite score
    print("\nStep 3: Calculating composite quality score...")
    print("-" * 80)

    score_result = scorer.calculate_score()

    print(f"\n  QUALITY SCORE: {score_result['score']}/100")
    print(f"  GRADE: {score_result['grade']}")
    print(f"\n  Issues Detected:")
    print(f"    Critical: {score_result['critical_issues']}")
    print(f"    High:     {score_result['high_issues']}")
    print(f"    Medium:   {score_result['medium_issues']}")
    print(f"    Low:      {score_result['low_issues']}")
    print(f"    Total:    {score_result['issues_found']}")

    # Step 4: Get prioritized issues
    print("\nStep 4: Analyzing issue priorities...")
    print("-" * 80)

    issues = scorer.prioritize_issues()

    if issues['critical']:
        print("\n  CRITICAL ISSUES:")
        for issue in issues['critical']:
            print(f"    - {issue['category']}: {issue['description']}")
            print(f"      Impact: {issue['impact']}")

    if issues['high']:
        print("\n  HIGH PRIORITY ISSUES:")
        for issue in issues['high']:
            print(f"    - {issue['category']}: {issue['description']}")
            print(f"      Impact: {issue['impact']}")

    if issues['medium']:
        print("\n  MEDIUM PRIORITY ISSUES:")
        for issue in issues['medium']:
            print(f"    - {issue['category']}: {issue['description']}")

    if issues['low']:
        print("\n  LOW PRIORITY ISSUES:")
        for issue in issues['low']:
            print(f"    - {issue['category']}: {issue['description']}")

    # Step 5: Generate recommendations
    print("\nStep 5: Generating actionable recommendations...")
    print("-" * 80)

    recommendations = scorer.generate_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    # Step 6: Check minimum standards
    print("\nStep 6: Checking minimum quality standards...")
    print("-" * 80)

    standards = scorer.meets_minimum_standards()

    if standards['passes']:
        print("  PASS: Data meets minimum quality standards")
    else:
        print("  FAIL: Data does NOT meet minimum quality standards")
        print("\n  Failed Checks:")
        if not standards['score_check']:
            print(f"    - Score: {standards['details']['score']}")
        if not standards['critical_issues_check']:
            print(f"    - Critical Issues: {standards['details']['critical_issues']}")
        if not standards['negative_spreads_check']:
            print(f"    - Negative Spreads: {standards['details']['negative_spreads']}")
        if not standards['crossed_books_check']:
            print(f"    - Crossed Books: {standards['details']['crossed_books']}")

    # Step 7: Generate detailed report
    print("\nStep 7: Generating detailed quality report...")
    print("-" * 80)

    report = scorer.get_detailed_report()

    print(f"\n  SUMMARY:")
    print(f"    {report['summary']}")

    print(f"\n  SCORE BREAKDOWN:")
    print(f"    Starting Score: {report['score_breakdown']['starting_score']}")
    if report['score_breakdown']['deductions']:
        print(f"    Deductions:")
        for category, details in report['score_breakdown']['deductions'].items():
            print(f"      - {details['description']}: -{details['points_deducted']} pts")
    print(f"    Final Score: {report['score_breakdown']['final_score']}")

    # Step 8: Decision making
    print("\nStep 8: Making data quality decision...")
    print("-" * 80)

    if score_result['score'] >= 90:
        decision = "APPROVED FOR PRODUCTION"
        action = "Proceed with backtesting and strategy development"
    elif score_result['score'] >= 70:
        decision = "APPROVED WITH CAUTION"
        action = "Usable for backtesting, but monitor results closely"
    elif score_result['score'] >= 60:
        decision = "NOT RECOMMENDED"
        action = "Consider re-recording or filtering problematic data"
    else:
        decision = "REJECTED"
        action = "Re-record data with corrected configuration"

    print(f"\n  DECISION: {decision}")
    print(f"  ACTION:   {action}")

    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
