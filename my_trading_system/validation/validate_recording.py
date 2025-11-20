#!/usr/bin/env python3
"""
Validate a Nautilus Trader recording directory.

This CLI script validates a recording directory to ensure all data is intact,
checksums match, and data is readable and properly ordered.

Usage:
    python validate_recording.py <path>
    python validate_recording.py /data/recordings/20251109-123456
    python validate_recording.py /data/recordings/20251109-123456 --verbose

Exit Codes:
    0 = Valid recording
    1 = Invalid recording with issues
"""

import argparse
import sys
from pathlib import Path

# Import persistence functions directly to avoid circular imports
import importlib.util

def _load_persistence_module():
    """Load persistence module directly."""
    persistence_path = Path(__file__).parent.parent / "native_recorder" / "persistence.py"
    spec = importlib.util.spec_from_file_location("persistence", persistence_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_persist = _load_persistence_module()
validate_recording = _persist.validate_recording
RecordingReader = _persist.RecordingReader


def format_status(status: str) -> str:
    """Format status with emoji and color."""
    if status == "pass":
        return "✅ PASS"
    elif status == "fail":
        return "❌ FAIL"
    else:
        return f"⚠️ {status.upper()}"


def print_colorized_report(report: dict, verbose: bool = False) -> None:
    """Print a colorized validation report."""
    print("\n" + "=" * 70)
    print("RECORDING VALIDATION REPORT")
    print("=" * 70 + "\n")

    # Overall status
    if report["valid"]:
        print("✅ OVERALL STATUS: VALID\n")
    else:
        print("❌ OVERALL STATUS: INVALID\n")

    # Issues summary
    if report["issues"]:
        print(f"Issues Found: {len(report['issues'])}")
        for issue in report["issues"]:
            print(f"  ❌ {issue}")
        print()

    # Detailed checks
    if verbose:
        print("Detailed Checks:")
        print("-" * 70)
        for check in report["checks"]:
            check_name = check["check"]
            status = format_status(check["status"])
            print(f"  {status} - {check_name}")

            if "count" in check:
                print(f"           Data points: {check['count']}")

            if "error" in check:
                print(f"           Error: {check['error']}")

            if "errors" in check:
                for error in check["errors"]:
                    print(f"           - {error}")

        print()

    # Statistics
    try:
        reader = RecordingReader(report.get("recording_dir", "."))
        stats = reader.get_statistics()

        print("Recording Statistics:")
        print("-" * 70)
        print(f"  📂 Directory: {report.get('recording_dir', 'Unknown')}")
        print(f"  💾 Total Size: {stats.get('total_parquet_size_mb', 0):.2f} MB")

        if stats.get("instruments"):
            print(f"  📊 Data Types: {', '.join(stats['instruments'].keys())}")
            for data_type, instruments in stats["instruments"].items():
                print(f"     - {data_type}: {len(instruments)} instrument(s)")

        print()

    except Exception as e:
        if verbose:
            print(f"Could not load statistics: {e}\n")

    # Summary
    print("=" * 70)
    if report["valid"]:
        print("✅ Validation passed! Recording is ready to use.")
        return_code = 0
    else:
        print("❌ Validation failed! Review issues above.")
        return_code = 1

    print("=" * 70 + "\n")
    return return_code


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate a Nautilus Trader recording directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a recording
  python validate_recording.py /data/recordings/20251109-123456

  # Validate with verbose output
  python validate_recording.py /data/recordings/20251109-123456 --verbose

  # Validate and save report to JSON
  python validate_recording.py /data/recordings/20251109-123456 --report validation.json
        """
    )

    parser.add_argument(
        "recording_dir",
        type=str,
        help="Path to recording directory"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed check results"
    )

    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Save detailed report to JSON file"
    )

    args = parser.parse_args()

    # Validate path exists
    recording_path = Path(args.recording_dir)
    if not recording_path.exists():
        print(f"❌ Error: Directory not found: {args.recording_dir}")
        sys.exit(1)

    if not recording_path.is_dir():
        print(f"❌ Error: Not a directory: {args.recording_dir}")
        sys.exit(1)

    # Run validation
    try:
        print(f"Validating recording: {recording_path}")
        report = validate_recording(recording_path)
        report["recording_dir"] = str(recording_path)

        # Save report if requested
        if args.report:
            import json
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to: {args.report}")

        # Print report
        return_code = print_colorized_report(report, verbose=args.verbose)
        sys.exit(return_code)

    except Exception as e:
        print(f"❌ Error during validation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
