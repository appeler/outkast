from __future__ import annotations

from typing import Any

import pandas as pd


def column_exists(df: pd.DataFrame, col: str | int) -> bool:
    """Check the column name exists in the DataFrame.

    Args:
        df: Pandas DataFrame.
        col: Column name.

    Returns:
        True if exists, False if not exists.
    """
    if col and (col not in df.columns):
        print(f"The specify column `{col}` not found in the input file")
        return False
    else:
        return True


def fixup_columns(cols: list[Any]) -> list[str]:
    """Replace index location column to name with `col` prefix

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


def find_ngrams(vocab: list[str], text: str, n: int) -> list[int]:
    """Find and return list of the index of n-grams in the vocabulary list.

    Generate the n-grams of the specific text, find them in the vocabulary list
    and return the list of index have been found.

    Args:
        vocab: Vocabulary list.
        text: Input text
        n: N-grams

    Returns:
        List of the index of n-grams in the vocabulary list.
    """
    wi = []

    if not isinstance(text, str):
        return wi

    a = zip(*[text[i:] for i in range(n)])
    for i in a:
        w = "".join(i)
        try:
            idx = vocab.index(w)
        except ValueError:
            idx = 0
        wi.append(idx)
    return wi
