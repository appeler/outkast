#!/usr/bin/env python

"""
Example tests using fixtures to demonstrate their usage
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd
import pytest

from outkast import secc_caste


class TestFixtureUsage:
    """Tests demonstrating fixture usage (pytest style)."""

    def test_with_sample_names_fixture(self, sample_names_df):
        """Test using the sample names fixture."""
        result = secc_caste(sample_names_df, "name")

        # Basic checks
        assert len(result) == len(sample_names_df)
        assert "prop_sc" in result.columns

        # Check that original columns are preserved
        for col in sample_names_df.columns:
            assert col in result.columns

    def test_with_edge_case_names(self, edge_case_names_df):
        """Test using the edge case names fixture."""
        # Should handle all edge cases without crashing
        result = secc_caste(edge_case_names_df, "name")

        assert len(result) == len(edge_case_names_df)
        assert "prop_sc" in result.columns

    def test_with_empty_df(self, empty_df):
        """Test using the empty DataFrame fixture."""
        result = secc_caste(empty_df, "name")

        # Should return empty DataFrame with same structure
        pd.testing.assert_frame_equal(result, empty_df)

    @pytest.mark.slow
    def test_with_large_df(self, large_df):
        """Test using the large DataFrame fixture."""
        result = secc_caste(large_df, "name")

        assert len(result) == len(large_df)
        assert "prop_sc" in result.columns

    def test_with_temp_csv_file(self, temp_csv_file):
        """Test using the temporary CSV file fixture."""
        # File should exist
        assert temp_csv_file.exists()

        # Should be readable as CSV
        df = pd.read_csv(temp_csv_file)
        assert "name" in df.columns

        # Use it with secc_caste
        result = secc_caste(df, "name")
        assert len(result) == len(df)

    def test_expected_columns_fixture(self, expected_secc_columns):
        """Test using the expected columns fixture."""
        sample_df = pd.DataFrame({"name": ["patel", "kohli"]})
        result = secc_caste(sample_df, "name")

        # All expected columns should be present
        for col in expected_secc_columns:
            assert col in result.columns

    def test_known_states_fixture(self, known_indian_states):
        """Test using the known states fixture."""
        # Should contain expected states
        assert "kerala" in known_indian_states
        assert "bihar" in known_indian_states
        assert len(known_indian_states) > 5

    def test_performance_timer(self, performance_timer, sample_names_df):
        """Test using the performance timer fixture."""
        performance_timer.start()
        result = secc_caste(sample_names_df, "name")
        performance_timer.stop()

        # Should complete in reasonable time
        assert performance_timer.elapsed is not None
        assert performance_timer.elapsed < 10.0  # Should be fast
        assert len(result) == len(sample_names_df)

    def test_cleanup_output_files(self, cleanup_output_files, sample_names_df):
        """Test using the cleanup fixture."""

        # Register files for cleanup
        cleanup_output_files("test-output-1.csv")
        cleanup_output_files("test-output-2.csv")

        # Files should be cleaned up automatically after test


class TestFixtureIntegration(unittest.TestCase):
    """Tests demonstrating fixture integration with unittest."""

    def setUp(self) -> None:
        # Manual setup for unittest style
        self.sample_df = pd.DataFrame({"name": ["patel", "kohli", "sharma"]})

    def test_sample_data_consistency(self) -> None:
        """Test that fixture data is consistent with expectations."""
        result = secc_caste(self.sample_df, "name")

        # Check basic structure
        assert len(result) == len(self.sample_df)

        # Check expected columns exist
        expected_cols = ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]
        for col in expected_cols:
            assert col in result.columns

    def test_temporary_file_creation(self) -> None:
        """Test temporary file operations."""
        import tempfile

        # Create temp file with test data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.sample_df.to_csv(f.name, index=False)
            temp_path = Path(f.name)

        try:
            # Use the temp file
            assert temp_path.exists()

            df = pd.read_csv(temp_path)
            result = secc_caste(df, "name")
            assert len(result) == len(df)

        finally:
            # Clean up
            temp_path.unlink(missing_ok=True)


# Performance tests using fixtures
@pytest.mark.slow
class TestPerformanceWithFixtures:
    """Performance tests using fixtures."""

    def test_large_dataset_performance(self, large_df, performance_timer):
        """Test performance with large dataset."""
        performance_timer.start()
        result = secc_caste(large_df, "name")
        performance_timer.stop()

        # Should complete in reasonable time even with large data
        assert performance_timer.elapsed < 30.0  # 30 second limit
        assert len(result) == len(large_df)

    def test_repeated_calls_performance(self, sample_names_df, performance_timer):
        """Test performance of repeated calls (should benefit from caching)."""
        # First call
        performance_timer.start()
        result1 = secc_caste(sample_names_df, "name")
        performance_timer.stop()
        first_time = performance_timer.elapsed

        # Second call (should be faster due to caching)
        performance_timer.start()
        result2 = secc_caste(sample_names_df, "name")
        performance_timer.stop()
        second_time = performance_timer.elapsed

        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

        # Both calls should complete in reasonable time
        assert first_time is not None
        assert second_time is not None
        assert first_time < 10.0  # Should be fast
        assert second_time < 10.0  # Should be fast


# Integration tests using multiple fixtures
@pytest.mark.integration
class TestIntegrationWithFixtures:
    """Integration tests using multiple fixtures."""

    def test_end_to_end_with_fixtures(
        self, temp_csv_file, expected_secc_columns, cleanup_output_files
    ):
        """Test end-to-end workflow using fixtures."""
        from outkast.secc_caste_ln import main

        # Register output file for cleanup
        output_file = "integration-test-output.csv"
        cleanup_output_files(output_file)

        # Run CLI command
        args = [str(temp_csv_file), "--last-name", "name", "--output", output_file]

        result_code = main(args)
        assert result_code == 0

        # Verify output file
        output_path = Path(output_file)
        assert output_path.exists()

        # Verify output content
        result_df = pd.read_csv(output_path)
        for col in expected_secc_columns:
            assert col in result_df.columns


if __name__ == "__main__":
    unittest.main()
