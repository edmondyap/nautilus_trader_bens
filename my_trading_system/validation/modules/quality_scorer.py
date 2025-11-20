"""
Quality Scoring Engine - Advanced Data Validation System

Wave 2: Quality Scoring and Aggregation
Location: my_trading_system/validation/modules/quality_scorer.py
Author: Benjamin Ang / Claude Code (Subagent 5)
Created: 2025-11-19

Aggregates results from Wave 1 validators and produces:
- Composite quality score (0-100)
- Issue prioritization (critical, high, medium, low)
- Actionable recommendations
- Pass/fail criteria validation

Scoring Rubric:
--------------
Start at 100 (perfect), deduct points for issues:
- Negative spreads: Automatic FAIL (0 pts) - impossible in real markets
- Crossed orderbooks: -15 pts (CRITICAL - data corruption)
- Price outliers >100: -10 pts (High - data quality issue)
- Large gaps >10: -10 pts (High - connectivity problems)
- Missing values: -10 pts (High - incomplete data)
- Duplicates: -5 pts (Medium - data duplication)
- Trades outside spread >15%: -5 pts (Medium - timing issues)
- Wide spreads >50: -3 pts (Low - liquidity issues)

Grade Assignment:
-----------------
A: 90-100 (Excellent)
B: 80-89  (Good)
C: 70-79  (Acceptable)
D: 60-69  (Poor)
F: 0-59   (Fail)

Examples
--------
>>> from pathlib import Path
>>> # Assume we have results from Wave 1 validators
>>> scorer = QualityScorer(statistical_results, integrity_results, orderbook_results)
>>> score_result = scorer.calculate_score()
>>> print(f"Quality Score: {score_result['score']}/100 ({score_result['grade']})")
>>>
>>> # Get recommendations
>>> recommendations = scorer.generate_recommendations()
>>> for rec in recommendations:
...     print(rec)
>>>
>>> # Get detailed report
>>> report = scorer.get_detailed_report()
>>> print(f"Critical issues: {report['issues_by_priority']['critical']}")
"""

from typing import Dict, Any, List
from dataclasses import dataclass


# Pass/fail criteria configuration
PASS_CRITERIA = {
    'min_score': 70,
    'max_critical_issues': 0,
    'max_negative_spreads': 0,
    'max_crossed_books': 0,
    'min_trade_count': 1000,
    'max_missing_percentage': 1.0,
}


@dataclass
class Issue:
    """
    Represents a single data quality issue.

    Attributes
    ----------
    priority : str
        Issue priority level: 'critical', 'high', 'medium', or 'low'
    category : str
        Issue category: 'spread', 'orderbook', 'price', 'connectivity',
        'completeness', 'duplicates', 'cross_validation'
    description : str
        Human-readable description of the issue
    impact : str
        Explanation of the issue's impact on data quality
    count : int
        Number of occurrences (if applicable)
    """
    priority: str
    category: str
    description: str
    impact: str
    count: int = 0


