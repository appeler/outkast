#!/usr/bin/env python

"""
Pytest configuration and fixtures for outkast tests
"""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def sample_names_df() -> pd.DataFrame:
    """Fixture providing a sample DataFrame with Indian names for testing."""
    return pd.DataFrame({
        "name": ["patel", "kohli", "sharma", "gupta", "singh", "kumar"],
        "age": [25, 30, 35, 40, 45, 50],
        "city": ["mumbai", "delhi", "bangalore", "chennai", "pune", "hyderabad"]
    })


@pytest.fixture
def edge_case_names_df() -> pd.DataFrame:
    """Fixture providing DataFrame with edge case names."""
    return pd.DataFrame({
        "name": [
            "patel",           # Normal case
            "PATEL",           # Uppercase
            "  patel  ",       # Whitespace
            "",                # Empty string
            None,              # None value
            "o'brien",         # Apostrophe
            "jean-luc",        # Hyphen
            "रम",              # Unicode
            "a" * 100,         # Very long name
            "123",             # Numeric string
        ]
    })


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Fixture providing an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def large_df() -> pd.DataFrame:
    """Fixture providing a large DataFrame for performance testing."""
    names = ["patel", "kohli", "sharma"] * 1000
    return pd.DataFrame({"name": names})


@pytest.fixture
def temp_csv_file() -> Generator[Path, None, None]:
    """Fixture providing a temporary CSV file with test data."""
    test_data = pd.DataFrame({
        "name": ["patel", "kohli", "sharma", "gupta"],
        "age": [25, 30, 35, 40],
        "occupation": ["engineer", "doctor", "teacher", "lawyer"]
    })

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        test_data.to_csv(f.name, index=False)
        temp_path = Path(f.name)

    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_csv_no_header() -> Generator[Path, None, None]:
    """Fixture providing a temporary CSV file without headers."""
    test_data = pd.DataFrame({
        "name": ["patel", "kohli", "sharma"],
        "value": [100, 200, 300]
    })

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        test_data.to_csv(f.name, index=False, header=False)
        temp_path = Path(f.name)

    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.fixture
def mock_secc_data() -> pd.DataFrame:
    """Fixture providing mock SECC data for testing."""
    return pd.DataFrame({
        "state": ["kerala", "kerala", "bihar", "bihar", "uttar pradesh", "uttar pradesh"],
        "birth_year": [1980, 1985, 1980, 1985, 1980, 1985],
        "last_name": ["patel", "patel", "kohli", "kohli", "sharma", "sharma"],
        "n_sc": [10, 15, 5, 8, 20, 25],
        "n_st": [2, 3, 1, 2, 4, 5],
        "n_other": [88, 82, 94, 90, 76, 70]
    })


@pytest.fixture
def expected_secc_columns() -> list[str]:
    """Fixture providing expected SECC output columns."""
    return ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]


@pytest.fixture(scope="session")
def known_indian_states() -> list[str]:
    """Fixture providing list of known Indian states for testing."""
    return [
        "kerala", "bihar", "uttar pradesh", "maharashtra", "tamil nadu",
        "karnataka", "gujarat", "rajasthan", "punjab", "haryana"
    ]


@pytest.fixture
def cleanup_output_files():
    """Fixture to clean up test output files."""
    output_files = []

    def register_file(file_path: str | Path) -> None:
        output_files.append(Path(file_path))

    yield register_file

    # Cleanup after test
    for file_path in output_files:
        file_path.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def reset_secc_cache():
    """Fixture to reset SECC class cache before each test."""
    from outkast.secc_caste_ln import SeccCasteLnData

    # Reset class variables before each test
    SeccCasteLnData._SeccCasteLnData__df = None
    SeccCasteLnData._SeccCasteLnData__state = None
    SeccCasteLnData._SeccCasteLnData__year = None


@pytest.fixture
def test_data_directory() -> Path:
    """Fixture providing the test data directory path."""
    return Path(__file__).parent


@pytest.fixture
def sample_input_csv() -> str:
    """Fixture providing path to sample input CSV for CLI testing."""
    return str(Path(__file__).parent / "input.csv")


# Custom markers for test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "cli: marks tests as CLI tests"
    )
    config.addinivalue_line(
        "markers", "mock: marks tests that use mocking"
    )


# Skip markers for conditional testing
skip_if_no_secc_data = pytest.mark.skipif(
    True,  # We'll always skip these in CI/development without real data
    reason="SECC data file not available"
)


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Fixture for timing test execution."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()
