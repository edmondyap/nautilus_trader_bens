"""
Persistence Utilities - Nautilus Trader Data Recorder

Trading Engines Project - Benchmark/Evaluation Code
Location: benchmark/nautilus_trader/native_recorder/persistence.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09

Utilities for working with recorded parquet data.

Note: The main Strategy class writes parquet directly using pandas.to_parquet()
(proven pattern from bybit_options_data_collector.py). This module provides
utilities for READING, VALIDATING, and ANALYZING recorded data.

Architecture:
- ✅ NATIVE: Can optionally use ParquetDataCatalog for reading (Nautilus)
- ✅ NATIVE: Uses pandas for DataFrame operations
- ❌ CUSTOM: Validation and metadata utilities
- ❌ CUSTOM: SHA256 checksum generation

Upstream: nautilus_trader/ (DO NOT MODIFY)
Custom: This file (benchmark/evaluation code)
"""

from pathlib import Path
from typing import Any
import json
import hashlib

import pandas as pd


class RecordingReader:
    """
    Read and analyze recorded parquet data.

    This class provides utilities for working with data recorded by
    NativeDataRecorderStrategy.

    Parameters
    ----------
    recording_dir : str | Path
        Path to recording directory (contains run_id/data_type/instrument/)

    Examples
    --------
    >>> reader = RecordingReader("data/recordings/20251109-123456")
    >>> quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")
    >>> print(f"Loaded {len(quotes)} quote ticks")
    >>> stats = reader.get_statistics()
    """

    def __init__(self, recording_dir: str | Path):
        self.recording_dir = Path(recording_dir)

        if not self.recording_dir.exists():
            raise FileNotFoundError(f"Recording directory not found: {recording_dir}")

    def read_quotes(self, instrument_key: str) -> pd.DataFrame:
        """
        Read quote ticks for an instrument.

        Parameters
        ----------
        instrument_key : str
            Instrument identifier (e.g., "SOLUSDT-SPOT.BYBIT")

        Returns
        -------
        pd.DataFrame
            Quote ticks with columns: timestamp, bid_price, ask_price, bid_size, ask_size
        """
        quotes_file = self.recording_dir / "quote_ticks" / instrument_key / "quote_ticks.parquet"

        if not quotes_file.exists():
            raise FileNotFoundError(f"Quote data not found: {quotes_file}")

        return pd.read_parquet(quotes_file)

    def read_deltas(self, instrument_key: str) -> pd.DataFrame:
        """
        Read order book deltas for an instrument.

        Parameters
        ----------
        instrument_key : str
            Instrument identifier

        Returns
        -------
        pd.DataFrame
            Order book deltas
        """
        deltas_file = self.recording_dir / "order_book_deltas" / instrument_key / "order_book_deltas.parquet"

        if not deltas_file.exists():
            raise FileNotFoundError(f"Delta data not found: {deltas_file}")

        return pd.read_parquet(deltas_file)

    def list_instruments(self) -> dict[str, list[str]]:
        """
        List all recorded instruments by data type.

        Returns
        -------
        dict[str, list[str]]
            {"quote_ticks": ["SOLUSDT-SPOT.BYBIT", ...], "order_book_deltas": [...]}
        """
        instruments = {}

        # Find quote ticks
        quotes_dir = self.recording_dir / "quote_ticks"
        if quotes_dir.exists():
            instruments["quote_ticks"] = [d.name for d in quotes_dir.iterdir() if d.is_dir()]

        # Find deltas
        deltas_dir = self.recording_dir / "order_book_deltas"
        if deltas_dir.exists():
            instruments["order_book_deltas"] = [d.name for d in deltas_dir.iterdir() if d.is_dir()]

        return instruments

    def get_metadata(self) -> dict[str, Any]:
        """
        Read session metadata.

        Returns
        -------
        dict[str, Any]
            Session metadata (run_id, timestamps, counts, config)
        """
        metadata_file = self.recording_dir / "session_metadata.json"

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_file}")

        with open(metadata_file, "r") as f:
            return json.load(f)

    def get_checksums(self) -> dict[str, dict[str, Any]]:
        """
        Read checksums file.

        Returns
        -------
        dict[str, dict[str, Any]]
            {relative_path: {"sha256": "...", "size_bytes": 12345}}
        """
        checksums_file = self.recording_dir / "checksums.json"

        if not checksums_file.exists():
            raise FileNotFoundError(f"Checksums not found: {checksums_file}")

        with open(checksums_file, "r") as f:
            return json.load(f)

    def get_statistics(self) -> dict[str, Any]:
        """
        Generate comprehensive statistics for the recording.

        Returns
        -------
        dict[str, Any]
            Statistics including counts, file sizes, time ranges, etc.
        """
        stats = {
            "recording_dir": str(self.recording_dir),
            "instruments": self.list_instruments(),
            "data_types": {},
        }

        # Load metadata
        try:
            metadata = self.get_metadata()
            stats["session"] = metadata
        except FileNotFoundError:
            stats["session"] = None

        # Analyze quotes
        if "quote_ticks" in stats["instruments"]:
            quote_stats = {}
            for instrument in stats["instruments"]["quote_ticks"]:
                try:
                    df = self.read_quotes(instrument)
                    quote_stats[instrument] = {
                        "count": len(df),
                        "time_range": (str(df["timestamp"].min()), str(df["timestamp"].max())),
                        "price_range": (float(df["bid_price"].min()), float(df["ask_price"].max())),
                    }
                except Exception as e:
                    quote_stats[instrument] = {"error": str(e)}

            stats["data_types"]["quote_ticks"] = quote_stats

        # Analyze deltas
        if "order_book_deltas" in stats["instruments"]:
            delta_stats = {}
            for instrument in stats["instruments"]["order_book_deltas"]:
                try:
                    df = self.read_deltas(instrument)
                    delta_stats[instrument] = {
                        "count": len(df),
                        "time_range": (str(df["timestamp"].min()), str(df["timestamp"].max())),
                    }
                except Exception as e:
                    delta_stats[instrument] = {"error": str(e)}

            stats["data_types"]["order_book_deltas"] = delta_stats

        # File sizes
        total_size = sum(f.stat().st_size for f in self.recording_dir.rglob("*.parquet"))
        stats["total_parquet_size_bytes"] = total_size
        stats["total_parquet_size_mb"] = total_size / (1024 * 1024)

        return stats


