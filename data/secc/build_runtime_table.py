"""Build the disclosure-limited SECC runtime lookup and its manifest."""

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
CONTEXTS = {
    "national": ["last_name"],
    "state": ["state", "last_name"],
    "birth_year": ["birth_year", "last_name"],
    "state_birth_year": ["state", "birth_year", "last_name"],
}


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
        output_dir: Package data directory receiving the runtime artifacts.
    """
    raw = pd.read_csv(  # pyright: ignore[reportCallIssue]
        source,
        usecols=[  # pyright: ignore[reportArgumentType]
            "state",
            "birth_year",
            "last_name",
            *COUNT_COLUMNS,
        ],
    )
    raw[COUNT_COLUMNS] = raw[COUNT_COLUMNS].astype("uint32")
    source_support = int(raw[COUNT_COLUMNS].sum(axis=1).sum())

    frames: list[pd.DataFrame] = []
    evidence: dict[str, dict[str, int | float]] = {}
    sensitivity: dict[str, dict[str, dict[str, int | float]]] = {
        str(threshold): {} for threshold in SENSITIVITY_THRESHOLDS
    }
    for context_level, keys in CONTEXTS.items():
        aggregated = (
            raw.groupby(keys, sort=True, observed=True)[COUNT_COLUMNS]
            .sum()
            .reset_index()
        )
        support = aggregated[COUNT_COLUMNS].sum(axis=1)
        keep = support >= MIN_CELL_SUPPORT
        retained = aggregated.loc[keep].copy()
        retained.insert(0, "context_level", context_level)
        retained["total_support"] = support.loc[keep].astype("uint32")
        if "state" not in retained:
            retained["state"] = pd.NA
        if "birth_year" not in retained:
            retained["birth_year"] = pd.NA
        frames.append(retained)
        evidence[context_level] = {
            "source_cells": int(len(aggregated)),
            "shipped_cells": int(keep.sum()),
            "cell_coverage": round(float(keep.mean()), 6),
            "support_coverage": round(
                float(support.loc[keep].sum() / support.sum()), 6
            ),
        }
        for threshold in SENSITIVITY_THRESHOLDS:
            threshold_keep = support >= threshold
            sensitivity[str(threshold)][context_level] = {
                "shipped_cells": int(threshold_keep.sum()),
                "cell_coverage": round(float(threshold_keep.mean()), 6),
                "support_coverage": round(
                    float(support.loc[threshold_keep].sum() / support.sum()), 6
                ),
            }

    runtime = pd.concat(frames, ignore_index=True)[
        [
            "context_level",
            "state",
            "birth_year",
            "last_name",
            *COUNT_COLUMNS,
            "total_support",
        ]
    ]
    runtime = runtime.sort_values(  # pyright: ignore[reportCallIssue]
        ["context_level", "state", "birth_year", "last_name"],
        na_position="first",
        ignore_index=True,
    )

    schema = pa.schema(
        [
            pa.field(
                "context_level",
                pa.dictionary(pa.int8(), pa.string()),
                nullable=False,
            ),
            pa.field("state", pa.dictionary(pa.int8(), pa.string())),
            pa.field("birth_year", pa.int16()),
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

    states = sorted(raw["state"].unique().tolist())
    years = sorted(int(value) for value in raw["birth_year"].unique())
    national_names = runtime.loc[
        runtime["context_level"] == "national", "last_name"
    ].sort_values()
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
            "rule": "Every shipped contextual cell has total_support >= minimum_cell_support.",
            "aggregation_note": (
                "Each context level is aggregated from the source independently before "
                "suppression; broader cells are not sums of shipped detailed cells."
            ),
            "coverage_evidence": evidence,
            "threshold_sensitivity": sensitivity,
        },
        "provenance": {
            "reference_dataset": "Socio-Economic and Caste Census 2011 parsed data",
            "reference_url": "https://doi.org/10.7910/DVN/LIIBNB",
            "source_artifact": SOURCE_NAME,
            "source_sha256": sha256(source),
            "source_repository_commit": "7cb6f32c3e42090e8da48fe8af321eccf44e02a4",
            "reference_population_note": (
                "Counts describe records retained in the historical Outkast SECC source "
                "after its documented name and birth-year filters; they are not population "
                "estimates and do not describe an individual."
            ),
            "source_total_support": source_support,
        },
        "shipped_universe": {
            "context_levels": evidence,
            "states": states,
            "birth_years": years,
            "national_surnames": {
                "count": int(len(national_names)),
                "sorted_utf8_sha256": hashlib.sha256(
                    "\n".join(national_names).encode()
                ).hexdigest(),
            },
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
    package_data = repository / "outkast" / "data" / "secc"
    build(args.source, package_data)
