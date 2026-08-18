"""Build the single-hierarchy SECC runtime lookup and its manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

MIN_CELL_SUPPORT = 100
SENSITIVITY_THRESHOLDS = (20, 50, 100, 200)
SOURCE_NAME = "secc_all_state_year_ln_outkast.csv.gz"
OUTPUT_NAME = "secc_surname_composition.parquet"
MANIFEST_NAME = "secc_surname_composition.manifest.json"
COUNT_COLUMNS = ["n_sc", "n_st", "n_other"]
CELL_KEYS = ["state", "birth_year", "last_name"]


def sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(source: Path, output_dir: Path) -> None:
    """Build the runtime table and manifest from the historical source table.

    Args:
        source: Historical full-resolution gzip-compressed CSV.
        output_dir: Directory receiving the runtime artifacts.
    """
    raw = pd.read_csv(  # pyright: ignore[reportCallIssue]
        source,
        usecols=[  # pyright: ignore[reportArgumentType]
            *CELL_KEYS,
            *COUNT_COLUMNS,
        ],
    )
    raw[COUNT_COLUMNS] = raw[COUNT_COLUMNS].astype("uint32")
    cells = (
        raw.groupby(CELL_KEYS, sort=True, observed=True)[COUNT_COLUMNS]
        .sum()
        .reset_index()
    )
    support = cells[COUNT_COLUMNS].sum(axis=1)
    keep = support >= MIN_CELL_SUPPORT
    runtime = cells.loc[keep].copy()
    runtime["total_support"] = support.loc[keep].astype("uint32")
    runtime = runtime.sort_values(  # pyright: ignore[reportCallIssue]
        CELL_KEYS, ignore_index=True
    )

    schema = pa.schema(
        [
            pa.field("state", pa.dictionary(pa.int8(), pa.string()), nullable=False),
            pa.field("birth_year", pa.int16(), nullable=False),
            pa.field("last_name", pa.string(), nullable=False),
            pa.field("n_sc", pa.uint32(), nullable=False),
            pa.field("n_st", pa.uint32(), nullable=False),
            pa.field("n_other", pa.uint32(), nullable=False),
            pa.field("total_support", pa.uint32(), nullable=False),
        ]
    )
    table = pa.Table.from_pandas(runtime, schema=schema, preserve_index=False)
    output = output_dir / OUTPUT_NAME
    pq.write_table(
        table,
        output,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
    )

    sensitivity: dict[str, dict[str, int | float]] = {}
    for threshold in SENSITIVITY_THRESHOLDS:
        threshold_keep = support >= threshold
        sensitivity[str(threshold)] = {
            "shipped_cells": int(threshold_keep.sum()),
            "cell_coverage": round(float(threshold_keep.mean()), 4),
            "support_coverage": round(
                float(support.loc[threshold_keep].sum() / support.sum()), 4
            ),
        }

    national = (
        raw.groupby("last_name", sort=True, observed=True)[COUNT_COLUMNS]
        .sum()
        .sum(axis=1)
    )
    known_surnames = national.index.tolist()
    evidence = {
        "source_cells": int(len(cells)),
        "shipped_cells": int(keep.sum()),
        "cell_coverage": round(float(keep.mean()), 4),
        "support_coverage": round(float(support.loc[keep].sum() / support.sum()), 4),
        "rounding_note": (
            "Coverage ratios are rounded to four decimal places. The manifest does "
            "not release exact source or suppressed support totals."
        ),
    }
    manifest = {
        "artifact": {
            "filename": OUTPUT_NAME,
            "sha256": sha256(output),
            "rows": len(runtime),
            "schema": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                }
                for field in schema
            ],
        },
        "disclosure_policy": {
            "minimum_cell_support": MIN_CELL_SUPPORT,
            "rule": "Every shipped state-birth-year-surname cell has total_support >= minimum_cell_support.",
            "release_design": {
                "cell_keys": CELL_KEYS,
                "released_hierarchies": ["state_birth_year_surname"],
                "parent_aggregates_released": False,
                "complementary_differencing_note": (
                    "The artifact releases one fixed-granularity hierarchy. It does "
                    "not release national, state-only, birth-year-only, or other "
                    "parent totals that could expose a suppressed cell by subtraction."
                ),
            },
            "coverage_evidence": evidence,
            "threshold_sensitivity": sensitivity,
        },
        "provenance": {
            "reference_dataset": "Socio-Economic and Caste Census 2011 parsed data",
            "reference_url": "https://doi.org/10.7910/DVN/LIIBNB",
            "source_artifact": SOURCE_NAME,
            "source_repository_commit": "7cb6f32c3e42090e8da48fe8af321eccf44e02a4",
            "reference_population_note": (
                "Counts describe records retained in the historical Outkast SECC source "
                "after its documented name and birth-year filters; they are not population "
                "estimates and do not describe an individual."
            ),
        },
        "shipped_universe": {
            "states": sorted(runtime["state"].unique().tolist()),
            "birth_years": sorted(
                int(value) for value in runtime["birth_year"].unique()
            ),
            "known_surnames": known_surnames,
            "known_surnames_note": (
                "This vocabulary contains no counts. It supports the distinction between "
                "out-of-vocabulary names and cells withheld for insufficient support."
            ),
            "known_surnames_sorted_utf8_sha256": hashlib.sha256(
                "\n".join(known_surnames).encode()
            ).hexdigest(),
        },
    }
    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        type=Path,
        help=f"Path to the historical {SOURCE_NAME} source artifact",
    )
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    package_data = repository / "src" / "outkast" / "data" / "secc"
    build(args.source, package_data)
