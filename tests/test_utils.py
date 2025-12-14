#!/usr/bin/env python

"""
Tests for utils.py functions
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from outkast.utils import column_exists, find_ngrams, fixup_columns


class TestColumnExists(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame({"name": ["john", "jane"], "age": [25, 30]})

    def test_column_exists_string_column(self) -> None:
        """Test column_exists with valid string column name."""
        self.assertTrue(column_exists(self.df, "name"))
        self.assertTrue(column_exists(self.df, "age"))

    def test_column_exists_integer_column(self) -> None:
        """Test column_exists with integer column index."""
        # Integer columns should be treated as column names, not positional indices
        # Since our DataFrame has ["name", "age"], integer 0 is not a valid column
        with patch("outkast.utils.logger") as mock_logger:
            self.assertFalse(column_exists(self.df, 0))  # 0 not in ["name", "age"]
            mock_logger.error.assert_called_once()

        # Same for other integers
        with patch("outkast.utils.logger") as mock_logger:
            self.assertFalse(column_exists(self.df, 5))  # 5 not in columns
            mock_logger.error.assert_called_once()

    def test_column_not_exists_string(self) -> None:
        """Test column_exists with invalid string column name."""
        with patch("outkast.utils.logger") as mock_logger:
            result = column_exists(self.df, "invalid_column")
            self.assertFalse(result)
            mock_logger.error.assert_called_once()

    def test_column_not_exists_integer(self) -> None:
        """Test column_exists with invalid integer column index."""
        with patch("outkast.utils.logger") as mock_logger:
            result = column_exists(self.df, 10)
            self.assertFalse(result)
            mock_logger.error.assert_called_once()

    def test_column_exists_empty_string(self) -> None:
        """Test column_exists with empty string."""
        with patch("outkast.utils.logger") as mock_logger:
            result = column_exists(self.df, "")
            self.assertFalse(result)
            mock_logger.error.assert_called_once()

    def test_column_exists_none(self) -> None:
        """Test column_exists with None."""
        with patch("outkast.utils.logger") as mock_logger:
            result = column_exists(self.df, None)
            self.assertFalse(result)
            mock_logger.error.assert_called_once()

    def test_column_exists_empty_dataframe(self) -> None:
        """Test column_exists with empty DataFrame."""
        empty_df = pd.DataFrame()
        with patch("outkast.utils.logger") as mock_logger:
            result = column_exists(empty_df, "any_column")
            self.assertFalse(result)
            mock_logger.error.assert_called_once()


class TestFixupColumns(unittest.TestCase):
    def test_fixup_columns_all_strings(self) -> None:
        """Test fixup_columns with all string columns."""
        cols = ["name", "age", "city"]
        result = fixup_columns(cols)
        self.assertEqual(result, ["name", "age", "city"])

    def test_fixup_columns_all_integers(self) -> None:
        """Test fixup_columns with all integer columns."""
        cols = [0, 1, 2]
        result = fixup_columns(cols)
        self.assertEqual(result, ["col0", "col1", "col2"])

    def test_fixup_columns_mixed(self) -> None:
        """Test fixup_columns with mixed string and integer columns."""
        cols = ["name", 1, "city", 3]
        result = fixup_columns(cols)
        self.assertEqual(result, ["name", "col1", "city", "col3"])

    def test_fixup_columns_empty_list(self) -> None:
        """Test fixup_columns with empty list."""
        cols = []
        result = fixup_columns(cols)
        self.assertEqual(result, [])

    def test_fixup_columns_single_string(self) -> None:
        """Test fixup_columns with single string column."""
        cols = ["name"]
        result = fixup_columns(cols)
        self.assertEqual(result, ["name"])

    def test_fixup_columns_single_integer(self) -> None:
        """Test fixup_columns with single integer column."""
        cols = [0]
        result = fixup_columns(cols)
        self.assertEqual(result, ["col0"])


class TestFindNgrams(unittest.TestCase):
    def setUp(self) -> None:
        self.vocab = ["ab", "bc", "cd", "de", "ef"]

    def test_find_ngrams_valid_text(self) -> None:
        """Test find_ngrams with valid text."""
        result = find_ngrams(self.vocab, "abcde", 2)
        # vocab = ["ab", "bc", "cd", "de", "ef"] -> indices 0,1,2,3,4
        # "abcde" with n=2 -> "ab", "bc", "cd", "de" -> indices 0,1,2,3
        self.assertEqual(result, [0, 1, 2, 3])

    def test_find_ngrams_partial_match(self) -> None:
        """Test find_ngrams with partial vocabulary matches."""
        result = find_ngrams(self.vocab, "abxyz", 2)
        # vocab = ["ab", "bc", "cd", "de", "ef"]
        # "abxyz" with n=2 -> "ab", "bx", "xy", "yz"
        # "ab" is at index 0, others not found (return -1)
        self.assertEqual(result, [0, -1, -1, -1])  # 'ab' found at index 0, others not found

    def test_find_ngrams_no_matches(self) -> None:
        """Test find_ngrams with no vocabulary matches."""
        result = find_ngrams(self.vocab, "xyz", 2)
        self.assertEqual(result, [-1, -1])  # 'xy', 'yz' not in vocab

    def test_find_ngrams_empty_text(self) -> None:
        """Test find_ngrams with empty text."""
        result = find_ngrams(self.vocab, "", 2)
        self.assertEqual(result, [])

    def test_find_ngrams_short_text(self) -> None:
        """Test find_ngrams with text shorter than n."""
        result = find_ngrams(self.vocab, "a", 2)
        self.assertEqual(result, [])

    def test_find_ngrams_non_string_input(self) -> None:
        """Test find_ngrams with non-string input."""
        result = find_ngrams(self.vocab, None, 2)
        self.assertEqual(result, [])

        result = find_ngrams(self.vocab, 123, 2)
        self.assertEqual(result, [])

    def test_find_ngrams_single_character(self) -> None:
        """Test find_ngrams with n=1."""
        vocab = ["a", "b", "c"]
        result = find_ngrams(vocab, "abc", 1)
        # vocab indices: "a"=0, "b"=1, "c"=2
        # "abc" with n=1 -> "a", "b", "c" -> indices 0, 1, 2
        self.assertEqual(result, [0, 1, 2])

    def test_find_ngrams_large_n(self) -> None:
        """Test find_ngrams with n larger than text length."""
        result = find_ngrams(self.vocab, "abc", 5)
        self.assertEqual(result, [])

    def test_find_ngrams_exact_match_length(self) -> None:
        """Test find_ngrams where text length equals n."""
        result = find_ngrams(self.vocab, "ab", 2)
        # "ab" is at index 0 in vocab = ["ab", "bc", "cd", "de", "ef"]
        self.assertEqual(result, [0])

    def test_find_ngrams_empty_vocab(self) -> None:
        """Test find_ngrams with empty vocabulary."""
        empty_vocab = []
        result = find_ngrams(empty_vocab, "abc", 2)
        # With empty vocab, .index() will raise ValueError, caught and returns -1
        # So result should be [-1, -1] for "ab", "bc"
        self.assertEqual(result, [-1, -1])


if __name__ == "__main__":
    unittest.main()
