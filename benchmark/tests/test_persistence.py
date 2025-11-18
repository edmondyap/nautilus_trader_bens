"""
Unit Tests for Recording Persistence and Reading

Tests RecordingReader, validation, and comparison utilities.

Location: benchmark/nautilus_trader/tests/test_persistence.py
Author: Benjamin Ang / Claude Code
Created: 2025-11-09
"""

import json
import hashlib
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd

from benchmark.nautilus_trader.native_recorder.persistence import (
    RecordingReader,
    validate_recording,
    generate_data_quality_report,
    load_recording,
    compare_recordings,
)


class TestRecordingReaderFixtures:
    """Shared fixtures for RecordingReader tests."""

    @pytest.fixture
    def sample_recording_dir(self):
        """Create a sample recording directory with test data."""
        with TemporaryDirectory() as tmpdir:
            recording_dir = Path(tmpdir) / "20251109-120000"
            recording_dir.mkdir(parents=True, exist_ok=True)

            # Create quotes data
            quotes_dir = recording_dir / "quote_ticks" / "SOLUSDT-SPOT.BYBIT"
            quotes_dir.mkdir(parents=True, exist_ok=True)

            quotes_data = {
                "timestamp": pd.date_range("2025-11-09 12:00:00", periods=100, freq="100ms", tz="UTC"),
                "bid_price": [100.0 + i * 0.01 for i in range(100)],
                "ask_price": [101.0 + i * 0.01 for i in range(100)],
                "bid_size": [1000.0] * 100,
                "ask_size": [1000.0] * 100,
            }
            quotes_df = pd.DataFrame(quotes_data)
            quotes_df.to_parquet(quotes_dir / "quote_ticks.parquet", index=False)

            # Create deltas data
            deltas_dir = recording_dir / "order_book_deltas" / "SOLUSDT-SPOT.BYBIT"
            deltas_dir.mkdir(parents=True, exist_ok=True)

            deltas_data = {
                "timestamp": pd.date_range("2025-11-09 12:00:00", periods=50, freq="200ms", tz="UTC"),
                "action": ["ADD"] * 25 + ["DELETE"] * 25,
                "side": ["BUY"] * 50,
                "price": [100.0 + i * 0.02 for i in range(50)],
                "size": [100.0] * 50,
                "order_id": [f"order_{i}" for i in range(50)],
            }
            deltas_df = pd.DataFrame(deltas_data)
            deltas_df.to_parquet(deltas_dir / "order_book_deltas.parquet", index=False)

            # Create metadata
            metadata = {
                "run_id": "20251109-120000",
                "session_start": 1699526400.0,
                "session_end": 1699526460.0,
                "duration_seconds": 60.0,
                "instruments": ["SOLUSDT-SPOT.BYBIT"],
                "quote_count": 100,
                "delta_count": 50,
                "config": {
                    "flush_interval_seconds": 60,
                    "record_quotes": True,
                    "record_orderbook": True,
                    "orderbook_depth": 50,
                }
            }
            with open(recording_dir / "session_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            # Create checksums
            checksums = {}
            for parquet_file in recording_dir.rglob("*.parquet"):
                with open(parquet_file, "rb") as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
                rel_path = str(parquet_file.relative_to(recording_dir))
                checksums[rel_path] = {
                    "sha256": sha256,
                    "size_bytes": parquet_file.stat().st_size,
                }
            with open(recording_dir / "checksums.json", "w") as f:
                json.dump(checksums, f, indent=2)

            yield recording_dir


class TestRecordingReader(TestRecordingReaderFixtures):
    """Tests for RecordingReader class."""

    def test_init_with_valid_directory(self, sample_recording_dir):
        """Test initialization with valid directory."""
        reader = RecordingReader(sample_recording_dir)
        assert reader.recording_dir == sample_recording_dir

    def test_init_with_nonexistent_directory(self):
        """Test initialization fails with nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            RecordingReader("/nonexistent/path")

    def test_read_quotes(self, sample_recording_dir):
        """Test reading quote ticks."""
        reader = RecordingReader(sample_recording_dir)
        quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")

        assert isinstance(quotes, pd.DataFrame)
        assert len(quotes) == 100
        assert list(quotes.columns) == ["timestamp", "bid_price", "ask_price", "bid_size", "ask_size"]
        assert quotes["bid_price"].min() >= 100.0
        assert quotes["ask_price"].min() > quotes["bid_price"].min()

    def test_read_quotes_nonexistent_instrument(self, sample_recording_dir):
        """Test reading quotes for nonexistent instrument."""
        reader = RecordingReader(sample_recording_dir)

        with pytest.raises(FileNotFoundError):
            reader.read_quotes("NONEXISTENT-SPOT.BYBIT")

    def test_read_deltas(self, sample_recording_dir):
        """Test reading order book deltas."""
        reader = RecordingReader(sample_recording_dir)
        deltas = reader.read_deltas("SOLUSDT-SPOT.BYBIT")

        assert isinstance(deltas, pd.DataFrame)
        assert len(deltas) == 50
        assert list(deltas.columns) == ["timestamp", "action", "side", "price", "size", "order_id"]
        assert "ADD" in deltas["action"].values
        assert "DELETE" in deltas["action"].values

    def test_read_deltas_nonexistent_instrument(self, sample_recording_dir):
        """Test reading deltas for nonexistent instrument."""
        reader = RecordingReader(sample_recording_dir)

        with pytest.raises(FileNotFoundError):
            reader.read_deltas("NONEXISTENT-SPOT.BYBIT")

    def test_list_instruments(self, sample_recording_dir):
        """Test listing all recorded instruments."""
        reader = RecordingReader(sample_recording_dir)
        instruments = reader.list_instruments()

        assert isinstance(instruments, dict)
        assert "quote_ticks" in instruments
        assert "order_book_deltas" in instruments
        assert "SOLUSDT-SPOT.BYBIT" in instruments["quote_ticks"]
        assert "SOLUSDT-SPOT.BYBIT" in instruments["order_book_deltas"]

    def test_list_instruments_empty_dir(self):
        """Test listing instruments from empty directory."""
        with TemporaryDirectory() as tmpdir:
            reader = RecordingReader(tmpdir)
            instruments = reader.list_instruments()

            assert instruments == {}

    def test_get_metadata(self, sample_recording_dir):
        """Test reading session metadata."""
        reader = RecordingReader(sample_recording_dir)
        metadata = reader.get_metadata()

        assert metadata["run_id"] == "20251109-120000"
        assert metadata["quote_count"] == 100
        assert metadata["delta_count"] == 50
        assert "config" in metadata
        assert metadata["config"]["record_quotes"] is True

    def test_get_metadata_not_found(self):
        """Test metadata read fails when file missing."""
        with TemporaryDirectory() as tmpdir:
            reader = RecordingReader(tmpdir)

            with pytest.raises(FileNotFoundError):
                reader.get_metadata()

    def test_get_checksums(self, sample_recording_dir):
        """Test reading checksums."""
        reader = RecordingReader(sample_recording_dir)
        checksums = reader.get_checksums()

        assert isinstance(checksums, dict)
        assert len(checksums) == 2  # quotes and deltas parquet files

        for rel_path, checksum_data in checksums.items():
            assert "sha256" in checksum_data
            assert "size_bytes" in checksum_data
            assert isinstance(checksum_data["sha256"], str)
            assert len(checksum_data["sha256"]) == 64  # SHA256 hex length

    def test_get_checksums_not_found(self):
        """Test checksums read fails when file missing."""
        with TemporaryDirectory() as tmpdir:
            reader = RecordingReader(tmpdir)

            with pytest.raises(FileNotFoundError):
                reader.get_checksums()

    def test_get_statistics(self, sample_recording_dir):
        """Test generating statistics."""
        reader = RecordingReader(sample_recording_dir)
        stats = reader.get_statistics()

        assert "recording_dir" in stats
        assert "instruments" in stats
        assert "data_types" in stats
        assert "total_parquet_size_bytes" in stats
        assert "total_parquet_size_mb" in stats
        assert "session" in stats

        # Check data type stats
        assert "quote_ticks" in stats["data_types"]
        quote_stats = stats["data_types"]["quote_ticks"]["SOLUSDT-SPOT.BYBIT"]
        assert quote_stats["count"] == 100

        delta_stats = stats["data_types"]["order_book_deltas"]["SOLUSDT-SPOT.BYBIT"]
        assert delta_stats["count"] == 50

    def test_get_statistics_empty_dir(self):
        """Test statistics with empty directory."""
        with TemporaryDirectory() as tmpdir:
            reader = RecordingReader(tmpdir)
            stats = reader.get_statistics()

            assert "instruments" in stats
            assert stats["total_parquet_size_bytes"] == 0


class TestValidateRecording(TestRecordingReaderFixtures):
    """Tests for validate_recording function."""

    def test_validate_valid_recording(self, sample_recording_dir):
        """Test validation passes for valid recording."""
        report = validate_recording(sample_recording_dir)

        assert report["valid"] is True
        assert len(report["issues"]) == 0

    def test_validate_missing_metadata(self):
        """Test validation fails with missing metadata."""
        with TemporaryDirectory() as tmpdir:
            report = validate_recording(tmpdir)

            assert report["valid"] is False
            assert any("Metadata missing" in issue for issue in report["issues"])

    def test_validate_missing_checksums(self):
        """Test validation fails with missing checksums."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create metadata but not checksums
            metadata = {"run_id": "test"}
            with open(tmpdir_path / "session_metadata.json", "w") as f:
                json.dump(metadata, f)

            report = validate_recording(tmpdir)

            assert report["valid"] is False
            assert any("Checksums missing" in issue for issue in report["issues"])

    def test_validate_corrupted_parquet(self):
        """Test validation detects corrupted parquet files."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create metadata and checksums with wrong checksum
            metadata = {"run_id": "test"}
            with open(tmpdir_path / "session_metadata.json", "w") as f:
                json.dump(metadata, f)

            checksums = {
                "quote_ticks/SOLUSDT-SPOT.BYBIT/quote_ticks.parquet": {
                    "sha256": "0" * 64,  # Wrong checksum
                    "size_bytes": 1000
                }
            }
            with open(tmpdir_path / "checksums.json", "w") as f:
                json.dump(checksums, f)

            report = validate_recording(tmpdir)

            # Should find missing file (which triggers different error)
            assert report["valid"] is False

    def test_validate_unordered_timestamps(self):
        """Test validation detects unordered timestamps."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quotes_dir = tmpdir_path / "quote_ticks" / "SOLUSDT-SPOT.BYBIT"
            quotes_dir.mkdir(parents=True, exist_ok=True)

            # Create data with unordered timestamps
            quotes_data = {
                "timestamp": [
                    pd.Timestamp("2025-11-09 12:00:02", tz="UTC"),
                    pd.Timestamp("2025-11-09 12:00:01", tz="UTC"),  # Out of order
                    pd.Timestamp("2025-11-09 12:00:03", tz="UTC"),
                ],
                "bid_price": [100.0, 100.5, 101.0],
                "ask_price": [101.0, 101.5, 102.0],
                "bid_size": [1000.0, 1000.0, 1000.0],
                "ask_size": [1000.0, 1000.0, 1000.0],
            }
            quotes_df = pd.DataFrame(quotes_data)
            quotes_df.to_parquet(quotes_dir / "quote_ticks.parquet", index=False)

            # Create metadata and checksums
            metadata = {"run_id": "test"}
            with open(tmpdir_path / "session_metadata.json", "w") as f:
                json.dump(metadata, f)

            checksums = {}
            for parquet_file in tmpdir_path.rglob("*.parquet"):
                with open(parquet_file, "rb") as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
                rel_path = str(parquet_file.relative_to(tmpdir_path))
                checksums[rel_path] = {"sha256": sha256, "size_bytes": 1000}

            with open(tmpdir_path / "checksums.json", "w") as f:
                json.dump(checksums, f)

            report = validate_recording(tmpdir_path)

            assert report["valid"] is False
            assert any("Timestamps not ordered" in issue for issue in report["issues"])

    def test_validate_empty_data(self):
        """Test validation detects empty data files."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quotes_dir = tmpdir_path / "quote_ticks" / "SOLUSDT-SPOT.BYBIT"
            quotes_dir.mkdir(parents=True, exist_ok=True)

            # Create empty DataFrame
            empty_df = pd.DataFrame({
                "timestamp": [],
                "bid_price": [],
                "ask_price": [],
                "bid_size": [],
                "ask_size": [],
            })
            empty_df.to_parquet(quotes_dir / "quote_ticks.parquet", index=False)

            # Create metadata and checksums
            metadata = {"run_id": "test"}
            with open(tmpdir_path / "session_metadata.json", "w") as f:
                json.dump(metadata, f)

            checksums = {}
            for parquet_file in tmpdir_path.rglob("*.parquet"):
                with open(parquet_file, "rb") as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
                rel_path = str(parquet_file.relative_to(tmpdir_path))
                checksums[rel_path] = {"sha256": sha256, "size_bytes": 100}

            with open(tmpdir_path / "checksums.json", "w") as f:
                json.dump(checksums, f)

            report = validate_recording(tmpdir_path)

            assert report["valid"] is False
            assert any("Empty data" in issue for issue in report["issues"])


class TestGenerateDataQualityReport(TestRecordingReaderFixtures):
    """Tests for generate_data_quality_report function."""

    def test_quality_report_valid_recording(self, sample_recording_dir):
        """Test quality report for valid recording."""
        report = generate_data_quality_report(sample_recording_dir)

        assert "validation" in report
        assert "statistics" in report
        assert "quality_score" in report
        assert "recommendations" in report
        assert report["validation"]["valid"] is True
        assert report["quality_score"] == 100

    def test_quality_report_saves_to_file(self, sample_recording_dir):
        """Test quality report can be saved to file."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "quality_report.json"

            report = generate_data_quality_report(sample_recording_dir, output_path)

            assert output_path.exists()
            with open(output_path) as f:
                saved_report = json.load(f)

            assert saved_report["validation"]["valid"] is True

    def test_quality_report_invalid_recording(self):
        """Test quality report for invalid recording."""
        with TemporaryDirectory() as tmpdir:
            report = generate_data_quality_report(tmpdir)

            assert report["validation"]["valid"] is False
            assert report["quality_score"] == 0


class TestLoadRecording(TestRecordingReaderFixtures):
    """Tests for load_recording convenience function."""

    def test_load_valid_recording(self, sample_recording_dir):
        """Test loading valid recording."""
        reader = load_recording(sample_recording_dir)

        assert isinstance(reader, RecordingReader)
        assert reader.recording_dir == sample_recording_dir

    def test_load_invalid_recording_raises_error(self):
        """Test loading invalid recording raises error."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Invalid recording"):
                load_recording(tmpdir)

    def test_loaded_reader_works(self, sample_recording_dir):
        """Test loaded reader can read data."""
        reader = load_recording(sample_recording_dir)
        quotes = reader.read_quotes("SOLUSDT-SPOT.BYBIT")

        assert len(quotes) == 100


class TestCompareRecordings(TestRecordingReaderFixtures):
    """Tests for compare_recordings function."""

    def test_compare_identical_recordings(self, sample_recording_dir):
        """Test comparing identical recordings."""
        comparison = compare_recordings(sample_recording_dir, sample_recording_dir)

        assert "recording1" in comparison
        assert "recording2" in comparison
        assert "size_comparison" in comparison
        assert "instruments_comparison" in comparison

        size_diff = comparison["size_comparison"]["difference_mb"]
        assert abs(size_diff) < 0.01  # Should be ~0

    def test_compare_different_size_recordings(self):
        """Test comparing recordings of different sizes."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create first recording with 100 quotes
            rec1_dir = tmpdir_path / "rec1" / "quote_ticks" / "SOL"
            rec1_dir.mkdir(parents=True, exist_ok=True)
            quotes1 = {
                "timestamp": pd.date_range("2025-11-09", periods=100, freq="1s", tz="UTC"),
                "bid_price": [100.0] * 100,
                "ask_price": [101.0] * 100,
                "bid_size": [1000.0] * 100,
                "ask_size": [1000.0] * 100,
            }
            pd.DataFrame(quotes1).to_parquet(rec1_dir / "quote_ticks.parquet", index=False)

            # Create second recording with 50 quotes
            rec2_dir = tmpdir_path / "rec2" / "quote_ticks" / "SOL"
            rec2_dir.mkdir(parents=True, exist_ok=True)
            quotes2 = {
                "timestamp": pd.date_range("2025-11-09", periods=50, freq="1s", tz="UTC"),
                "bid_price": [100.0] * 50,
                "ask_price": [101.0] * 50,
                "bid_size": [1000.0] * 50,
                "ask_size": [1000.0] * 50,
            }
            pd.DataFrame(quotes2).to_parquet(rec2_dir / "quote_ticks.parquet", index=False)

            comparison = compare_recordings(rec1_dir.parent, rec2_dir.parent)

            # First should be larger
            assert comparison["size_comparison"]["recording1_mb"] > comparison["size_comparison"]["recording2_mb"]

    def test_compare_recordings_by_path_object(self, sample_recording_dir):
        """Test comparing recordings using Path objects."""
        comparison = compare_recordings(
            Path(str(sample_recording_dir)),
            Path(str(sample_recording_dir))
        )

        assert "recording1" in comparison
        assert "recording2" in comparison


class TestPersistenceIntegration:
    """Integration tests for persistence utilities."""

    def test_full_workflow(self):
        """Test complete workflow: create, validate, read, compare."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create two recordings
            for rec_num in [1, 2]:
                rec_dir = tmpdir_path / f"recording_{rec_num}" / "quote_ticks" / "SOLUSDT"
                rec_dir.mkdir(parents=True, exist_ok=True)

                quotes = {
                    "timestamp": pd.date_range("2025-11-09", periods=100, freq="1s", tz="UTC"),
                    "bid_price": [100.0 + rec_num] * 100,
                    "ask_price": [101.0 + rec_num] * 100,
                    "bid_size": [1000.0] * 100,
                    "ask_size": [1000.0] * 100,
                }
                pd.DataFrame(quotes).to_parquet(rec_dir / "quote_ticks.parquet", index=False)

                # Create metadata and checksums
                parent_dir = rec_dir.parent.parent.parent
                metadata = {
                    "run_id": f"recording_{rec_num}",
                    "quote_count": 100,
                    "config": {"record_quotes": True}
                }
                with open(parent_dir / "session_metadata.json", "w") as f:
                    json.dump(metadata, f)

                checksums = {}
                for pf in parent_dir.rglob("*.parquet"):
                    with open(pf, "rb") as f:
                        checksums[str(pf.relative_to(parent_dir))] = {
                            "sha256": hashlib.sha256(f.read()).hexdigest(),
                            "size_bytes": pf.stat().st_size
                        }
                with open(parent_dir / "checksums.json", "w") as f:
                    json.dump(checksums, f)

            # Validate
            for rec_num in [1, 2]:
                rec_parent = tmpdir_path / f"recording_{rec_num}"
                report = validate_recording(rec_parent)
                assert report["valid"] is True

            # Read
            rec1_parent = tmpdir_path / "recording_1"
            reader1 = RecordingReader(rec1_parent)
            quotes1 = reader1.read_quotes("SOLUSDT")
            assert len(quotes1) == 100

            # Compare
            rec1 = tmpdir_path / "recording_1"
            rec2 = tmpdir_path / "recording_2"
            comparison = compare_recordings(rec1, rec2)
            assert "size_comparison" in comparison
