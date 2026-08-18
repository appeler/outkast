"""Small DataFrame column-handling helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pandas as pd

logger = logging.getLogger(__name__)


def column_exists(df: pd.DataFrame, col: str | int) -> bool:
    """Check the column name exists in the DataFrame.

    Args:
        df: Pandas DataFrame.
        col: Column name.

    Returns:
        True if exists, False if not exists.
    """
    if col is None or col == "":
        logger.error("Column name cannot be None or empty")
        return False

    if col not in df.columns:
        logger.error("The specified column `%s` not found in the input file", col)
        return False

    return True


def fixup_columns(cols: Sequence[str | int]) -> list[str]:
    """Replace index location column to name with `col` prefix.

    Args:
        cols: List of original columns

    Returns:
        List of column names
    """
    out_cols = []
    for col in cols:
        if isinstance(col, int):
            out_cols.append(f"col{col:d}")
        else:
            out_cols.append(col)
    return out_cols


def find_ngrams(vocab: Sequence[str], text: str, n: int) -> list[int]:
    """Find and return list of the index of n-grams in the vocabulary list.

    Generate the n-grams of the specific text, find them in the vocabulary list
    and return the list of index have been found.

    Args:
        vocab: Vocabulary list.
        text: Input text
        n: N-grams

    Returns:
        List of the index of n-grams in the vocabulary list.
        Returns -1 for n-grams not found in vocabulary.
    """
    wi = []

    if not isinstance(text, str):
        return wi

    a = zip(*[text[i:] for i in range(n)], strict=False)
    for i in a:
        w = "".join(i)
        try:
            idx = vocab.index(w)
        except ValueError:
            idx = -1  # Use -1 to indicate "not found"
        wi.append(idx)
    return wi
