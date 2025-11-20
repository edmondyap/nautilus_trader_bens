"""
HTML Report Generator - Advanced Validation System

Trading Engines Project - Wave 3 Parallel Execution
Location: my_trading_system/validation/modules/html_report.py
Author: Benjamin Ang / Claude Code (Subagent 6)
Created: 2025-11-19

Production-grade HTML report generation for market data validation results.

Generates professional, self-contained HTML validation reports with:
- Executive summary with color-coded quality score
- Detailed statistical analysis tables
- Integrity check results
- Orderbook validation findings
- Embedded visualizations (base64 PNG, inline Plotly HTML)
- Responsive layout with print support
- Professional styling

Features:
---------
- Single HTML file (self-contained)
- All images embedded as base64 data URLs
- Plotly charts embedded as iframes
- Color-coded quality indicators (A=green, B=light-green, C=orange, D/F=red)
- Responsive design (desktop, tablet, print)
- Professional typography and spacing
- Printable format (CSS @media print)
- File size optimized (<10MB typical)
- No external dependencies (runs in any browser)

Report Structure:
-----------------
1. Header: Recording ID, generation timestamp, metadata
2. Executive Summary: Score badge, grade, recommendations
3. Quality Score: Breakdown by category, issues by priority
4. Statistical Analysis: Gaps, outliers, spreads with charts
5. Integrity Checks: Duplicates, missing values, cross-validation
6. Orderbook Validation: Crossed books, depth, price levels
7. Visualizations: Price charts, spreads, volume, orderbook heatmap
8. Footer: System info, report version

Examples
--------
>>> from pathlib import Path
>>> generator = HTMLReportGenerator(
...     validation_results={
...         'statistical': statistical_results,
...         'integrity': integrity_results,
...         'orderbook': orderbook_results,
...         'quality_score': quality_score_results
...     },
...     viz_paths={
...         'price_timeseries': Path('charts/price_timeseries.png'),
...         'spread_distribution': Path('charts/spread_distribution.png'),
...         'volume_profile': Path('charts/volume_profile.png'),
...         'orderbook_heatmap': Path('charts/orderbook_heatmap.html')
...     },
...     recording_dir=Path('data/recordings/20251119-152837'),
...     output_path=Path('reports/validation_report_20251119.html')
... )
>>> report_path = generator.generate_report()
>>> print(f"Report generated: {report_path}")
"""

import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class HTMLReportGenerator:
    """
    Generates professional HTML validation reports.

    Creates self-contained HTML reports with embedded visualizations,
    professional styling, and comprehensive validation results.

    Parameters
    ----------
    validation_results : dict
        Complete validation results with keys:
        - statistical: dict (StatisticalAnalyzer results)
        - integrity: dict (IntegrityChecker results)
        - orderbook: dict (OrderbookValidator results)
        - quality_score: dict (QualityScorer results with score, grade, issues)
    viz_paths : dict
        Paths to visualization files:
        - price_timeseries_path: str or Path (PNG file)
        - spread_distribution_path: str or Path (PNG file)
        - volume_profile_path: str or Path (PNG file)
        - orderbook_heatmap_path: str or Path (HTML file)
    recording_dir : Path
        Path to recording directory (for metadata extraction)
    output_path : Path
        Where to save the HTML report

    Attributes
    ----------
    validation_results : dict
        Validation results dictionary
    viz_paths : dict
        Visualization file paths
    recording_dir : Path
        Recording directory path
    output_path : Path
        Output HTML file path
    recording_id : str
        Extracted recording ID from directory name

    Examples
    --------
    >>> generator = HTMLReportGenerator(
    ...     validation_results=results,
    ...     viz_paths=charts,
    ...     recording_dir=Path('data/recordings/20251119-152837'),
    ...     output_path=Path('report.html')
    ... )
    >>> report_path = generator.generate_report()
    """

    def __init__(
        self,
        validation_results: Dict[str, Any],
        viz_paths: Dict[str, Any],
        recording_dir: Path,
        output_path: Path
    ):
        """
        Initialize HTML report generator.

        Parameters
        ----------
        validation_results : dict
            Complete validation results
        viz_paths : dict
            Paths to visualization files
        recording_dir : Path
            Recording directory
        output_path : Path
            Output file path
        """
        self.validation_results = validation_results
        self.viz_paths = viz_paths
        self.recording_dir = Path(recording_dir)
        self.output_path = Path(output_path)

        # Extract recording ID from directory name
        self.recording_id = self.recording_dir.name

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_report(self) -> str:
        """
        Generate complete HTML validation report.

        Creates a self-contained HTML file with all validation results
        and embedded visualizations.

        Returns
        -------
        str
            Path to generated HTML file

        Examples
        --------
        >>> report_path = generator.generate_report()
        >>> print(f"Report saved: {report_path}")
        """
        # Build complete HTML document
        html_content = self._generate_html()

        # Write to file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(self.output_path)

    def _generate_html(self) -> str:
        """
        Build complete HTML document.

        Returns
        -------
        str
            Full HTML content
        """
        # Extract results for easier access
        quality_results = self.validation_results.get('quality_score', {})
        score = quality_results.get('score', 0)
        grade = quality_results.get('grade', 'F')

        # Generate report sections
        header_html = self._generate_header()
        summary_html = self._generate_executive_summary()
        quality_html = self._generate_quality_section()
        statistical_html = self._generate_statistical_section()
        integrity_html = self._generate_integrity_section()
        orderbook_html = self._generate_orderbook_section()
        visualizations_html = self._generate_visualizations_section()
        footer_html = self._generate_footer()

        # Build complete HTML document
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Validation Report - {self.recording_id}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        {header_html}
        {summary_html}
        {quality_html}
        {statistical_html}
        {integrity_html}
        {orderbook_html}
        {visualizations_html}
        {footer_html}
    </div>