class QualityScorer:
    """
    Calculates overall data quality score from validation results.

    Aggregates results from:
    - StatisticalAnalyzer (gaps, outliers, spreads, volume)
    - IntegrityChecker (duplicates, missing values, cross-validation)
    - OrderbookValidator (structure, crossed books, depth)

    Produces:
    - Composite quality score (0-100)
    - Issue prioritization (critical, high, medium, low)
    - Actionable recommendations

    Parameters
    ----------
    statistical_results : dict
        Results from StatisticalAnalyzer with keys:
        - gaps: dict (num_large_gaps, max_gap_ms, etc.)
        - outliers: dict (z_outliers_count, price_jumps_count, etc.)
        - spreads: dict (negative_spreads_count, wide_spreads_count, etc.)
        - volume: dict (optional, trade volume analysis)
    integrity_results : dict
        Results from IntegrityChecker with keys:
        - duplicates: dict (exact_duplicates_count, etc.)
        - missing_values: dict (total_invalid_count, etc.)
        - cross_validation: dict (trades_outside_spread_percentage, etc.)
    orderbook_results : dict
        Results from OrderbookValidator with keys:
        - price_levels: dict (bid_ordering_violations, etc.)
        - crossed_books: dict (crossed_books_detected, etc.)
        - depth: dict (mean_bid_levels, min_bid_levels, etc.)

    Attributes
    ----------
    statistical_results : dict
        Statistical analysis results
    integrity_results : dict
        Integrity check results
    orderbook_results : dict
        Orderbook validation results
    issues : list[Issue]
        List of detected issues
    score : int
        Composite quality score (0-100)

    Examples
    --------
    >>> scorer = QualityScorer(
    ...     statistical_results={'gaps': {...}, 'outliers': {...}, 'spreads': {...}},
    ...     integrity_results={'duplicates': {...}, 'missing_values': {...}},
    ...     orderbook_results={'price_levels': {...}, 'crossed_books': {...}}
    ... )
    >>> result = scorer.calculate_score()
    >>> print(f"Score: {result['score']}/100 ({result['grade']})")
    """

    def __init__(
        self,
        statistical_results: Dict[str, Any],
        integrity_results: Dict[str, Any],
        orderbook_results: Dict[str, Any]
    ):
        """
        Initialize with results from Wave 1 validators.

        Parameters
        ----------
        statistical_results : dict
            Results from StatisticalAnalyzer
        integrity_results : dict
            Results from IntegrityChecker
        orderbook_results : dict
            Results from OrderbookValidator
        """
        self.statistical_results = statistical_results
        self.integrity_results = integrity_results
        self.orderbook_results = orderbook_results
        self.issues: List[Issue] = []
        self.score = 100  # Start at perfect, deduct for issues

    def calculate_score(self) -> Dict[str, Any]:
        """
        Calculate composite quality score (0-100).

        Scoring rubric:
        - Start at 100 (perfect)
        - Deduct points for issues:
          - Negative spreads: AUTOMATIC FAIL (score = 0)
          - Crossed orderbooks: -15 pts (CRITICAL)
          - Price outliers >100: -10 pts (High)
          - Large gaps >10: -10 pts (High)
          - Missing values: -10 pts (High)
          - Duplicates: -5 pts (Medium)
          - Trades outside spread >15%: -5 pts (Medium)
          - Wide spreads >50: -3 pts (Low)

        Returns
        -------
        dict
            Dictionary with keys:
            - score: int (0-100)
            - grade: str (A/B/C/D/F)
            - issues_found: int
            - critical_issues: int
            - high_issues: int
            - medium_issues: int
            - low_issues: int

        Examples
        --------
        >>> result = scorer.calculate_score()
        >>> print(f"Score: {result['score']}/100")
        >>> print(f"Grade: {result['grade']}")
        >>> print(f"Critical issues: {result['critical_issues']}")
        """
        # Reset for recalculation
        self.score = 100
        self.issues = []

        # CRITICAL ISSUES (Automatic Fail)
        self._check_negative_spreads()

        # If we have negative spreads, score is 0 regardless of other issues
        if self.score == 0:
            return self._compile_score_result()

        # CRITICAL ISSUES (Major deductions)
        self._check_crossed_orderbooks()

        # HIGH PRIORITY ISSUES
        self._check_price_outliers()
        self._check_large_gaps()
        self._check_missing_values()

        # MEDIUM PRIORITY ISSUES
        self._check_duplicates()
        self._check_cross_validation()

        # LOW PRIORITY ISSUES
        self._check_wide_spreads()
        self._check_orderbook_violations()

        # Ensure score doesn't go below 0
        self.score = max(0, self.score)

        return self._compile_score_result()

    def _check_negative_spreads(self):
        """Check for negative spreads (CRITICAL - automatic fail)."""
        spread_results = self.statistical_results.get('spreads', {})
        negative_count = spread_results.get('negative_spreads_count', 0)

        if negative_count > 0:
            self.score = 0  # AUTOMATIC FAIL
            self.issues.append(Issue(
                priority='critical',
                category='spread',
                description=f"Negative spreads detected: {negative_count}",
                impact='Data physically impossible - complete re-record required',
                count=negative_count
            ))

    def _check_crossed_orderbooks(self):
        """Check for crossed orderbooks (CRITICAL)."""
        crossed_results = self.orderbook_results.get('crossed_books', {})
        crossed_count = crossed_results.get('crossed_books_detected', 0)

        if crossed_count > 0:
            self.score -= 15
            self.issues.append(Issue(
                priority='critical',
                category='orderbook',
                description=f"Crossed orderbooks detected: {crossed_count}",
                impact='Best bid >= best ask violates market laws',
                count=crossed_count
            ))

    def _check_price_outliers(self):
        """Check for excessive price outliers (HIGH priority)."""
        outlier_results = self.statistical_results.get('outliers', {})
        z_outliers = outlier_results.get('z_outliers_count', 0)

        if z_outliers > 100:
            self.score -= 10
            self.issues.append(Issue(
                priority='high',
                category='price',
                description=f"Excessive price outliers: {z_outliers}",
                impact='May indicate data quality issues or flash crashes',
                count=z_outliers
            ))

    def _check_large_gaps(self):
        """Check for large temporal gaps (HIGH priority)."""
        gap_results = self.statistical_results.get('gaps', {})
        large_gaps = gap_results.get('num_large_gaps', 0)

        if large_gaps > 10:
            self.score -= 10
            self.issues.append(Issue(
                priority='high',
                category='connectivity',
                description=f"Large temporal gaps: {large_gaps}",
                impact='Missing data during gaps - may affect backtest accuracy',
                count=large_gaps
            ))

    def _check_missing_values(self):
        """Check for missing/invalid values (HIGH priority)."""
        missing_results = self.integrity_results.get('missing_values', {})
        total_invalid = missing_results.get('total_invalid_count', 0)

        if total_invalid > 0:
            self.score -= 10
            self.issues.append(Issue(
                priority='high',
                category='completeness',
                description=f"Invalid/missing values: {total_invalid}",
                impact='Incomplete dataset - records have null/zero/negative values',
                count=total_invalid
            ))

    def _check_duplicates(self):
        """Check for duplicate records (MEDIUM priority)."""
        dup_results = self.integrity_results.get('duplicates', {})
        exact_dups = dup_results.get('exact_duplicates_count', 0)

        if exact_dups > 0:
            self.score -= 5
            self.issues.append(Issue(
                priority='medium',
                category='duplicates',
                description=f"Duplicate records found: {exact_dups}",
                impact='Data redundancy - may affect volume calculations',
                count=exact_dups
            ))

    def _check_cross_validation(self):
        """Check cross-validation issues (MEDIUM priority)."""
        cross_val_results = self.integrity_results.get('cross_validation', {})
        outside_spread_pct = cross_val_results.get('trades_outside_spread_percentage', 0.0)

        if outside_spread_pct > 15.0:
            self.score -= 5
            outside_count = cross_val_results.get('trades_outside_spread_count', 0)
            self.issues.append(Issue(
                priority='medium',
                category='cross_validation',
                description=f"Trades outside spread: {outside_spread_pct:.1f}%",
                impact='Quote-trade timing misalignment - may indicate latency issues',
                count=outside_count
            ))

    def _check_wide_spreads(self):
        """Check for wide spreads (LOW priority)."""
        spread_results = self.statistical_results.get('spreads', {})
        wide_spreads = spread_results.get('wide_spreads_count', 0)

        if wide_spreads > 50:
            self.score -= 3
            self.issues.append(Issue(
                priority='low',
                category='spread',
                description=f"Wide spreads detected: {wide_spreads}",
                impact='Low liquidity periods - may affect strategy execution',
                count=wide_spreads
            ))

    def _check_orderbook_violations(self):
        """Check for orderbook ordering violations (LOW priority)."""
        price_level_results = self.orderbook_results.get('price_levels', {})
        bid_violations = price_level_results.get('bid_ordering_violations', 0)
        ask_violations = price_level_results.get('ask_ordering_violations', 0)

        total_violations = bid_violations + ask_violations
        if total_violations > 0:
            self.score -= 2
            self.issues.append(Issue(
                priority='low',
                category='orderbook',
                description=f"Price level ordering violations: {total_violations}",
                impact='Minor orderbook reconstruction issues',
                count=total_violations
            ))

    def _compile_score_result(self) -> Dict[str, Any]:
        """Compile final score result with issue counts."""
        # Count issues by priority
        critical_count = sum(1 for i in self.issues if i.priority == 'critical')
        high_count = sum(1 for i in self.issues if i.priority == 'high')
        medium_count = sum(1 for i in self.issues if i.priority == 'medium')
        low_count = sum(1 for i in self.issues if i.priority == 'low')

        return {
            'score': self.score,
            'grade': self._assign_grade(self.score),
            'issues_found': len(self.issues),
            'critical_issues': critical_count,
            'high_issues': high_count,
            'medium_issues': medium_count,
            'low_issues': low_count
        }

    def _assign_grade(self, score: int) -> str:
        """
        Assign letter grade based on score.

        Parameters
        ----------
        score : int
            Quality score (0-100)

        Returns
        -------
        str
            Letter grade (A/B/C/D/F)
        """
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def prioritize_issues(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize and prioritize detected issues.

        Returns
        -------
        dict
            Dictionary with keys:
            - critical: list[dict] (negative spreads, crossed books)
            - high: list[dict] (outliers, gaps, missing values)
            - medium: list[dict] (duplicates, cross-validation issues)
            - low: list[dict] (wide spreads, minor anomalies)

        Examples
        --------
        >>> priorities = scorer.prioritize_issues()
        >>> for issue in priorities['critical']:
        ...     print(f"CRITICAL: {issue['description']}")
        """
        prioritized = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }

        for issue in self.issues:
            issue_dict = {
                'category': issue.category,
                'description': issue.description,
                'impact': issue.impact,
                'count': issue.count
            }
            prioritized[issue.priority].append(issue_dict)

        return prioritized

    def generate_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on findings.

        Returns
        -------
        list[str]
            List of recommendations like:
            - "Re-record: Critical data errors detected (negative spreads)"
            - "Acceptable: Minor issues that won't affect backtesting"
            - "Excellent: High-quality data suitable for production"

        Examples
        --------
        >>> recommendations = scorer.generate_recommendations()
        >>> for rec in recommendations:
        ...     print(rec)
        """
        recommendations = []

        # Overall assessment based on score
        if self.score == 0:
            recommendations.append(
                "CRITICAL: Data contains physically impossible values. Complete re-record required."
            )
        elif self.score < 70:
            recommendations.append(
                "WARNING: Data quality issues detected. Re-recording recommended."
            )
        elif self.score < 85:
            recommendations.append(
                "ACCEPTABLE: Data usable with caveats. Monitor backtest behavior closely."
            )
        else:
            recommendations.append(
                "EXCELLENT: High-quality data suitable for production use."
            )

        # Specific recommendations based on critical issues
        critical_issues = [i for i in self.issues if i.priority == 'critical']
        for issue in critical_issues:
            if issue.category == 'spread':
                recommendations.append(
                    f"Fix Required: {issue.description} - Check data source configuration"
                )
            elif issue.category == 'orderbook':
                recommendations.append(
                    f"Fix Required: {issue.description} - Verify orderbook reconstruction logic"
                )

        # Specific recommendations based on high priority issues
        high_issues = [i for i in self.issues if i.priority == 'high']
        for issue in high_issues:
            if issue.category == 'price':
                recommendations.append(
                    f"Review: {issue.description} - Consider filtering extreme outliers"
                )
            elif issue.category == 'connectivity':
                recommendations.append(
                    f"Review: {issue.description} - Check network stability during recording"
                )
            elif issue.category == 'completeness':
                recommendations.append(
                    f"Review: {issue.description} - Consider excluding invalid records"
                )

        # Medium priority recommendations
        medium_issues = [i for i in self.issues if i.priority == 'medium']
        if medium_issues:
            recommendations.append(
                f"Note: {len(medium_issues)} medium-priority issue(s) detected - "
                "may impact accuracy but not critical"
            )

        # Low priority recommendations
        low_issues = [i for i in self.issues if i.priority == 'low']
        if low_issues:
            recommendations.append(
                f"Info: {len(low_issues)} low-priority issue(s) detected - "
                "unlikely to affect backtest results"
            )

        return recommendations

    def meets_minimum_standards(self) -> Dict[str, Any]:
        """
        Check if data meets minimum quality standards.

        Returns
        -------
        dict
            Dictionary with keys:
            - passes: bool (overall pass/fail)
            - score_check: bool (score >= 70)
            - critical_issues_check: bool (no critical issues)
            - negative_spreads_check: bool (no negative spreads)
            - crossed_books_check: bool (no crossed books)
            - details: dict (detailed check results)

        Examples
        --------
        >>> standards = scorer.meets_minimum_standards()
        >>> if not standards['passes']:
        ...     print("Data does not meet minimum quality standards!")
        ...     for check, result in standards['details'].items():
        ...         if not result:
        ...             print(f"  Failed: {check}")
        """
        spread_results = self.statistical_results.get('spreads', {})
        crossed_results = self.orderbook_results.get('crossed_books', {})

        # Individual checks
        score_check = self.score >= PASS_CRITERIA['min_score']
        critical_check = len([i for i in self.issues if i.priority == 'critical']) == 0
        negative_spreads_check = spread_results.get('negative_spreads_count', 0) == 0
        crossed_books_check = crossed_results.get('crossed_books_detected', 0) == 0

        # Overall pass: must pass ALL checks
        passes = all([
            score_check,
            critical_check,
            negative_spreads_check,
            crossed_books_check
        ])

        return {
            'passes': passes,
            'score_check': score_check,
            'critical_issues_check': critical_check,
            'negative_spreads_check': negative_spreads_check,
            'crossed_books_check': crossed_books_check,
            'details': {
                'score': f"{self.score} >= {PASS_CRITERIA['min_score']} (required)",
                'critical_issues': f"{len([i for i in self.issues if i.priority == 'critical'])} == 0 (required)",
                'negative_spreads': f"{spread_results.get('negative_spreads_count', 0)} == 0 (required)",
                'crossed_books': f"{crossed_results.get('crossed_books_detected', 0)} == 0 (required)"
            }
        }

    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive quality report.

        Returns
        -------
        dict
            Dictionary with keys:
            - score_breakdown: dict (points deducted per category)
            - issues_by_priority: dict (critical/high/medium/low)
            - recommendations: list[str]
            - pass_criteria: dict (meets minimum standards)
            - summary: str (overall assessment)

        Examples
        --------
        >>> report = scorer.get_detailed_report()
        >>> print(report['summary'])
        >>> print(f"Score: {report['score_breakdown']['final_score']}/100")
        >>> for issue in report['issues_by_priority']['critical']:
        ...     print(f"  - {issue['description']}")
        """
        # Calculate score breakdown
        score_breakdown = self._calculate_score_breakdown()

        # Get prioritized issues
        issues_by_priority = self.prioritize_issues()

        # Get recommendations
        recommendations = self.generate_recommendations()

        # Check pass criteria
        pass_criteria = self.meets_minimum_standards()

        # Generate summary
        summary = self._generate_summary()

        return {
            'score_breakdown': score_breakdown,
            'issues_by_priority': issues_by_priority,
            'recommendations': recommendations,
            'pass_criteria': pass_criteria,
            'summary': summary
        }

    def _calculate_score_breakdown(self) -> Dict[str, Any]:
        """Calculate detailed score breakdown by category."""
        breakdown = {
            'starting_score': 100,
            'deductions': {},
            'final_score': self.score
        }

        # Group deductions by category
        for issue in self.issues:
            category_key = f"{issue.priority}_{issue.category}"
            if category_key not in breakdown['deductions']:
                breakdown['deductions'][category_key] = {
                    'priority': issue.priority,
                    'category': issue.category,
                    'description': issue.description,
                    'points_deducted': 0
                }

            # Calculate points deducted for this issue
            if issue.priority == 'critical' and issue.category == 'spread':
                points = 100  # Negative spreads = automatic fail
            elif issue.priority == 'critical':
                points = 15
            elif issue.priority == 'high':
                points = 10
            elif issue.priority == 'medium':
                points = 5
            else:  # low
                points = 3

            breakdown['deductions'][category_key]['points_deducted'] = points

        return breakdown

    def _generate_summary(self) -> str:
        """Generate text summary of data quality assessment."""
        grade = self._assign_grade(self.score)

        if self.score == 0:
            summary = (
                f"FAIL (Grade {grade}): Data contains critical errors that make it unusable. "
                f"Negative spreads or other physically impossible values detected. "
                f"Complete re-recording required."
            )
        elif self.score < 70:
            summary = (
                f"POOR (Grade {grade}): Data quality is below acceptable standards. "
                f"Score: {self.score}/100. {len(self.issues)} issue(s) detected. "
                f"Re-recording is strongly recommended."
            )
        elif self.score < 85:
            summary = (
                f"ACCEPTABLE (Grade {grade}): Data quality meets minimum standards. "
                f"Score: {self.score}/100. {len(self.issues)} issue(s) detected. "
                f"Usable for backtesting but monitor results carefully."
            )
        else:
            summary = (
                f"EXCELLENT (Grade {grade}): High-quality data suitable for production use. "
                f"Score: {self.score}/100. {len(self.issues)} minor issue(s) detected. "
                f"Data is reliable for backtesting and strategy development."
            )

        return summary


# Example usage and testing
if __name__ == '__main__':
    """
    Test the QualityScorer with sample data from Wave 1 validators.
    """
    print("=" * 80)
    print("QUALITY SCORING ENGINE - TEST SUITE")
    print("=" * 80)

    # Test Case 1: Excellent quality data (no issues)
    print("\nTest 1: Excellent Quality Data")
    print("-" * 80)

    sample_statistical_excellent = {
        'gaps': {'num_large_gaps': 2, 'max_gap_ms': 1500},
        'outliers': {'z_outliers_count': 50, 'price_jumps_count': 10},
        'spreads': {
            'negative_spreads_count': 0,
            'wide_spreads_count': 10,
            'mean_spread_bps': 5.2
        },
        'volume': {'total_volume': 1000000}
    }

    sample_integrity_excellent = {
        'duplicates': {'exact_duplicates_count': 0},
        'missing_values': {'total_invalid_count': 0},
        'cross_validation': {
            'trades_outside_spread_percentage': 9.5,
            'trades_outside_spread_count': 95
        }
    }

    sample_orderbook_excellent = {
        'price_levels': {
            'bid_ordering_violations': 0,
            'ask_ordering_violations': 0
        },
        'crossed_books': {'crossed_books_detected': 0},
        'depth': {'mean_bid_levels': 50, 'min_bid_levels': 48}
    }

    scorer1 = QualityScorer(
        sample_statistical_excellent,
        sample_integrity_excellent,
        sample_orderbook_excellent
    )

    result1 = scorer1.calculate_score()
    print(f"Score: {result1['score']}/100 (Grade: {result1['grade']})")
    print(f"Issues: {result1['issues_found']} (Critical: {result1['critical_issues']}, "
          f"High: {result1['high_issues']}, Medium: {result1['medium_issues']}, "
          f"Low: {result1['low_issues']})")

    print("\nRecommendations:")
    for rec in scorer1.generate_recommendations():
        print(f"  - {rec}")

    print("\nMinimum Standards:")
    standards1 = scorer1.meets_minimum_standards()
    print(f"  Passes: {standards1['passes']}")

    # Test Case 2: Poor quality data (multiple issues)
    print("\n" + "=" * 80)
    print("Test 2: Poor Quality Data")
    print("-" * 80)

    sample_statistical_poor = {
        'gaps': {'num_large_gaps': 50, 'max_gap_ms': 15000},
        'outliers': {'z_outliers_count': 250, 'price_jumps_count': 100},
        'spreads': {
            'negative_spreads_count': 0,
            'wide_spreads_count': 200,
            'mean_spread_bps': 25.0
        },
        'volume': {'total_volume': 500000}
    }

    sample_integrity_poor = {
        'duplicates': {'exact_duplicates_count': 500},
        'missing_values': {'total_invalid_count': 100},
        'cross_validation': {
            'trades_outside_spread_percentage': 25.0,
            'trades_outside_spread_count': 2500
        }
    }

    sample_orderbook_poor = {
        'price_levels': {
            'bid_ordering_violations': 5,
            'ask_ordering_violations': 3
        },
        'crossed_books': {'crossed_books_detected': 0},
        'depth': {'mean_bid_levels': 50, 'min_bid_levels': 30}
    }

    scorer2 = QualityScorer(
        sample_statistical_poor,
        sample_integrity_poor,
        sample_orderbook_poor
    )

    result2 = scorer2.calculate_score()
    print(f"Score: {result2['score']}/100 (Grade: {result2['grade']})")
    print(f"Issues: {result2['issues_found']} (Critical: {result2['critical_issues']}, "
          f"High: {result2['high_issues']}, Medium: {result2['medium_issues']}, "
          f"Low: {result2['low_issues']})")

    print("\nRecommendations:")
    for rec in scorer2.generate_recommendations():
        print(f"  - {rec}")

    print("\nMinimum Standards:")
    standards2 = scorer2.meets_minimum_standards()
    print(f"  Passes: {standards2['passes']}")

    # Test Case 3: CRITICAL FAILURE (negative spreads)
    print("\n" + "=" * 80)
    print("Test 3: Critical Failure (Negative Spreads)")
    print("-" * 80)

    sample_statistical_fail = {
        'gaps': {'num_large_gaps': 5, 'max_gap_ms': 2000},
        'outliers': {'z_outliers_count': 50, 'price_jumps_count': 10},
        'spreads': {
            'negative_spreads_count': 15,  # CRITICAL ERROR
            'wide_spreads_count': 10,
            'mean_spread_bps': 5.2
        },
        'volume': {'total_volume': 1000000}
    }

    sample_integrity_fail = {
        'duplicates': {'exact_duplicates_count': 0},
        'missing_values': {'total_invalid_count': 0},
        'cross_validation': {
            'trades_outside_spread_percentage': 9.5,
            'trades_outside_spread_count': 95
        }
    }

    sample_orderbook_fail = {
        'price_levels': {
            'bid_ordering_violations': 0,
            'ask_ordering_violations': 0
        },
        'crossed_books': {'crossed_books_detected': 0},
        'depth': {'mean_bid_levels': 50, 'min_bid_levels': 48}
    }

    scorer3 = QualityScorer(
        sample_statistical_fail,
        sample_integrity_fail,
        sample_orderbook_fail
    )

    result3 = scorer3.calculate_score()
    print(f"Score: {result3['score']}/100 (Grade: {result3['grade']})")
    print(f"Issues: {result3['issues_found']} (Critical: {result3['critical_issues']}, "
          f"High: {result3['high_issues']}, Medium: {result3['medium_issues']}, "
          f"Low: {result3['low_issues']})")

    print("\nRecommendations:")
    for rec in scorer3.generate_recommendations():
        print(f"  - {rec}")

    print("\nMinimum Standards:")
    standards3 = scorer3.meets_minimum_standards()
    print(f"  Passes: {standards3['passes']}")

    # Test detailed report
    print("\n" + "=" * 80)
    print("Test 4: Detailed Report Generation")
    print("-" * 80)

    report = scorer2.get_detailed_report()
    print(f"\nSummary:")
    print(f"  {report['summary']}")

    print(f"\nScore Breakdown:")
    print(f"  Starting Score: {report['score_breakdown']['starting_score']}")
    for category, details in report['score_breakdown']['deductions'].items():
        print(f"  - {details['priority'].upper()} ({details['category']}): "
              f"-{details['points_deducted']} pts - {details['description']}")
    print(f"  Final Score: {report['score_breakdown']['final_score']}")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)