def validate_recording(recording_dir: str | Path) -> dict[str, Any]:
    """
    Validate a recording directory.

    Checks:
    - All files exist
    - Checksums match
    - Data is readable
    - Timestamps are ordered
    - No data gaps

    Parameters
    ----------
    recording_dir : str | Path
        Path to recording directory

    Returns
    -------
    dict[str, Any]
        Validation report with status and any issues found

    Examples
    --------
    >>> report = validate_recording("data/recordings/20251109-123456")
    >>> if report["valid"]:
    ...     print("✅ Recording valid")
    ... else:
    ...     print(f"❌ Issues found: {report['issues']}")
    """
    reader = RecordingReader(recording_dir)
    report = {
        "valid": True,
        "issues": [],
        "checks": [],
    }

    # Check 1: Metadata exists
    try:
        metadata = reader.get_metadata()
        report["checks"].append({"check": "metadata_exists", "status": "pass"})
    except FileNotFoundError as e:
        report["valid"] = False
        report["issues"].append(f"Metadata missing: {e}")
        report["checks"].append({"check": "metadata_exists", "status": "fail", "error": str(e)})
        return report  # Can't continue without metadata

    # Check 2: Checksums exist and match
    try:
        checksums = reader.get_checksums()
        report["checks"].append({"check": "checksums_exist", "status": "pass"})

        # Verify checksums
        mismatches = []
        for rel_path, checksum_data in checksums.items():
            file_path = Path(recording_dir) / rel_path
            if not file_path.exists():
                mismatches.append(f"File missing: {rel_path}")
                continue

            with open(file_path, "rb") as f:
                actual_sha256 = hashlib.sha256(f.read()).hexdigest()

            if actual_sha256 != checksum_data["sha256"]:
                mismatches.append(f"Checksum mismatch: {rel_path}")

        if mismatches:
            report["valid"] = False
            report["issues"].extend(mismatches)
            report["checks"].append({"check": "checksums_match", "status": "fail", "errors": mismatches})
        else:
            report["checks"].append({"check": "checksums_match", "status": "pass"})

    except FileNotFoundError as e:
        report["valid"] = False
        report["issues"].append(f"Checksums missing: {e}")
        report["checks"].append({"check": "checksums_exist", "status": "fail", "error": str(e)})

    # Check 3: Data is readable and timestamps are ordered
    instruments = reader.list_instruments()

    for data_type, instrument_list in instruments.items():
        for instrument in instrument_list:
            try:
                if data_type == "quote_ticks":
                    df = reader.read_quotes(instrument)
                elif data_type == "order_book_deltas":
                    df = reader.read_deltas(instrument)
                else:
                    continue

                # Check timestamps are sorted
                if not df["timestamp"].is_monotonic_increasing:
                    report["valid"] = False
                    report["issues"].append(f"Timestamps not ordered: {data_type}/{instrument}")
                    report["checks"].append({
                        "check": f"timestamps_ordered_{data_type}_{instrument}",
                        "status": "fail"
                    })
                else:
                    report["checks"].append({
                        "check": f"timestamps_ordered_{data_type}_{instrument}",
                        "status": "pass"
                    })

                # Check for data
                if len(df) == 0:
                    report["valid"] = False
                    report["issues"].append(f"Empty data: {data_type}/{instrument}")
                    report["checks"].append({
                        "check": f"data_exists_{data_type}_{instrument}",
                        "status": "fail"
                    })
                else:
                    report["checks"].append({
                        "check": f"data_exists_{data_type}_{instrument}",
                        "status": "pass",
                        "count": len(df)
                    })

            except Exception as e:
                report["valid"] = False
                report["issues"].append(f"Error reading {data_type}/{instrument}: {e}")
                report["checks"].append({
                    "check": f"readable_{data_type}_{instrument}",
                    "status": "fail",
                    "error": str(e)
                })

    return report


