#!/usr/bin/env python3
"""
Compare two Nautilus Trader recordings.

This CLI script compares two recording directories (e.g., hybrid vs native)
and displays side-by-side statistics and differences.

Usage:
    python compare_recordings.py <dir1> <dir2>
    python compare_recordings.py /data/recordings/hybrid /data/recordings/native
    python compare_recordings.py /data/recordings/hybrid /data/recordings/native --verbose

Exit Codes:
    0 = Comparison completed successfully
    1 = Error during comparison
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
compare_recordings = _persist.compare_recordings
RecordingReader = _persist.RecordingReader
validate_recording = _persist.validate_recording


def print_comparison_table(comparison: dict, verbose: bool = False) -> None:
    """Print a formatted comparison table."""
    print("\n" + "=" * 90)
    print("RECORDING COMPARISON REPORT")
    print("=" * 90 + "\n")

    # File paths
    print("Recording Paths:")
    print(f"  Recording 1: {comparison['recording1']}")
    print(f"  Recording 2: {comparison['recording2']}\n")

    # Size comparison
    size_comp = comparison.get("size_comparison", {})
    print("Size Comparison:")
    print("-" * 90)
    print(f"  Recording 1: {size_comp.get('recording1_mb', 0):>10.2f} MB")
    print(f"  Recording 2: {size_comp.get('recording2_mb', 0):>10.2f} MB")

    diff_mb = size_comp.get("difference_mb", 0)
    diff_pct = 0
    if size_comp.get("recording2_mb", 0) != 0:
        diff_pct = (diff_mb / size_comp.get("recording2_mb")) * 100

    if diff_mb > 0:
        print(f"  Difference: {diff_mb:>10.2f} MB ({diff_pct:+.1f}%) [Rec1 larger]")
    elif diff_mb < 0:
        print(f"  Difference: {abs(diff_mb):>10.2f} MB ({diff_pct:+.1f}%) [Rec2 larger]")
    else:
        print(f"  Difference: {diff_mb:>10.2f} MB (identical)")

    # Instrument comparison
    print("\n" + "Instrument Comparison:")
    print("-" * 90)

    inst_comp = comparison.get("instruments_comparison", {})
    rec1_inst = inst_comp.get("recording1", {})
    rec2_inst = inst_comp.get("recording2", {})

    all_data_types = set(rec1_inst.keys()) | set(rec2_inst.keys())

    for data_type in sorted(all_data_types):
        rec1_count = len(rec1_inst.get(data_type, []))
        rec2_count = len(rec2_inst.get(data_type, []))

        print(f"\n  {data_type}:")
        print(f"    Recording 1: {rec1_count} instrument(s)")
        print(f"    Recording 2: {rec2_count} instrument(s)")

        if verbose:
            rec1_names = set(rec1_inst.get(data_type, []))
            rec2_names = set(rec2_inst.get(data_type, []))

            if rec1_names:
                print(f"      Rec1 instruments: {', '.join(sorted(rec1_names))}")
            if rec2_names:
                print(f"      Rec2 instruments: {', '.join(sorted(rec2_names))}")

            # Show differences
            only_in_rec1 = rec1_names - rec2_names
            only_in_rec2 = rec2_names - rec1_names

            if only_in_rec1:
                print(f"      Only in Rec1: {', '.join(sorted(only_in_rec1))}")
            if only_in_rec2:
                print(f"      Only in Rec2: {', '.join(sorted(only_in_rec2))}")

    print("\n" + "=" * 90 + "\n")


def print_detailed_stats(recording_path: Path, label: str, verbose: bool = False) -> dict:
    """Print detailed statistics for a recording."""
    try:
        reader = RecordingReader(recording_path)
        stats = reader.get_statistics()

        print(f"\n{label} - Detailed Statistics:")
        print("-" * 90)

        if stats.get("session"):
            session = stats["session"]
            print(f"  Run ID: {session.get('run_id', 'Unknown')}")
            print(f"  Start Time: {session.get('start_time', 'Unknown')}")
            print(f"  End Time: {session.get('end_time', 'Unknown')}")
            print(f"  Duration: {session.get('duration_seconds', 'Unknown')} seconds")

        # Data type statistics
        for data_type, instruments in stats.get("data_types", {}).items():
            print(f"\n  {data_type}:")
            total_count = 0
            for instrument, inst_stats in instruments.items():
                if "error" in inst_stats:
                    print(f"    {instrument}: ERROR - {inst_stats['error']}")
                else:
                    count = inst_stats.get("count", 0)
                    total_count += count
                    print(f"    {instrument}: {count:,} records")

                    if verbose and "time_range" in inst_stats:
                        start, end = inst_stats["time_range"]
                        print(f"      Time range: {start} to {end}")

            print(f"    Total: {total_count:,} records")

        return stats

    except Exception as e:
        print(f"  ❌ Error loading statistics: {e}")
        return {}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare two Nautilus Trader recording directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two recordings
  python compare_recordings.py /data/hybrid /data/native

  # Compare with verbose output
  python compare_recordings.py /data/hybrid /data/native --verbose

  # Save comparison report to JSON
  python compare_recordings.py /data/hybrid /data/native --report comparison.json
        """
    )

    parser.add_argument(
        "recording1",
        type=str,
        help="Path to first recording directory"
    )

    parser.add_argument(
        "recording2",
        type=str,
        help="Path to second recording directory"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed statistics and instrument lists"
    )

    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Save comparison report to JSON file"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Also validate both recordings"
    )

    args = parser.parse_args()

    # Validate paths exist
    for path_str, label in [(args.recording1, "Recording 1"), (args.recording2, "Recording 2")]:
        path = Path(path_str)
        if not path.exists():
            print(f"❌ Error: {label} directory not found: {path_str}")
            sys.exit(1)
        if not path.is_dir():
            print(f"❌ Error: {label} is not a directory: {path_str}")
            sys.exit(1)

    try:
        # Run comparison
        print("Comparing recordings...")
        comparison = compare_recordings(args.recording1, args.recording2)

        # Validate if requested
        if args.validate:
            print("\nValidating Recording 1...")
            val1 = validate_recording(args.recording1)
            status1 = "✅ Valid" if val1["valid"] else "❌ Invalid"
            print(f"  {status1}")

            print("Validating Recording 2...")
            val2 = validate_recording(args.recording2)
            status2 = "✅ Valid" if val2["valid"] else "❌ Invalid"
            print(f"  {status2}")

            comparison["validation1"] = val1
            comparison["validation2"] = val2

        # Print comparison table
        print_comparison_table(comparison, verbose=args.verbose)

        # Print detailed stats if verbose
        if args.verbose:
            print_detailed_stats(Path(args.recording1), "Recording 1", verbose=True)
            print_detailed_stats(Path(args.recording2), "Recording 2", verbose=True)
            print("\n" + "=" * 90 + "\n")

        # Save report if requested
        if args.report:
            import json
            with open(args.report, "w") as f:
                json.dump(comparison, f, indent=2, default=str)
            print(f"Comparison report saved to: {args.report}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
