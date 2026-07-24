#!/usr/bin/env python

"""
Tests for secc_caste_ln.py

"""

from __future__ import annotations

import unittest
from io import StringIO
from unittest.mock import patch

import pandas as pd
import pytest

from outkast import secc_caste
from outkast.secc_caste_ln import SeccCasteLnData


class TestSeccCasteLnFunction(unittest.TestCase):
    def setUp(self) -> None:
        names = [
            {"name": "patel"},
            {"name": "kohli"},
            {"name": "lal"},
            {"name": "agarwal"},
        ]
        self.df = pd.DataFrame(names)

    def tearDown(self) -> None:
        pass

    def test_secc_caste_ln_basic(self) -> None:
        """Test basic functionality with all states and years."""
        odf = secc_caste(self.df, "name")

        # Check all expected columns are present
        expected_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in expected_cols:
            assert col in odf.columns

        # Check data integrity
        assert len(odf) == len(self.df)
        assert odf.iloc[2].prop_sc > 0.3

    def test_secc_caste_ln_state_specific(self) -> None:
        """Test with specific state filtering."""
        odf = secc_caste(self.df, "name", "kerala")

        expected_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in expected_cols:
            assert col in odf.columns

        assert len(odf) == len(self.df)
        assert odf.iloc[2].prop_sc > 0.1

    def test_secc_caste_ln_state_year_specific(self) -> None:
        """Test with both state and year filtering."""
        odf = secc_caste(self.df, "name", "kerala", 1985)

        expected_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in expected_cols:
            assert col in odf.columns

        assert len(odf) == len(self.df)
        assert odf.iloc[2].prop_sc > 0.1

    def test_secc_caste_multiple_state_year_combinations(self) -> None:
        """Test different combinations of state and year parameters."""
        test_cases = [
            (None, None),
            ("kerala", None),
            (None, 1985),
            ("kerala", 1985),
        ]

        for state, year in test_cases:
            with self.subTest(state=state, year=year):
                odf = secc_caste(self.df, "name", state, year)

                # Basic structure tests
                expected_cols = [
                    "prop_sc",
                    "prop_st",
                    "prop_other",
                    "n_sc",
                    "n_st",
                    "n_other",
                ]
                for col in expected_cols:
                    assert col in odf.columns

                assert len(odf) == len(self.df)

                # Check proportions sum to 1 (or NaN for missing data)
                for idx in range(len(odf)):
                    row = odf.iloc[idx]
                    if not pd.isna(row.prop_sc):
                        total_prop = row.prop_sc + row.prop_st + row.prop_other
                        assert total_prop == pytest.approx(1.0, abs=1e-10)

    def test_secc_caste_invalid_column(self) -> None:
        """Test behavior with invalid column name."""
        with patch("outkast.secc_caste_ln.logger") as mock_logger:
            result = secc_caste(self.df, "invalid_column")

            # Should return original dataframe unchanged
            pd.testing.assert_frame_equal(result, self.df)

            # Should log error message
            mock_logger.error.assert_called_once()

    def test_secc_caste_empty_dataframe(self) -> None:
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame()
        with patch("sys.stdout", new_callable=StringIO):
            result = secc_caste(empty_df, "name")
            pd.testing.assert_frame_equal(result, empty_df)

    def test_secc_caste_whitespace_names(self) -> None:
        """Test that whitespace is properly handled."""
        df_with_spaces = pd.DataFrame(
            {"name": ["  patel  ", " kohli", "lal ", "  agarwal  "]}
        )

        odf = secc_caste(df_with_spaces, "name")

        # Should process without errors
        assert len(odf) == len(df_with_spaces)
        expected_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in expected_cols:
            assert col in odf.columns

    def test_secc_caste_case_insensitive(self) -> None:
        """Test that name matching is case insensitive."""
        df_mixed_case = pd.DataFrame({"name": ["PATEL", "Kohli", "lal", "AGARWAL"]})

        odf = secc_caste(df_mixed_case, "name")

        # Should process without errors
        assert len(odf) == len(df_mixed_case)
        expected_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in expected_cols:
            assert col in odf.columns

    def test_secc_caste_data_types(self) -> None:
        """Test that output data types are correct."""
        odf = secc_caste(self.df, "name")

        # Check that numeric columns are numeric
        numeric_cols = ["prop_sc", "prop_st", "prop_other", "n_sc", "n_st", "n_other"]
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(odf[col])

    def test_secc_caste_no_temp_columns(self) -> None:
        """Test that temporary columns are cleaned up."""
        odf = secc_caste(self.df, "name")

        # Should not contain temporary __last_name column
        assert "__last_name" not in odf.columns

    def test_list_states_function(self) -> None:
        """Test that list_states returns valid state names."""
        states = SeccCasteLnData.list_states()

        # Should return a non-empty list
        assert isinstance(states, list)
        assert len(states) > 0

        # Should contain some expected states
        expected_states = ["kerala", "uttar pradesh", "bihar"]
        for state in expected_states:
            assert state in states


if __name__ == "__main__":
    unittest.main()