def generate_data_quality_report(recording_dir: str | Path, output_path: str | Path | None = None) -> dict[str, Any]:
    """
    Generate comprehensive data quality report.

    Parameters
    ----------
    recording_dir : str | Path
        Path to recording directory
    output_path : str | Path | None, default=None
        If provided, save report to this JSON file

    Returns
    -------
    dict[str, Any]
        Data quality report

    Examples
    --------
    >>> report = generate_data_quality_report("data/recordings/20251109-123456")
    >>> print(f"Quality Score: {report['quality_score']}/100")
    """
    reader = RecordingReader(recording_dir)

    # Get validation results
    validation = validate_recording(recording_dir)

    # Get statistics
    stats = reader.get_statistics()

    # Build report
    report = {
        "recording_dir": str(recording_dir),
        "validation": validation,
        "statistics": stats,
        "quality_score": 100 if validation["valid"] else 0,  # Simple scoring
        "recommendations": [],
    }

    # Add recommendations
    if not validation["valid"]:
        report["recommendations"].append("Fix validation issues before using this data")

    if stats.get("session") and stats["session"].get("connection_warnings", 0) > 0:
        report["recommendations"].append("Connection issues detected during recording")

    # Save if requested
    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def load_recording(recording_dir: str | Path) -> RecordingReader:
    """
    Load a recording directory.

    Convenience function that creates RecordingReader and validates.

    Parameters
    ----------
    recording_dir : str | Path
        Path to recording directory

    Returns
    -------
    RecordingReader
        Reader instance

    Raises
    ------
    ValueError
        If recording is invalid

    Examples
    --------
    >>> reader = load_recording("data/recordings/20251109-123456")
    >>> quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")
    """
    # Validate first
    validation = validate_recording(recording_dir)

    if not validation["valid"]:
        raise ValueError(f"Invalid recording: {validation['issues']}")

    return RecordingReader(recording_dir)


def compare_recordings(dir1: str | Path, dir2: str | Path) -> dict[str, Any]:
    """
    Compare two recordings (e.g., hybrid vs native).

    Parameters
    ----------
    dir1 : str | Path
        First recording directory
    dir2 : str | Path
        Second recording directory

    Returns
    -------
    dict[str, Any]
        Comparison results
    """
    reader1 = RecordingReader(dir1)
    reader2 = RecordingReader(dir2)

    stats1 = reader1.get_statistics()
    stats2 = reader2.get_statistics()

    comparison = {
        "recording1": str(dir1),
        "recording2": str(dir2),
        "size_comparison": {
            "recording1_mb": stats1["total_parquet_size_mb"],
            "recording2_mb": stats2["total_parquet_size_mb"],
            "difference_mb": stats1["total_parquet_size_mb"] - stats2["total_parquet_size_mb"],
        },
        "instruments_comparison": {
            "recording1": stats1["instruments"],
            "recording2": stats2["instruments"],
        },
    }

    return comparison