</body>
</html>"""

        return html

    def _get_css_styles(self) -> str:
        """
        Get CSS styling for the report.

        Returns
        -------
        str
            CSS stylesheet content
        """
        return """
        /* Color Palette */
        :root {
            --color-excellent: #2E7D32;   /* Dark green (A) */
            --color-good: #4CAF50;        /* Green (B) */
            --color-acceptable: #FFA726;  /* Orange (C) */
            --color-poor: #EF5350;        /* Red (D) */
            --color-fail: #C62828;        /* Dark red (F) */
            --color-primary: #1976D2;     /* Blue (primary) */
            --color-secondary: #424242;   /* Dark gray */
            --color-light-gray: #f5f5f5;
            --color-border: #ddd;
        }

        /* Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: var(--color-light-gray);
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border-radius: 5px;
        }

        /* Header Styles */
        header {
            border-bottom: 4px solid var(--color-primary);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        header h1 {
            color: var(--color-primary);
            font-size: 32px;
            margin-bottom: 10px;
        }

        .metadata {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 15px;
        }

        .metadata p {
            color: var(--color-secondary);
            font-size: 14px;
        }

        .metadata strong {
            font-weight: 600;
        }

        /* Section Styles */
        section {
            margin-bottom: 40px;
        }

        section h2 {
            color: var(--color-primary);
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--color-light-gray);
        }

        section h3 {
            color: var(--color-secondary);
            font-size: 18px;
            margin-top: 25px;
            margin-bottom: 15px;
        }

        /* Executive Summary */
        .summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 40px;
        }

        .summary h2 {
            color: white;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        }

        /* Score Badge */
        .score-badge {
            display: inline-block;
            font-size: 48px;
            font-weight: bold;
            padding: 25px 50px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .score-badge.grade-a {
            background: var(--color-excellent);
            color: white;
        }

        .score-badge.grade-b {
            background: var(--color-good);
            color: white;
        }

        .score-badge.grade-c {
            background: var(--color-acceptable);
            color: white;
        }

        .score-badge.grade-d {
            background: var(--color-poor);
            color: white;
        }

        .score-badge.grade-f {
            background: var(--color-fail);
            color: white;
        }

        .score-badge .grade-text {
            display: block;
            font-size: 24px;
            margin-top: 10px;
            opacity: 0.9;
        }

        /* Recommendations */
        .recommendations {
            margin-top: 25px;
        }

        .recommendations h3 {
            color: white;
            font-size: 20px;
            margin-bottom: 15px;
        }

        .recommendations ul {
            list-style: none;
            padding: 0;
        }

        .recommendations li {
            background: rgba(255, 255, 255, 0.1);
            padding: 12px 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid rgba(255, 255, 255, 0.5);
        }

        .recommendations li strong {
            display: block;
            margin-bottom: 5px;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        table caption {
            font-size: 16px;
            font-weight: 600;
            text-align: left;
            padding: 10px;
            color: var(--color-secondary);
        }

        table th {
            background: var(--color-primary);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }

        table td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--color-border);
        }

        table tr:hover {
            background: var(--color-light-gray);
        }

        table tr:last-child td {
            border-bottom: none;
        }

        /* Status Badges */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.critical {
            background: var(--color-fail);
            color: white;
        }

        .status-badge.high {
            background: var(--color-poor);
            color: white;
        }

        .status-badge.medium {
            background: var(--color-acceptable);
            color: white;
        }

        .status-badge.low {
            background: var(--color-good);
            color: white;
        }

        .status-badge.pass {
            background: var(--color-excellent);
            color: white;
        }

        .status-badge.fail {
            background: var(--color-fail);
            color: white;
        }

        /* Charts */
        .chart {
            margin: 30px 0;
        }

        .chart h3 {
            color: var(--color-secondary);
            font-size: 18px;
            margin-bottom: 15px;
        }

        .chart img {
            max-width: 100%;
            height: auto;
            border: 1px solid var(--color-border);
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .chart iframe {
            width: 100%;
            height: 600px;
            border: 1px solid var(--color-border);
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        /* Info Boxes */
        .info-box {
            background: var(--color-light-gray);
            border-left: 4px solid var(--color-primary);
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .info-box.warning {
            background: #FFF3E0;
            border-left-color: var(--color-acceptable);
        }

        .info-box.error {
            background: #FFEBEE;
            border-left-color: var(--color-fail);
        }

        .info-box.success {
            background: #E8F5E9;
            border-left-color: var(--color-excellent);
        }

        /* Footer */
        footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid var(--color-light-gray);
            text-align: center;
            color: #777;
            font-size: 14px;
        }

        footer p {
            margin: 5px 0;
        }

        /* Print Styles */
        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                padding: 20px;
            }

            section {
                page-break-inside: avoid;
            }

            .chart {
                page-break-inside: avoid;
            }

            table {
                page-break-inside: avoid;
            }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }

            header h1 {
                font-size: 24px;
            }

            .score-badge {
                font-size: 36px;
                padding: 20px 40px;
            }

            .metadata {
                flex-direction: column;
                gap: 10px;
            }

            table {
                font-size: 14px;
            }

            table th, table td {
                padding: 8px;
            }
        }
        """

    def _generate_header(self) -> str:
        """Generate header section."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        return f"""
        <header>
            <h1>Market Data Validation Report</h1>
            <div class="metadata">
                <p><strong>Recording ID:</strong> {self.recording_id}</p>
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Report Version:</strong> 1.0.0</p>
            </div>
        </header>
        """

    def _generate_executive_summary(self) -> str:
        """Generate executive summary section."""
        quality_results = self.validation_results.get('quality_score', {})
        score = quality_results.get('score', 0)
        grade = quality_results.get('grade', 'F')
        issues_found = quality_results.get('issues_found', 0)

        # Get detailed report for recommendations
        detailed_report = quality_results.get('detailed_report', {})
        recommendations = detailed_report.get('recommendations', [])

        # Format score badge
        score_badge = self._format_score_badge(score, grade)

        # Format recommendations
        recommendations_html = "<ul>"
        for rec in recommendations:
            recommendations_html += f"<li>{rec}</li>"
        recommendations_html += "</ul>"

        return f"""
        <section class="summary">
            <h2>Executive Summary</h2>
            {score_badge}
            <div class="recommendations">
                <h3>Recommendations</h3>
                {recommendations_html}
            </div>
            <div style="margin-top: 20px;">
                <p><strong>Total Issues Found:</strong> {issues_found}</p>
            </div>
        </section>
        """

    def _format_score_badge(self, score: int, grade: str) -> str:
        """
        Create visual score badge with color coding.

        Parameters
        ----------
        score : int
            Quality score (0-100)
        grade : str
            Letter grade (A/B/C/D/F)

        Returns
        -------
        str
            HTML badge markup
        """
        grade_class = f"grade-{grade.lower()}"

        return f"""
        <div class="score-badge {grade_class}">
            {score}/100
            <span class="grade-text">Grade: {grade}</span>
        </div>
        """

    def _generate_quality_section(self) -> str:
        """Generate quality score breakdown section."""
        quality_results = self.validation_results.get('quality_score', {})
        detailed_report = quality_results.get('detailed_report', {})

        # Score breakdown table
        score_breakdown = detailed_report.get('score_breakdown', {})
        breakdown_html = self._format_score_breakdown_table(score_breakdown)

        # Issues by priority table
        issues_by_priority = detailed_report.get('issues_by_priority', {})
        issues_html = self._format_issues_by_priority_table(issues_by_priority)

        # Pass criteria table
        pass_criteria = detailed_report.get('pass_criteria', {})
        criteria_html = self._format_pass_criteria_table(pass_criteria)

        return f"""
        <section class="quality-score">
            <h2>Data Quality Score</h2>

            <h3>Score Breakdown</h3>
            {breakdown_html}

            <h3>Issues by Priority</h3>
            {issues_html}

            <h3>Pass Criteria Check</h3>
            {criteria_html}
        </section>
        """

    def _format_score_breakdown_table(self, score_breakdown: Dict[str, Any]) -> str:
        """Format score breakdown as HTML table."""
        starting_score = score_breakdown.get('starting_score', 100)
        final_score = score_breakdown.get('final_score', 0)
        deductions = score_breakdown.get('deductions', {})

        html = f"""
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Description</th>
                    <th>Points Deducted</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="3"><strong>Starting Score</strong></td>
                    <td><strong>{starting_score}</strong></td>
                </tr>
        """

        for category, details in deductions.items():
            priority = details['priority']
            category_name = details['category']
            description = details['description']
            points = details['points_deducted']

            priority_badge = f'<span class="status-badge {priority}">{priority.upper()}</span>'

            html += f"""
                <tr>
                    <td>{category_name.title()}</td>
                    <td>{priority_badge}</td>
                    <td>{description}</td>
                    <td>-{points}</td>
                </tr>
            """

        html += f"""
                <tr style="border-top: 2px solid var(--color-primary);">
                    <td colspan="3"><strong>Final Score</strong></td>
                    <td><strong>{final_score}</strong></td>
                </tr>
            </tbody>
        </table>
        """

        return html

    def _format_issues_by_priority_table(self, issues_by_priority: Dict[str, Any]) -> str:
        """Format issues by priority as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Priority</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Impact</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
        """

        if not issues_by_priority:
            html += """
                <tr>
                    <td colspan="5" style="text-align: center;">No issues detected</td>
                </tr>
            """
        else:
            for priority in ['critical', 'high', 'medium', 'low']:
                issues = issues_by_priority.get(priority, [])
                for issue in issues:
                    priority_badge = f'<span class="status-badge {priority}">{priority.upper()}</span>'
                    html += f"""
                <tr>
                    <td>{priority_badge}</td>
                    <td>{issue['category'].title()}</td>
                    <td>{issue['description']}</td>
                    <td>{issue['impact']}</td>
                    <td>{issue['count']}</td>
                </tr>
                    """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_pass_criteria_table(self, pass_criteria: Dict[str, Any]) -> str:
        """Format pass criteria check as HTML table."""
        passes = pass_criteria.get('passes', False)
        details = pass_criteria.get('details', {})

        status_badge = f'<span class="status-badge {"pass" if passes else "fail"}">{"PASS" if passes else "FAIL"}</span>'

        html = f"""
        <div class="info-box {"success" if passes else "error"}">
            <p><strong>Overall Status:</strong> {status_badge}</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Check</th>
                    <th>Result</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        """

        checks = {
            'score': (pass_criteria.get('score_check', False), 'Score >= 70'),
            'critical_issues': (pass_criteria.get('critical_issues_check', False), 'No critical issues'),
            'negative_spreads': (pass_criteria.get('negative_spreads_check', False), 'No negative spreads'),
            'crossed_books': (pass_criteria.get('crossed_books_check', False), 'No crossed orderbooks')
        }

        for check_name, (passed, description) in checks.items():
            status_badge = f'<span class="status-badge {"pass" if passed else "fail"}">{"PASS" if passed else "FAIL"}</span>'
            detail_text = details.get(check_name, 'N/A')

            html += f"""
                <tr>
                    <td>{description}</td>
                    <td>{detail_text}</td>
                    <td>{status_badge}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_statistical_section(self) -> str:
        """Generate statistical analysis section."""
        statistical = self.validation_results.get('statistical', {})

        # Gap analysis
        gaps = statistical.get('gaps', {})
        gap_html = self._format_gap_analysis_table(gaps)

        # Outlier analysis
        outliers = statistical.get('outliers', {})
        outlier_html = self._format_outlier_analysis_table(outliers)

        # Spread analysis
        spreads = statistical.get('spreads', {})
        spread_html = self._format_spread_analysis_table(spreads)

        return f"""
        <section class="statistical">
            <h2>Statistical Analysis</h2>

            <h3>Temporal Gap Analysis</h3>
            {gap_html}

            <h3>Price Outlier Detection</h3>
            {outlier_html}

            <h3>Bid-Ask Spread Analysis</h3>
            {spread_html}
        </section>
        """

    def _format_gap_analysis_table(self, gaps: Dict[str, Any]) -> str:
        """Format gap analysis as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'num_large_gaps': 'Large Gaps Detected',
            'max_gap_ms': 'Maximum Gap (ms)',
            'mean_gap_ms': 'Mean Gap (ms)',
            'median_gap_ms': 'Median Gap (ms)',
            'std_gap_ms': 'Gap Std Dev (ms)'
        }

        for key, label in metrics.items():
            value = gaps.get(key, 'N/A')
            if isinstance(value, (int, float)):
                if key.endswith('_ms'):
                    value = f"{value:.2f}"
                else:
                    value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_outlier_analysis_table(self, outliers: Dict[str, Any]) -> str:
        """Format outlier analysis as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'z_outliers_count': 'Z-Score Outliers',
            'price_jumps_count': 'Price Jumps Detected',
            'max_price_jump_pct': 'Max Price Jump (%)',
            'outlier_percentage': 'Outlier Percentage (%)'
        }

        for key, label in metrics.items():
            value = outliers.get(key, 'N/A')
            if isinstance(value, (int, float)):
                if key.endswith('_pct') or key.endswith('_percentage'):
                    value = f"{value:.2f}%"
                else:
                    value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_spread_analysis_table(self, spreads: Dict[str, Any]) -> str:
        """Format spread analysis as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'negative_spreads_count': 'Negative Spreads',
            'wide_spreads_count': 'Wide Spreads (>threshold)',
            'mean_spread_bps': 'Mean Spread (bps)',
            'median_spread_bps': 'Median Spread (bps)',
            'std_spread_bps': 'Spread Std Dev (bps)',
            'min_spread_bps': 'Minimum Spread (bps)',
            'max_spread_bps': 'Maximum Spread (bps)'
        }

        for key, label in metrics.items():
            value = spreads.get(key, 'N/A')
            if isinstance(value, (int, float)):
                if key.endswith('_bps'):
                    value = f"{value:.2f}"
                else:
                    value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_integrity_section(self) -> str:
        """Generate integrity checks section."""
        integrity = self.validation_results.get('integrity', {})

        # Duplicate detection
        duplicates = integrity.get('duplicates', {})
        dup_html = self._format_duplicate_results_table(duplicates)

        # Missing values
        missing = integrity.get('missing_values', {})
        missing_html = self._format_missing_values_table(missing)

        # Cross-validation
        cross_val = integrity.get('cross_validation', {})
        cross_val_html = self._format_cross_validation_table(cross_val)

        return f"""
        <section class="integrity">
            <h2>Data Integrity Checks</h2>

            <h3>Duplicate Detection</h3>
            {dup_html}

            <h3>Missing/Invalid Values</h3>
            {missing_html}

            <h3>Cross-Validation (Quotes vs Trades)</h3>
            {cross_val_html}
        </section>
        """

    def _format_duplicate_results_table(self, duplicates: Dict[str, Any]) -> str:
        """Format duplicate detection results as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Check</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'exact_duplicates_count': 'Exact Duplicates',
            'timestamp_duplicates_count': 'Timestamp Duplicates'
        }

        for key, label in metrics.items():
            value = duplicates.get(key, 'N/A')
            if isinstance(value, int):
                value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_missing_values_table(self, missing: Dict[str, Any]) -> str:
        """Format missing values results as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Check</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'total_invalid_count': 'Total Invalid Records',
            'null_values_count': 'Null Values',
            'zero_price_count': 'Zero Prices',
            'negative_price_count': 'Negative Prices',
            'zero_size_count': 'Zero Sizes'
        }

        for key, label in metrics.items():
            value = missing.get(key, 'N/A')
            if isinstance(value, int):
                value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_cross_validation_table(self, cross_val: Dict[str, Any]) -> str:
        """Format cross-validation results as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'trades_outside_spread_count': 'Trades Outside Spread',
            'trades_outside_spread_percentage': 'Trades Outside Spread (%)',
            'trades_analyzed': 'Total Trades Analyzed'
        }

        for key, label in metrics.items():
            value = cross_val.get(key, 'N/A')
            if isinstance(value, (int, float)):
                if key.endswith('_percentage'):
                    value = f"{value:.2f}%"
                else:
                    value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_orderbook_section(self) -> str:
        """Generate orderbook validation section."""
        orderbook = self.validation_results.get('orderbook', {})

        # Price level validation
        price_levels = orderbook.get('price_levels', {})
        price_html = self._format_price_level_table(price_levels)

        # Crossed books detection
        crossed = orderbook.get('crossed_books', {})
        crossed_html = self._format_crossed_books_table(crossed)

        # Depth consistency
        depth = orderbook.get('depth', {})
        depth_html = self._format_depth_consistency_table(depth)

        return f"""
        <section class="orderbook">
            <h2>Orderbook Validation</h2>

            <h3>Price Level Ordering</h3>
            {price_html}

            <h3>Crossed Orderbook Detection</h3>
            {crossed_html}

            <h3>Depth Consistency</h3>
            {depth_html}
        </section>
        """

    def _format_price_level_table(self, price_levels: Dict[str, Any]) -> str:
        """Format price level validation results as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Check</th>
                    <th>Violations</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'bid_ordering_violations': 'Bid Ordering Violations',
            'ask_ordering_violations': 'Ask Ordering Violations',
            'snapshots_analyzed': 'Snapshots Analyzed'
        }

        for key, label in metrics.items():
            value = price_levels.get(key, 'N/A')
            if isinstance(value, int):
                value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_crossed_books_table(self, crossed: Dict[str, Any]) -> str:
        """Format crossed orderbook detection results as HTML table."""
        crossed_count = crossed.get('crossed_books_detected', 0)

        if crossed_count > 0:
            info_box_class = "error"
            message = f"CRITICAL: {crossed_count} crossed orderbook instances detected!"
        else:
            info_box_class = "success"
            message = "No crossed orderbooks detected - data integrity confirmed."

        html = f"""
        <div class="info-box {info_box_class}">
            <p><strong>{message}</strong></p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = {
            'crossed_books_detected': 'Crossed Orderbooks',
            'snapshots_checked': 'Snapshots Checked',
            'first_crossed_timestamp': 'First Crossed Timestamp'
        }

        for key, label in metrics.items():
            value = crossed.get(key, 'N/A')
            if isinstance(value, int):
                value = f"{value:,}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_depth_consistency_table(self, depth: Dict[str, Any]) -> str:
        """Format depth consistency results as HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Bid Side</th>
                    <th>Ask Side</th>
                </tr>
            </thead>
            <tbody>
        """

        metrics = [
            ('mean_bid_levels', 'mean_ask_levels', 'Mean Depth (levels)'),
            ('min_bid_levels', 'min_ask_levels', 'Minimum Depth'),
            ('max_bid_levels', 'max_ask_levels', 'Maximum Depth'),
            ('std_bid_levels', 'std_ask_levels', 'Std Dev')
        ]

        for bid_key, ask_key, label in metrics:
            bid_value = depth.get(bid_key, 'N/A')
            ask_value = depth.get(ask_key, 'N/A')

            if isinstance(bid_value, (int, float)):
                bid_value = f"{bid_value:.1f}"
            if isinstance(ask_value, (int, float)):
                ask_value = f"{ask_value:.1f}"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{bid_value}</td>
                    <td>{ask_value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_visualizations_section(self) -> str:
        """Generate visualizations section with embedded charts."""
        html = """
        <section class="visualizations">
            <h2>Data Visualizations</h2>
        """

        # Price time series
        if 'price_timeseries' in self.viz_paths:
            price_path = self.viz_paths['price_timeseries']
            if Path(price_path).exists():
                price_img = self._embed_image(str(price_path))
                html += f"""
            <div class="chart">
                <h3>Price Evolution Over Time</h3>
                <img src="{price_img}" alt="Price Time Series">
                <p style="color: #777; font-size: 14px; margin-top: 10px;">
                    Bid/ask prices with trade execution overlay showing market dynamics and spread evolution.
                </p>
            </div>
                """

        # Spread distribution
        if 'spread_distribution' in self.viz_paths:
            spread_path = self.viz_paths['spread_distribution']
            if Path(spread_path).exists():
                spread_img = self._embed_image(str(spread_path))
                html += f"""
            <div class="chart">
                <h3>Bid-Ask Spread Distribution</h3>
                <img src="{spread_img}" alt="Spread Distribution">
                <p style="color: #777; font-size: 14px; margin-top: 10px;">
                    Statistical distribution of spreads with histogram and box plot for outlier detection.
                </p>
            </div>
                """

        # Volume profile
        if 'volume_profile' in self.viz_paths:
            volume_path = self.viz_paths['volume_profile']
            if Path(volume_path).exists():
                volume_img = self._embed_image(str(volume_path))
                html += f"""
            <div class="chart">
                <h3>Trade Volume Profile</h3>
                <img src="{volume_img}" alt="Volume Profile">
                <p style="color: #777; font-size: 14px; margin-top: 10px;">
                    Volume distribution by price level and time showing liquidity patterns.
                </p>
            </div>
                """

        # Orderbook heatmap (interactive Plotly)
        if 'orderbook_heatmap' in self.viz_paths:
            heatmap_path = self.viz_paths['orderbook_heatmap']
            if Path(heatmap_path).exists():
                heatmap_html = self._embed_plotly_chart(str(heatmap_path))
                html += f"""
            <div class="chart">
                <h3>Orderbook Depth Evolution (Interactive)</h3>
                {heatmap_html}
                <p style="color: #777; font-size: 14px; margin-top: 10px;">
                    Interactive orderbook depth visualization showing bid/ask imbalance over time.
                    Zoom, pan, and hover for detailed insights.
                </p>
            </div>
                """

        html += """
        </section>
        """

        return html

    def _embed_image(self, img_path: str) -> str:
        """
        Convert PNG image to base64 data URL for embedding.

        Parameters
        ----------
        img_path : str
            Path to PNG file

        Returns
        -------
        str
            data:image/png;base64,... URL
        """
        try:
            with open(img_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            return f'data:image/png;base64,{img_data}'
        except Exception as e:
            return f'data:text/plain;base64,{base64.b64encode(f"Error loading image: {e}".encode()).decode()}'

    def _embed_plotly_chart(self, html_path: str) -> str:
        """
        Embed Plotly HTML chart as iframe.

        Parameters
        ----------
        html_path : str
            Path to Plotly HTML file

        Returns
        -------
        str
            iframe HTML markup with embedded chart
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                plotly_html = f.read()

            # Escape quotes for srcdoc attribute
            plotly_html_escaped = plotly_html.replace('"', '&quot;').replace("'", '&#39;')

            return f'<iframe srcdoc="{plotly_html_escaped}" style="width:100%; height:600px; border:1px solid #ddd; border-radius:5px;"></iframe>'
        except Exception as e:
            return f'<div class="info-box error"><p>Error loading interactive chart: {e}</p></div>'

    def _generate_footer(self) -> str:
        """Generate footer section."""
        return """
        <footer>
            <p><strong>Generated by NautilusTrader Advanced Validation System</strong></p>
            <p>Report Version 1.0.0 | Trading Engines Project</p>
            <p>Created by Benjamin Ang / Claude Code</p>
        </footer>
        """


# Example usage and testing
if __name__ == '__main__':
    """
    Test HTMLReportGenerator with sample validation results.
    """
    from pathlib import Path

    print("=" * 80)
    print("HTML REPORT GENERATOR - TEST SUITE")
    print("=" * 80)

    # Sample validation results (mimicking real validator outputs)
    sample_validation_results = {
        'statistical': {
            'gaps': {
                'num_large_gaps': 15,
                'max_gap_ms': 2543.5,
                'mean_gap_ms': 127.3,
                'median_gap_ms': 98.2,
                'std_gap_ms': 215.7
            },
            'outliers': {
                'z_outliers_count': 87,
                'price_jumps_count': 23,
                'max_price_jump_pct': 0.85,
                'outlier_percentage': 0.15
            },
            'spreads': {
                'negative_spreads_count': 0,
                'wide_spreads_count': 34,
                'mean_spread_bps': 5.23,
                'median_spread_bps': 4.87,
                'std_spread_bps': 2.15,
                'min_spread_bps': 2.10,
                'max_spread_bps': 45.30
            }
        },
        'integrity': {
            'duplicates': {
                'exact_duplicates_count': 0,
                'timestamp_duplicates_count': 0
            },
            'missing_values': {
                'total_invalid_count': 0,
                'null_values_count': 0,
                'zero_price_count': 0,
                'negative_price_count': 0,
                'zero_size_count': 0
            },
            'cross_validation': {
                'trades_outside_spread_count': 234,
                'trades_outside_spread_percentage': 11.3,
                'trades_analyzed': 2071
            }
        },
        'orderbook': {
            'price_levels': {
                'bid_ordering_violations': 0,
                'ask_ordering_violations': 0,
                'snapshots_analyzed': 4127
            },
            'crossed_books': {
                'crossed_books_detected': 0,
                'snapshots_checked': 4127,
                'first_crossed_timestamp': 'N/A'
            },
            'depth': {
                'mean_bid_levels': 49.3,
                'mean_ask_levels': 48.7,
                'min_bid_levels': 45,
                'min_ask_levels': 44,
                'max_bid_levels': 50,
                'max_ask_levels': 50,
                'std_bid_levels': 1.2,
                'std_ask_levels': 1.4
            }
        },
        'quality_score': {
            'score': 87,
            'grade': 'B',
            'issues_found': 3,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 1,
            'low_issues': 2,
            'detailed_report': {
                'score_breakdown': {
                    'starting_score': 100,
                    'deductions': {
                        'medium_cross_validation': {
                            'priority': 'medium',
                            'category': 'cross_validation',
                            'description': 'Trades outside spread: 11.3%',
                            'points_deducted': 5
                        },
                        'low_spread': {
                            'priority': 'low',
                            'category': 'spread',
                            'description': 'Wide spreads detected: 34',
                            'points_deducted': 3
                        },
                        'high_connectivity': {
                            'priority': 'high',
                            'category': 'connectivity',
                            'description': 'Large temporal gaps: 15',
                            'points_deducted': 5
                        }
                    },
                    'final_score': 87
                },
                'issues_by_priority': {
                    'critical': [],
                    'high': [
                        {
                            'category': 'connectivity',
                            'description': 'Large temporal gaps: 15',
                            'impact': 'Missing data during gaps - may affect backtest accuracy',
                            'count': 15
                        }
                    ],
                    'medium': [
                        {
                            'category': 'cross_validation',
                            'description': 'Trades outside spread: 11.3%',
                            'impact': 'Quote-trade timing misalignment - may indicate latency issues',
                            'count': 234
                        }
                    ],
                    'low': [
                        {
                            'category': 'spread',
                            'description': 'Wide spreads detected: 34',
                            'impact': 'Low liquidity periods - may affect strategy execution',
                            'count': 34
                        }
                    ]
                },
                'recommendations': [
                    'EXCELLENT: High-quality data suitable for production use.',
                    'Review: Large temporal gaps: 15 - Check network stability during recording',
                    'Note: 1 medium-priority issue(s) detected - may impact accuracy but not critical',
                    'Info: 1 low-priority issue(s) detected - unlikely to affect backtest results'
                ],
                'pass_criteria': {
                    'passes': True,
                    'score_check': True,
                    'critical_issues_check': True,
                    'negative_spreads_check': True,
                    'crossed_books_check': True,
                    'details': {
                        'score': '87 >= 70 (required)',
                        'critical_issues': '0 == 0 (required)',
                        'negative_spreads': '0 == 0 (required)',
                        'crossed_books': '0 == 0 (required)'
                    }
                }
            }
        }
    }

    # Sample visualization paths (these would normally be generated by DataVisualizer)
    sample_viz_paths = {
        'price_timeseries': Path('./test_visualizations/price_timeseries.png'),
        'spread_distribution': Path('./test_visualizations/spread_distribution.png'),
        'volume_profile': Path('./test_visualizations/volume_profile.png'),
        'orderbook_heatmap': Path('./test_visualizations/orderbook_heatmap.html')
    }

    # Test report generation
    print("\nTest 1: Generate HTML Report")
    print("-" * 80)

    test_output_path = Path('./test_report.html')
    test_recording_dir = Path('data/recordings/20251119-152837')

    generator = HTMLReportGenerator(
        validation_results=sample_validation_results,
        viz_paths=sample_viz_paths,
        recording_dir=test_recording_dir,
        output_path=test_output_path
    )

    try:
        report_path = generator.generate_report()
        print(f"✅ Report generated successfully!")
        print(f"📄 Report path: {report_path}")

        # Check file size
        file_size = Path(report_path).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"📊 File size: {file_size_mb:.2f} MB")

        if file_size_mb < 10:
            print("✅ File size within acceptable limits (<10MB)")
        else:
            print("⚠️  File size exceeds 10MB - consider optimization")

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("HTML REPORT GENERATOR TEST COMPLETE")
    print("=" * 80)
    print("\nTo view the report, open test_report.html in your web browser:")
    print(f"  file://{Path(test_output_path).absolute()}")
