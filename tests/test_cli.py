#!/usr/bin/env python

"""
Tests for CLI functionality
"""

from __future__ import annotations

import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from outkast.secc_caste_ln import main


class TestCLIFunctionality(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temporary CSV file for testing
        self.test_data = pd.DataFrame(
            {"name": ["patel", "kohli", "sharma", "gupta"], "age": [25, 30, 35, 40]}
        )

        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self) -> None:
        # Clean up temporary files
        self.temp_path.unlink(missing_ok=True)

        # Clean up any output files
        output_files = [
            Path("secc-caste-output.csv"),
            Path("test-output.csv"),
        ]
        for file_path in output_files:
            file_path.unlink(missing_ok=True)

    def test_cli_basic_functionality(self) -> None:
        """Test basic CLI functionality with required arguments."""
        args = [
            str(self.temp_path),
            "--last-name",
            "name",
        ]

        # CLI should complete successfully
        result = main(args)

        # Should return 0 on success
        self.assertEqual(result, 0)

        # Check that output file was created
        output_file = Path("secc-caste-output.csv")
        self.assertTrue(output_file.exists())

        # Verify output file content
        result_df = pd.read_csv(output_file)
        expected_cols = [
            "name",
            "age",
            "n_sc",
            "n_st",
            "n_other",
            "prop_sc",
            "prop_st",
            "prop_other",
        ]
        for col in expected_cols:
            self.assertIn(col, result_df.columns)

        self.assertEqual(len(result_df), len(self.test_data))

    def test_cli_with_custom_output(self) -> None:
        """Test CLI with custom output filename."""
        args = [
            str(self.temp_path),
            "--last-name",
            "name",
            "--output",
            "test-output.csv",
        ]

        with patch("sys.stdout", new_callable=StringIO):
            result = main(args)

            self.assertEqual(result, 0)

        # Check that custom output file was created
        output_file = Path("test-output.csv")
        self.assertTrue(output_file.exists())

    def test_cli_with_state_filter(self) -> None:
        """Test CLI with state filtering."""
        args = [
            str(self.temp_path),
            "--last-name",
            "name",
            "--state",
            "kerala",
        ]

        with patch("sys.stdout", new_callable=StringIO):
            result = main(args)

            self.assertEqual(result, 0)

    def test_cli_with_year_filter(self) -> None:
        """Test CLI with year filtering."""
        args = [
            str(self.temp_path),
            "--last-name",
            "name",
            "--year",
            "1985",
        ]

        with patch("sys.stdout", new_callable=StringIO):
            result = main(args)

            self.assertEqual(result, 0)

    def test_cli_with_state_and_year_filter(self) -> None:
        """Test CLI with both state and year filtering."""
        args = [
            str(self.temp_path),
            "--last-name",
            "name",
            "--state",
            "kerala",
            "--year",
            "1985",
        ]

        with patch("sys.stdout", new_callable=StringIO):
            result = main(args)

            self.assertEqual(result, 0)

    def test_cli_with_integer_column_index(self) -> None:
        """Test CLI using integer column index instead of name."""
        # Create CSV without header
        temp_no_header = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.test_data.to_csv(temp_no_header.name, index=False, header=False)
        temp_no_header.close()
        temp_path_no_header = Path(temp_no_header.name)

        try:
            args = [
                str(temp_path_no_header),
                "--last-name",
                "0",  # First column (name)
            ]

            with patch("sys.stdout", new_callable=StringIO):
                result = main(args)

                self.assertEqual(result, 0)

        finally:
            temp_path_no_header.unlink(missing_ok=True)

    def test_cli_invalid_column_name(self) -> None:
        """Test CLI with invalid column name."""
        args = [
            str(self.temp_path),
            "--last-name",
            "invalid_column",
        ]

        with patch("sys.stdout", new_callable=StringIO):
            result = main(args)

            # Should return -1 on error
            self.assertEqual(result, -1)

    def test_cli_invalid_column_index(self) -> None:
        """Test CLI with invalid column index."""
        args = [
            str(self.temp_path),
            "--last-name",
            "10",  # Out of bounds index
        ]

        with patch("sys.stdout", new_callable=StringIO):
            result = main(args)

            # Should return -1 on error
            self.assertEqual(result, -1)

    def test_cli_missing_input_file(self) -> None:
        """Test CLI with non-existent input file."""
        args = [
            "nonexistent_file.csv",
            "--last-name",
            "name",
        ]

        with self.assertRaises(FileNotFoundError):
            main(args)

    def test_cli_missing_required_argument(self) -> None:
        """Test CLI without required --last-name argument."""
        args = [str(self.temp_path)]

        with self.assertRaises(SystemExit):
            main(args)

    def test_cli_help_option(self) -> None:
        """Test CLI help option."""
        args = ["--help"]

        with self.assertRaises(SystemExit):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main(args)

                # Should contain help text
                output = mock_stdout.getvalue()
                self.assertIn("Appends SECC 2011 data columns", output)

    def test_cli_invalid_state(self) -> None:
        """Test CLI with invalid state name."""
        args = [
            str(self.temp_path),
            "--last-name",
            "name",
            "--state",
            "invalid_state",
        ]

        # Should exit with error due to invalid choice
        with self.assertRaises(SystemExit):
            main(args)

    def test_cli_valid_states_in_choices(self) -> None:
        """Test that CLI accepts valid state names."""
        # This test verifies the state choices are properly configured
        valid_states = ["kerala", "uttar pradesh", "bihar", "maharashtra"]

        for state in valid_states:
            args = [
                str(self.temp_path),
                "--last-name",
                "name",
                "--state",
                state,
            ]

            with patch("sys.stdout", new_callable=StringIO):
                # Should not raise SystemExit for valid states
                result = main(args)
                self.assertEqual(result, 0)

    def test_cli_output_file_column_fixup(self) -> None:
        """Test that output file has properly fixed column names."""
        # Create input with integer column names
        df_int_cols = pd.DataFrame([[1, "patel"], [2, "kohli"]])  # No header

        temp_int_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        df_int_cols.to_csv(temp_int_file.name, index=False, header=False)
        temp_int_file.close()
        temp_int_path = Path(temp_int_file.name)

        try:
            args = [
                str(temp_int_path),
                "--last-name",
                "1",  # Second column
                "--output",
                "int-cols-output.csv",
            ]

            with patch("sys.stdout", new_callable=StringIO):
                result = main(args)
                self.assertEqual(result, 0)

            # Check that column names are fixed
            output_file = Path("int-cols-output.csv")
            self.assertTrue(output_file.exists())

            result_df = pd.read_csv(output_file)

            # Should have col0, col1 instead of 0, 1
            self.assertIn("col0", result_df.columns)
            self.assertIn("col1", result_df.columns)

            output_file.unlink(missing_ok=True)

        finally:
            temp_int_path.unlink(missing_ok=True)


class TestCLIMainFunction(unittest.TestCase):
    def test_main_with_none_argv(self) -> None:
        """Test main function with None argv (uses sys.argv)."""
        with patch("sys.argv", ["secc_caste", "--help"]):
            with self.assertRaises(SystemExit):
                main(None)

    def test_main_with_empty_argv(self) -> None:
        """Test main function with empty argv list."""
        with self.assertRaises(SystemExit):
            main([])


if __name__ == "__main__":
    unittest.main()
