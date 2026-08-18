"""Disclosure-limited aggregate composition lookups from SECC surname groups."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from importlib import resources
from typing import Any, Final

import pandas as pd

ARTIFACT_NAME: Final = "secc_surname_composition.parquet"
MANIFEST_NAME: Final = "secc_surname_composition.manifest.json"
EXPECTED_MANIFEST_SHA256: Final = (
    "2e462d523f08b2e431a70147dad37c0eb688b6dff7db7e8396a560238496960d"
)

COUNT_COLUMNS: Final = ("n_sc", "n_st", "n_other")
OUTPUT_COLUMNS: Final = (
    "secc_count_sc",
    "secc_count_st",
    "secc_count_other",
    "secc_total_support",
    "secc_proportion_sc",
    "secc_proportion_st",
    "secc_proportion_other",
    "secc_lookup_status",
    "secc_abstention_reason",
)

_runtime_table: pd.DataFrame | None = None
_manifest: dict[str, Any] | None = None


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_runtime_data() -> tuple[pd.DataFrame, dict[str, Any]]:
    global _manifest, _runtime_table
    if _runtime_table is not None and _manifest is not None:
        return _runtime_table, _manifest

    data_root = resources.files("outkast") / "data" / "secc"
    manifest_bytes = (data_root / MANIFEST_NAME).read_bytes()
    if _sha256_bytes(manifest_bytes) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("The packaged SECC data manifest failed its integrity check")
    manifest = json.loads(manifest_bytes)

    artifact_bytes = (data_root / ARTIFACT_NAME).read_bytes()
    if _sha256_bytes(artifact_bytes) != manifest["artifact"]["sha256"]:
        raise RuntimeError("The packaged SECC runtime table failed its integrity check")
    with (data_root / ARTIFACT_NAME).open("rb") as stream:
        table = pd.read_parquet(stream, engine="pyarrow", dtype_backend="pyarrow")

    expected_columns = [
        "state",
        "birth_year",
        "last_name",
        *COUNT_COLUMNS,
        "total_support",
    ]
    if list(table.columns) != expected_columns:
        raise RuntimeError("The packaged SECC runtime table has an invalid schema")
    if len(table) != manifest["artifact"]["rows"]:
        raise RuntimeError("The packaged SECC runtime table has an invalid row count")
    if table.duplicated(["state", "birth_year", "last_name"]).any():
        raise RuntimeError("The packaged SECC runtime table has duplicate cells")
    if bool(table[["state", "birth_year", "last_name"]].isna().to_numpy().any()):
        raise RuntimeError("The packaged SECC runtime table has incomplete cell keys")
    support = table[list(COUNT_COLUMNS)].sum(axis=1)
    minimum = manifest["disclosure_policy"]["minimum_cell_support"]
    if bool((support != table["total_support"]).any()) or bool(
        (support < minimum).any()
    ):
        raise RuntimeError(
            "The packaged SECC runtime table violates its support policy"
        )

    _runtime_table = table
    _manifest = manifest
    return table, manifest


def get_secc_data_manifest() -> dict[str, Any]:
    """Return a copy of the immutable packaged-data manifest."""
    _, manifest = _load_runtime_data()
    return deepcopy(manifest)


def list_supported_states() -> tuple[str, ...]:
    """Return states in the packaged SECC reference universe."""
    _, manifest = _load_runtime_data()
    return tuple(manifest["shipped_universe"]["states"])


def _validate_call(
    frame: pd.DataFrame,
    surname_column: str | int,
    state: str,
    birth_year: int,
) -> tuple[str, int]:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    if not frame.columns.is_unique:
        raise ValueError("frame must have unique column labels")
    if not isinstance(surname_column, (str, int)) or isinstance(surname_column, bool):
        raise TypeError("surname_column must be a string or integer column label")
    if surname_column not in frame.columns:
        raise KeyError(f"surname column {surname_column!r} is not in frame")
    collisions = sorted(set(frame.columns).intersection(OUTPUT_COLUMNS), key=str)
    if collisions:
        joined = ", ".join(repr(column) for column in collisions)
        raise ValueError(f"frame already contains result column(s): {joined}")

    if not isinstance(state, str):
        raise TypeError("state must be a string")
    normalized_state = state.strip().casefold()
    if not normalized_state:
        raise ValueError("state must not be empty")
    if not isinstance(birth_year, int) or isinstance(birth_year, bool):
        raise TypeError("birth_year must be an integer")
    return normalized_state, birth_year


def _normalize_surname(value: object) -> tuple[str | None, str | None]:
    if value is None or value is pd.NA:
        return None, "missing_name"
    try:
        if bool(pd.isna(value)):
            return None, "missing_name"
    except (TypeError, ValueError):
        return None, "out_of_vocabulary"
    if not isinstance(value, str):
        return None, "out_of_vocabulary"
    normalized = value.strip().casefold()
    if not normalized:
        return None, "missing_name"
    if any(character.isalpha() and not character.isascii() for character in normalized):
        return None, "unsupported_script"
    if not normalized.isascii() or not normalized.isalpha():
        return None, "out_of_vocabulary"
    return normalized, None


def lookup_secc_caste_composition(
    frame: pd.DataFrame,
    surname_column: str | int,
    *,
    state: str,
    birth_year: int,
) -> pd.DataFrame:
    """Append deterministic SECC surname-group composition to a DataFrame.

    The returned counts describe a reference-data group. They are not an
    individual's caste and must not be used as individual labels. Cells with
    fewer than the manifest's minimum support are absent from the package.

    Args:
        frame: Input observations. The input object is not modified.
        surname_column: Unique column label containing surnames.
        state: Required SECC state context. Matching ignores case and outer space.
        birth_year: Required SECC birth-year context.

    Returns:
        A copy of ``frame`` with counts, total support, group proportions, lookup
        status, and abstention reason appended. Row count, order, and index are
        preserved.

    Raises:
        TypeError: If an argument has the wrong type.
        ValueError: If columns are duplicated, output columns collide, or state
            is empty.
        KeyError: If ``surname_column`` is not present in ``frame``.
        RuntimeError: If the packaged table contains duplicate surnames in the
            requested context.

    """  # noqa: DOC503
    normalized_state, birth_year = _validate_call(
        frame, surname_column, state, birth_year
    )
    table, manifest = _load_runtime_data()
    context = table.loc[
        (table["state"] == normalized_state) & (table["birth_year"] == birth_year)
    ]

    supported_states = manifest["shipped_universe"]["states"]
    supported_years = manifest["shipped_universe"]["birth_years"]
    unsupported_context = normalized_state not in supported_states or (
        birth_year not in supported_years
    )

    normalized_and_reasons = [
        _normalize_surname(value) for value in frame[surname_column].array
    ]
    normalized = pd.Series(
        (item[0] for item in normalized_and_reasons),
        index=frame.index,
        dtype="string",
    )
    input_reasons = [item[1] for item in normalized_and_reasons]

    result = frame.copy()
    result_length = len(result)
    if unsupported_context:
        for column in OUTPUT_COLUMNS[:4]:
            result[column] = pd.array([pd.NA] * result_length, dtype="UInt64")
        for column in OUTPUT_COLUMNS[4:7]:
            result[column] = pd.array([pd.NA] * result_length, dtype="Float64")
        result["secc_lookup_status"] = pd.array(
            ["abstained"] * result_length, dtype="string"
        )
        result["secc_abstention_reason"] = pd.array(
            ["unsupported_context"] * result_length, dtype="string"
        )
        return result

    lookup = context.set_index("last_name")
    if not lookup.index.is_unique:
        raise RuntimeError("The packaged SECC runtime table has duplicate surnames")
    national_names = frozenset(manifest["shipped_universe"]["known_surnames"])
    matched = normalized.isin(lookup.index)

    source_to_output = {
        "n_sc": "secc_count_sc",
        "n_st": "secc_count_st",
        "n_other": "secc_count_other",
        "total_support": "secc_total_support",
    }
    for source, output in source_to_output.items():
        result[output] = pd.array(normalized.map(lookup[source]), dtype="UInt64")
    for category in ("sc", "st", "other"):
        result[f"secc_proportion_{category}"] = pd.array(
            result[f"secc_count_{category}"] / result["secc_total_support"],
            dtype="Float64",
        )

    reasons: list[str | None] = []
    for name, input_reason, is_matched in zip(
        normalized.array, input_reasons, matched.array, strict=True
    ):
        if is_matched:
            reasons.append(None)
        elif input_reason is not None:
            reasons.append(input_reason)
        elif name in national_names:
            reasons.append("insufficient_support")
        else:
            reasons.append("out_of_vocabulary")
    result["secc_lookup_status"] = pd.array(
        ["matched" if value else "abstained" for value in matched], dtype="string"
    )
    result["secc_abstention_reason"] = pd.array(reasons, dtype="string")
    return result


def main(argv: list[str] | None = None) -> int:
    """Run the disclosure-limited SECC composition lookup CLI."""
    parser = argparse.ArgumentParser(
        description="Append SECC surname-group composition; never individual labels."
    )
    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("--surname-column", required=True, help="Surname column label")
    parser.add_argument("--state", required=True, choices=list_supported_states())
    parser.add_argument("--birth-year", required=True, type=int)
    parser.add_argument("--output", default="secc-composition-output.csv")
    args = parser.parse_args(argv)

    frame = pd.read_csv(args.input)
    result = lookup_secc_caste_composition(
        frame,
        args.surname_column,
        state=args.state,
        birth_year=args.birth_year,
    )
    result.to_csv(args.output, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
