#!/usr/bin/env python

"""
Tests for data validation and output correctness
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from outkast import secc_caste


class TestDataValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.test_df = pd.DataFrame(
            {"name": ["patel", "kohli", "sharma", "unknown_name_xyz"]}
        )

    def test_output_column_data_types(self) -> None:
        """Test that output columns have correct data types."""
        result = secc_caste(self.test_df, "name")

        # Numeric columns should be float64 (pandas default for NaN-capable numeric)
        numeric_cols = ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]
        for col in numeric_cols:
            self.assertTrue(
                pd.api.types.is_numeric_dtype(result[col]),
                f"Column {col} should be numeric, got {result[col].dtype}",
            )

    def test_proportion_columns_sum_to_one(self) -> None:
        """Test that proportion columns sum to 1.0 for valid data."""
        result = secc_caste(self.test_df, "name")

        for idx in range(len(result)):
            row = result.iloc[idx]
            # Only test rows where we have data (not all NaN)
            if not pd.isna(row.prop_sc):
                total_prop = row.prop_sc + row.prop_st + row.prop_other
                self.assertAlmostEqual(
                    total_prop,
                    1.0,
                    places=10,
                    msg=f"Proportions don't sum to 1.0 for row {idx}: {total_prop}",
                )

    def test_proportion_values_between_zero_and_one(self) -> None:
        """Test that all proportion values are between 0 and 1."""
        result = secc_caste(self.test_df, "name")

        prop_cols = ["prop_sc", "prop_st", "prop_other"]
        for col in prop_cols:
            # Filter out NaN values for testing
            valid_values = result[col].dropna()

            # All valid values should be between 0 and 1
            self.assertTrue(
                (valid_values >= 0.0).all(),
                f"Found negative values in {col}: {valid_values[valid_values < 0].tolist()}",
            )
            self.assertTrue(
                (valid_values <= 1.0).all(),
                f"Found values > 1.0 in {col}: {valid_values[valid_values > 1].tolist()}",
            )

    def test_count_columns_non_negative(self) -> None:
        """Test that count columns (n_*) are non-negative integers."""
        result = secc_caste(self.test_df, "name")

        count_cols = ["n_sc", "n_st", "n_other"]
        for col in count_cols:
            valid_values = result[col].dropna()

            # All valid values should be non-negative
            self.assertTrue(
                (valid_values >= 0).all(),
                f"Found negative counts in {col}: {valid_values[valid_values < 0].tolist()}",
            )

    def test_missing_name_handling(self) -> None:
        """Test handling of names not in SECC data."""
        # Use a clearly non-existent name
        missing_name_df = pd.DataFrame({"name": ["definitely_not_in_secc_data_xyz"]})
        result = secc_caste(missing_name_df, "name")

        # Should have all expected columns
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
            self.assertIn(col, result.columns)

        # Values should be NaN for missing name
        self.assertTrue(pd.isna(result.iloc[0].n_sc))
        self.assertTrue(pd.isna(result.iloc[0].prop_sc))

    def test_input_dataframe_preservation(self) -> None:
        """Test that input DataFrame is not modified (fixed behavior)."""
        original_df = self.test_df.copy()
        original_columns = set(self.test_df.columns)

        result = secc_caste(self.test_df, "name")

        # Input DataFrame should remain unchanged
        self.assertNotIn("__last_name", self.test_df.columns)
        pd.testing.assert_frame_equal(self.test_df, original_df)

        # Original columns should still be present in input
        for col in original_columns:
            self.assertIn(col, self.test_df.columns)

        # Result should be different from input (no temporary columns)
        self.assertNotIn("__last_name", result.columns)

        # Result should have more columns than original input
        self.assertGreater(len(result.columns), len(original_columns))

    def test_output_row_count_matches_input(self) -> None:
        """Test that output has same number of rows as input."""
        for test_size in [1, 5, 100]:
            test_df = pd.DataFrame({"name": ["patel"] * test_size})

            result = secc_caste(test_df, "name")
            self.assertEqual(len(result), test_size)

    def test_duplicate_names_handling(self) -> None:
        """Test handling of duplicate names in input."""
        dup_df = pd.DataFrame({"name": ["patel", "patel", "kohli", "kohli", "patel"]})

        result = secc_caste(dup_df, "name")

        # Should have same length as input
        self.assertEqual(len(result), len(dup_df))

        # All "patel" rows should have identical caste data
        patel_rows = result[result.name == "patel"]
        if len(patel_rows) > 1 and not patel_rows.iloc[0].isnull().all():
            # Check that all patel rows have same values
            for col in ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]:
                unique_vals = patel_rows[col].dropna().unique()
                self.assertLessEqual(
                    len(unique_vals),
                    1,
                    f"Duplicate names should have identical values for {col}",
                )

    def test_case_insensitive_consistency(self) -> None:
        """Test that case variations of same name produce consistent results."""
        case_df = pd.DataFrame({"name": ["patel", "PATEL", "Patel", "PaTeL"]})

        result = secc_caste(case_df, "name")

        # All rows should have identical caste data (if any data exists)
        if not result.iloc[0].isnull().all():
            for col in ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]:
                unique_vals = result[col].dropna().unique()
                self.assertLessEqual(
                    len(unique_vals),
                    1,
                    f"Case variations should produce identical values for {col}",
                )

    def test_whitespace_normalization(self) -> None:
        """Test that whitespace is properly normalized."""
        whitespace_df = pd.DataFrame(
            {"name": ["patel", "  patel  ", "patel ", " patel", "\tpatel\n"]}
        )

        result = secc_caste(whitespace_df, "name")

        # All rows should have identical caste data
        if not result.iloc[0].isnull().all():
            for col in ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]:
                unique_vals = result[col].dropna().unique()
                self.assertLessEqual(
                    len(unique_vals),
                    1,
                    f"Whitespace variations should produce identical values for {col}",
                )

    def test_numeric_precision(self) -> None:
        """Test that numeric calculations maintain sufficient precision."""
        result = secc_caste(self.test_df, "name")

        # Check for reasonable precision in proportions
        for idx in range(len(result)):
            row = result.iloc[idx]
            if not pd.isna(row.prop_sc):
                # Test that we have at least 10 decimal places of precision
                total_counts = row.n_sc + row.n_st + row.n_other
                if total_counts > 0:
                    manual_prop_sc = row.n_sc / total_counts
                    self.assertAlmostEqual(
                        row.prop_sc,
                        manual_prop_sc,
                        places=10,
                        msg="Proportion calculation lacks sufficient precision",
                    )

    def test_no_infinite_values(self) -> None:
        """Test that no infinite values are produced."""
        result = secc_caste(self.test_df, "name")

        numeric_cols = ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]
        for col in numeric_cols:
            self.assertFalse(
                np.isinf(result[col]).any(), f"Found infinite values in column {col}"
            )

    def test_output_column_order(self) -> None:
        """Test that output columns include expected columns."""
        # Use a fresh dataframe to avoid modification issues
        fresh_df = pd.DataFrame({"name": ["patel", "kohli"]})
        result = secc_caste(fresh_df, "name")

        result_cols = list(result.columns)

        # Check that original columns are preserved
        self.assertIn("name", result_cols)

        # Check that new columns are present
        new_cols = ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]
        for col in new_cols:
            self.assertIn(col, result_cols)

        # Check that temporary columns are not present
        self.assertNotIn("__last_name", result_cols)

    def test_empty_string_names(self) -> None:
        """Test handling of empty string names."""
        empty_df = pd.DataFrame({"name": ["", "  ", "\t", "\n", "patel"]})

        result = secc_caste(empty_df, "name")

        # Should not crash and should have correct length
        self.assertEqual(len(result), len(empty_df))

        # Empty names should result in NaN values
        for idx in range(4):  # First 4 rows are empty/whitespace
            self.assertTrue(pd.isna(result.iloc[idx].prop_sc))

    def test_large_numbers_handling(self) -> None:
        """Test that function can handle large count numbers properly."""
        # This test verifies numeric stability with large values
        result = secc_caste(self.test_df, "name")

        # Check that any large numbers don't cause overflow issues
        numeric_cols = ["n_sc", "n_st", "n_other"]
        for col in numeric_cols:
            valid_values = result[col].dropna()
            if len(valid_values) > 0:
                # Values should be reasonable (not astronomically large)
                self.assertTrue(
                    (valid_values < 1e10).all(),
                    f"Unexpectedly large values found in {col}",
                )


class TestStateYearSpecificValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.test_df = pd.DataFrame({"name": ["patel", "kohli"]})

    def test_state_specific_data_validation(self) -> None:
        """Test data validation for state-specific queries."""
        result = secc_caste(self.test_df, "name", "kerala")

        # Same validation rules should apply
        self._validate_basic_structure(result)

    def test_year_specific_data_validation(self) -> None:
        """Test data validation for year-specific queries."""
        result = secc_caste(self.test_df, "name", None, 1985)

        # Same validation rules should apply
        self._validate_basic_structure(result)

    def test_state_year_specific_data_validation(self) -> None:
        """Test data validation for state and year specific queries."""
        result = secc_caste(self.test_df, "name", "kerala", 1985)

        # Same validation rules should apply
        self._validate_basic_structure(result)

    def _validate_basic_structure(self, result: pd.DataFrame) -> None:
        """Helper method to validate basic result structure."""
        # Check column presence
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
            self.assertIn(col, result.columns)

        # Check data types
        numeric_cols = ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]
        for col in numeric_cols:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))

        # Check proportions sum to 1 where data exists
        for idx in range(len(result)):
            row = result.iloc[idx]
            if not pd.isna(row.prop_sc):
                total_prop = row.prop_sc + row.prop_st + row.prop_other
                self.assertAlmostEqual(total_prop, 1.0, places=10)


if __name__ == "__main__":
    unittest.main()
