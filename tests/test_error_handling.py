#!/usr/bin/env python

"""
Tests for error handling and edge cases
"""

from __future__ import annotations

import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from outkast import secc_caste
from outkast.secc_caste_ln import SeccCasteLnData, get_secc_data_path


class TestErrorHandling(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame({"name": ["patel", "kohli"]})

    def test_missing_data_file(self) -> None:
        """Test behavior when SECC data file is missing."""
        with patch("outkast.secc_caste_ln.get_secc_data_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/file.csv")

            with pytest.raises(FileNotFoundError):
                secc_caste(self.df, "name")

    def test_corrupted_data_file(self) -> None:
        """Test behavior with corrupted SECC data file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("not,valid,csv,data\nwith\ninvalid\nstructure")
            temp_path = Path(f.name)

        try:
            with patch("outkast.secc_caste_ln.get_secc_data_path") as mock_path:
                mock_path.return_value = temp_path

                # Should raise an exception due to missing required columns
                with pytest.raises((KeyError, ValueError)):
                    secc_caste(self.df, "name")
        finally:
            temp_path.unlink(missing_ok=True)

    def test_invalid_state_parameter(self) -> None:
        """Test with invalid state parameter."""
        # Invalid state should return empty results but not crash
        result = secc_caste(self.df, "name", "nonexistent_state")

        # Should complete without error
        assert len(result) == len(self.df)

        # All caste columns should be NaN since no data matches
        caste_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in caste_cols:
            assert col in result.columns

    def test_invalid_year_parameter(self) -> None:
        """Test with invalid year parameter."""
        # Future year should return empty results but not crash
        result = secc_caste(self.df, "name", None, 2050)

        # Should complete without error
        assert len(result) == len(self.df)

    def test_malformed_dataframe_no_columns(self) -> None:
        """Test with DataFrame that has no columns."""
        empty_cols_df = pd.DataFrame([["value1", "value2"]])  # No column names

        with patch("sys.stdout", new_callable=StringIO):
            result = secc_caste(empty_cols_df, "name")
            # Should return original DataFrame
            pd.testing.assert_frame_equal(result, empty_cols_df)

    def test_dataframe_with_nan_names(self) -> None:
        """Test DataFrame with NaN values in name column."""
        df_with_nan = pd.DataFrame({"name": ["patel", None, "kohli", pd.NA, ""]})

        # Should handle gracefully without crashing
        result = secc_caste(df_with_nan, "name")
        assert len(result) == len(df_with_nan)

    def test_numeric_name_column(self) -> None:
        """Test with numeric values in name column."""
        df_numeric = pd.DataFrame({"name": [123, 456, 789]})

        # Should convert to string and process without errors
        result = secc_caste(df_numeric, "name")
        assert len(result) == len(df_numeric)

        # Should have expected columns
        expected_cols = [
            "name",
            "n_sc",
            "n_st",
            "n_other",
            "prop_sc",
            "prop_st",
            "prop_other",
        ]
        for col in expected_cols:
            assert col in result.columns

    def test_very_large_dataframe_memory(self) -> None:
        """Test with large DataFrame to check memory handling."""
        # Create a large DataFrame
        large_df = pd.DataFrame({"name": ["patel"] * 10000 + ["kohli"] * 10000})

        # Should handle large data without memory issues
        result = secc_caste(large_df, "name")
        assert len(result) == len(large_df)

    def test_unicode_names(self) -> None:
        """Test with Unicode characters in names."""
        df_unicode = pd.DataFrame({"name": ["पटेल", "कोहली", "राम", "श्याम"]})

        # Should process without crashing
        result = secc_caste(df_unicode, "name")
        assert len(result) == len(df_unicode)

    def test_special_characters_in_names(self) -> None:
        """Test with special characters in names."""
        df_special = pd.DataFrame({"name": ["o'brien", "d'souza", "jean-luc", "josé"]})

        # Should process without crashing
        result = secc_caste(df_special, "name")
        assert len(result) == len(df_special)

    def test_extremely_long_names(self) -> None:
        """Test with extremely long name strings."""
        df_long = pd.DataFrame({"name": ["a" * 1000, "b" * 5000, "patel"]})

        # Should process without memory issues
        result = secc_caste(df_long, "name")
        assert len(result) == len(df_long)


class TestDataPathErrors(unittest.TestCase):
    def test_get_secc_data_path_missing_package(self) -> None:
        """Test get_secc_data_path when package resources are missing."""
        with patch("outkast.secc_caste_ln.resources.files") as mock_files:
            mock_files.side_effect = ImportError("Package not found")

            with pytest.raises(ImportError):
                get_secc_data_path()

    def test_get_secc_data_path_missing_data_dir(self) -> None:
        """Test get_secc_data_path when data directory is missing."""
        with patch("outkast.secc_caste_ln.resources.files") as mock_files:
            mock_package = Mock()
            mock_files.return_value = mock_package

            # Mock the path traversal to raise an error
            mock_package.__truediv__ = Mock(
                side_effect=FileNotFoundError("Data directory not found")
            )

            with pytest.raises(FileNotFoundError):
                get_secc_data_path()


class TestClassVariableCaching(unittest.TestCase):
    def setUp(self) -> None:
        # Reset class variables before each test
        SeccCasteLnData._SeccCasteLnData__df = None
        SeccCasteLnData._SeccCasteLnData__state = None
        SeccCasteLnData._SeccCasteLnData__year = None
        self.df = pd.DataFrame({"name": ["patel", "kohli"]})

    def test_caching_same_parameters(self) -> None:
        """Test that data is cached for same parameters."""
        # First call should load data
        result1 = secc_caste(self.df, "name", "kerala", 1985)

        # Second call with same parameters should use cached data
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read:
            result2 = secc_caste(self.df, "name", "kerala", 1985)

            # read_csv should not be called again
            mock_read.assert_not_called()

            # Results should be identical
            pd.testing.assert_frame_equal(result1, result2)

    def test_cache_invalidation_different_state(self) -> None:
        """Test that cache is invalidated when state changes."""
        # Load data for kerala
        secc_caste(self.df, "name", "kerala", 1985)

        # Change to different state should reload data
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read:
            # Mock the return value
            mock_read.return_value = pd.DataFrame(
                {
                    "state": ["bihar"],
                    "birth_year": [1985],
                    "last_name": ["patel"],
                    "n_sc": [10],
                    "n_st": [5],
                    "n_other": [85],
                }
            )

            secc_caste(self.df, "name", "bihar", 1985)

            # read_csv should be called once for the new state
            mock_read.assert_called_once()

    def test_cache_invalidation_different_year(self) -> None:
        """Test that cache is invalidated when year changes."""
        # Load data for 1985
        secc_caste(self.df, "name", "kerala", 1985)

        # Change to different year should reload data
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read:
            # Mock the return value
            mock_read.return_value = pd.DataFrame(
                {
                    "state": ["kerala"],
                    "birth_year": [1990],
                    "last_name": ["patel"],
                    "n_sc": [15],
                    "n_st": [8],
                    "n_other": [77],
                }
            )

            secc_caste(self.df, "name", "kerala", 1990)

            # read_csv should be called once for the new year
            mock_read.assert_called_once()


if __name__ == "__main__":
    unittest.main()
