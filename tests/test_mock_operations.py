#!/usr/bin/env python

"""
Tests for mocked file operations and isolated unit testing
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from outkast.secc_caste_ln import SeccCasteLnData, get_secc_data_path, secc_caste


class TestMockedFileOperations(unittest.TestCase):
    def setUp(self) -> None:
        # Reset class variables before each test
        SeccCasteLnData._SeccCasteLnData__df = None
        SeccCasteLnData._SeccCasteLnData__state = None
        SeccCasteLnData._SeccCasteLnData__year = None

        self.sample_df = pd.DataFrame({"name": ["patel", "kohli"]})

        # Sample SECC data for mocking
        self.mock_secc_data = pd.DataFrame(
            {
                "state": ["kerala", "kerala", "bihar", "bihar"],
                "birth_year": [1980, 1985, 1980, 1985],
                "last_name": ["patel", "patel", "kohli", "kohli"],
                "n_sc": [10, 15, 5, 8],
                "n_st": [2, 3, 1, 2],
                "n_other": [88, 82, 94, 90],
            }
        )

    def test_secc_caste_with_mocked_data_file(self) -> None:
        """Test secc_caste with completely mocked data file."""
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            mock_read_csv.return_value = self.mock_secc_data.copy()

            result = secc_caste(self.sample_df, "name")

            # Verify read_csv was called once
            mock_read_csv.assert_called_once()

            # Check that result has expected structure
            assert len(result) == len(self.sample_df)
            expected_cols = [
                "name",
                "prop_sc",
                "prop_st",
                "prop_other",
                "n_sc",
                "n_st",
                "n_other",
            ]
            for col in expected_cols:
                assert col in result.columns

    def test_secc_caste_with_mocked_path_and_data(self) -> None:
        """Test secc_caste with both path and data mocked."""
        mock_path = Mock()
        mock_path.exists.return_value = True

        with (
            patch("outkast.secc_caste_ln.get_secc_data_path") as mock_get_path,
            patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv,
        ):
            mock_get_path.return_value = mock_path
            mock_read_csv.return_value = self.mock_secc_data.copy()

            result = secc_caste(self.sample_df, "name", "kerala")

            # Verify both functions were called
            mock_get_path.assert_called_once()
            mock_read_csv.assert_called_once_with(
                mock_path,
                usecols=["state", "birth_year", "last_name", "n_sc", "n_st", "n_other"],
            )

            # Check result integrity
            assert len(result) == len(self.sample_df)

    def test_multiple_calls_cache_behavior_mocked(self) -> None:
        """Test caching behavior with mocked file operations."""
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            mock_read_csv.return_value = self.mock_secc_data.copy()

            # First call
            result1 = secc_caste(self.sample_df, "name", "kerala", 1985)

            # Second call with same parameters
            result2 = secc_caste(self.sample_df, "name", "kerala", 1985)

            # Should only call read_csv once due to caching
            assert mock_read_csv.call_count == 1

            # Results should be identical
            pd.testing.assert_frame_equal(result1, result2)

    def test_cache_invalidation_with_mock(self) -> None:
        """Test cache invalidation with different parameters using mocks."""
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            mock_read_csv.return_value = self.mock_secc_data.copy()

            # First call
            secc_caste(self.sample_df, "name", "kerala", 1985)

            # Second call with different state
            secc_caste(self.sample_df, "name", "bihar", 1985)

            # Should call read_csv twice due to cache invalidation
            assert mock_read_csv.call_count == 2

    def test_get_secc_data_path_mocked(self) -> None:
        """Test get_secc_data_path function with mocked resources."""
        mock_data_file = Mock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_data_file
        mock_context.__exit__.return_value = False

        with (
            patch("outkast.secc_caste_ln.resources.as_file") as mock_as_file,
            patch("outkast.secc_caste_ln.resources.files") as mock_files,
        ):
            mock_files.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = "mock_resource"
            mock_as_file.return_value = mock_context

            result = get_secc_data_path()

            # Should return the mocked data file
            assert result == mock_data_file

            # Verify the resource path construction
            mock_files.assert_called_once_with("outkast")

    def test_list_states_with_mocked_data(self) -> None:
        """Test list_states function with mocked data."""
        mock_states_data = pd.DataFrame(
            {"state": ["kerala", "bihar", "uttar pradesh", "kerala", "bihar"]}
        )

        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            mock_read_csv.return_value = mock_states_data

            states = SeccCasteLnData.list_states()

            # Should return unique states
            assert isinstance(states, list)
            expected_states = ["kerala", "bihar", "uttar pradesh"]
            assert set(states) == set(expected_states)

            # Verify read_csv was called with correct parameters
            mock_read_csv.assert_called_once()
            call_args = mock_read_csv.call_args
            assert "usecols" in call_args.kwargs
            assert call_args.kwargs["usecols"] == ["state"]

    def test_secc_caste_aggregation_logic_mocked(self) -> None:
        """Test data aggregation logic with controlled mock data."""
        # Create specific test data for aggregation testing
        test_aggregation_data = pd.DataFrame(
            {
                "state": ["kerala", "kerala", "kerala"],
                "birth_year": [1980, 1980, 1985],
                "last_name": ["patel", "patel", "patel"],
                "n_sc": [10, 20, 15],
                "n_st": [5, 5, 3],
                "n_other": [85, 75, 82],
            }
        )

        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            mock_read_csv.return_value = test_aggregation_data

            # Test state-only aggregation
            result = secc_caste(self.sample_df, "name", "kerala", None)

            # For "patel", should aggregate all kerala data
            patel_row = result[result.name == "patel"].iloc[0]
            expected_n_sc = 10 + 20 + 15  # 45
            expected_n_total = (10 + 5 + 85) + (20 + 5 + 75) + (15 + 3 + 82)  # 300
            expected_prop_sc = expected_n_sc / expected_n_total

            assert patel_row.n_sc == pytest.approx(expected_n_sc)
            assert patel_row.prop_sc == pytest.approx(expected_prop_sc, abs=1e-10)

    def test_error_handling_with_mocked_exceptions(self) -> None:
        """Test error handling when mocked operations raise exceptions."""
        with patch("outkast.secc_caste_ln.get_secc_data_path") as mock_path:
            mock_path.side_effect = FileNotFoundError("Mock file not found")

            with pytest.raises(FileNotFoundError):
                secc_caste(self.sample_df, "name")

    def test_pandas_operations_isolation(self) -> None:
        """Test that pandas operations don't have side effects."""
        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            # Create a DataFrame that we can monitor for mutations
            original_data = self.mock_secc_data.copy()
            mock_read_csv.return_value = original_data

            # Run the function
            secc_caste(self.sample_df, "name")

            # Original mock data should not be modified
            pd.testing.assert_frame_equal(
                mock_read_csv.return_value, self.mock_secc_data
            )

            # Result should have expected columns without modifying input
            # Check that input DataFrame wasn't modified
            assert "__last_name" not in self.sample_df.columns

    def test_memory_efficiency_with_large_mocked_data(self) -> None:
        """Test memory efficiency with large mocked datasets."""
        # Create large mock dataset
        large_mock_data = pd.concat([self.mock_secc_data] * 1000, ignore_index=True)

        with patch("outkast.secc_caste_ln.pd.read_csv") as mock_read_csv:
            mock_read_csv.return_value = large_mock_data

            # Should handle large data without issues
            result = secc_caste(self.sample_df, "name")

            # Result size should still match input
            assert len(result) == len(self.sample_df)

            # Memory should be manageable (no specific assertion, just shouldn't crash)
            assert result is not None


if __name__ == "__main__":
    unittest.main()
