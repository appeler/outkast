"""Integrity and disclosure tests for packaged SECC data."""

from __future__ import annotations

import hashlib
import json
from importlib import resources

import pandas as pd
import pytest

from data.secc.build_runtime_table import build
from outkast import get_secc_data_manifest, list_supported_states
from outkast.secc_composition import (
    ARTIFACT_NAME,
    EXPECTED_MANIFEST_SHA256,
    MANIFEST_NAME,
)


def test_manifest_and_artifact_hashes_are_immutable() -> None:
    data_root = resources.files("outkast") / "data" / "secc"
    manifest_bytes = (data_root / MANIFEST_NAME).read_bytes()
    manifest = json.loads(manifest_bytes)
    artifact_bytes = (data_root / ARTIFACT_NAME).read_bytes()

    assert hashlib.sha256(manifest_bytes).hexdigest() == EXPECTED_MANIFEST_SHA256
    assert hashlib.sha256(artifact_bytes).hexdigest() == manifest["artifact"]["sha256"]


def test_no_low_support_cell_is_shipped() -> None:
    data_root = resources.files("outkast") / "data" / "secc"
    with (data_root / ARTIFACT_NAME).open("rb") as stream:
        table = pd.read_parquet(stream)
    manifest = get_secc_data_manifest()
    minimum = manifest["disclosure_policy"]["minimum_cell_support"]

    assert minimum == 100
    assert table["total_support"].min() >= minimum
    assert (
        table[["n_sc", "n_st", "n_other"]].sum(axis=1) == table["total_support"]
    ).all()
    assert list(table.columns) == [
        "state",
        "birth_year",
        "last_name",
        "n_sc",
        "n_st",
        "n_other",
        "total_support",
    ]
    assert not table.duplicated(["state", "birth_year", "last_name"]).any()
    assert not table[["state", "birth_year", "last_name"]].isna().any().any()


def test_manifest_records_real_coverage_floor_and_universe() -> None:
    manifest = get_secc_data_manifest()
    evidence = manifest["disclosure_policy"]["coverage_evidence"]
    sensitivity = manifest["disclosure_policy"]["threshold_sensitivity"]

    assert evidence["support_coverage"] == 0.8345
    assert evidence["cell_coverage"] == 0.0751
    assert manifest["artifact"]["rows"] == evidence["shipped_cells"] == 101_822
    assert len(manifest["shipped_universe"]["known_surnames"]) == 6_661
    assert "source_total_support" not in manifest["provenance"]
    assert "source_sha256" not in manifest["provenance"]
    assert len(list_supported_states()) == 19
    assert sensitivity["20"]["support_coverage"] == 0.9522
    assert sensitivity["200"]["support_coverage"] == 0.7644


def test_release_has_no_parent_or_child_hierarchy_for_differencing() -> None:
    manifest = get_secc_data_manifest()
    design = manifest["disclosure_policy"]["release_design"]

    assert design["cell_keys"] == ["state", "birth_year", "last_name"]
    assert design["released_hierarchies"] == ["state_birth_year_surname"]
    assert design["parent_aggregates_released"] is False


def test_rounded_coverage_cannot_pinpoint_a_suppressed_cell() -> None:
    data_root = resources.files("outkast") / "data" / "secc"
    with (data_root / ARTIFACT_NAME).open("rb") as stream:
        table = pd.read_parquet(stream)
    manifest = get_secc_data_manifest()
    reported = manifest["disclosure_policy"]["coverage_evidence"]["support_coverage"]
    released_support = int(table["total_support"].sum())
    rounding_half_width = 0.00005
    smallest_compatible_source = released_support / (reported + rounding_half_width)
    largest_compatible_source = released_support / (reported - rounding_half_width)

    assert largest_compatible_source - smallest_compatible_source > 100


@pytest.fixture
def differencing_attack_source() -> pd.DataFrame:
    """Return cells that overlapping parent releases would expose by subtraction."""
    return pd.DataFrame(
        {
            "state": ["a", "a", "b", "a", "b", "b"],
            "birth_year": [2000, 2000, 2001, 2001, 2000, 2001],
            "last_name": ["patel", "lal", "patel", "patel", "patel", "lal"],
            "n_sc": [1, 2, 3, 100, 100, 100],
            "n_st": [2, 3, 4, 0, 0, 0],
            "n_other": [3, 4, 5, 0, 0, 0],
        }
    )


def test_every_suppressed_cell_is_nonidentifiable_from_release(
    tmp_path, differencing_attack_source: pd.DataFrame
) -> None:
    """Changing any suppressed cell leaves all released statistics unchanged."""
    source = tmp_path / "source.csv.gz"
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    differencing_attack_source.to_csv(source, index=False)
    build(source, baseline_dir)
    baseline = pd.read_parquet(baseline_dir / ARTIFACT_NAME)
    suppressed = differencing_attack_source[
        differencing_attack_source[["n_sc", "n_st", "n_other"]].sum(axis=1) < 100
    ]

    assert len(suppressed) == 3
    assert len(baseline) == 3
    for row_index in suppressed.index:
        alternative = differencing_attack_source.copy()
        alternative.loc[row_index, "n_sc"] += 1
        alternative_source = tmp_path / f"alternative-{row_index}.csv.gz"
        alternative_dir = tmp_path / f"alternative-{row_index}"
        alternative_dir.mkdir()
        alternative.to_csv(alternative_source, index=False)
        build(alternative_source, alternative_dir)
        released_alternative = pd.read_parquet(alternative_dir / ARTIFACT_NAME)
        alternative_manifest = json.loads(
            (alternative_dir / MANIFEST_NAME).read_text(encoding="utf-8")
        )

        pd.testing.assert_frame_equal(baseline, released_alternative)
        assert alternative_manifest["shipped_universe"]["known_surnames"] == [
            "lal",
            "patel",
        ]


def test_manifest_callers_cannot_mutate_cached_manifest() -> None:
    first = get_secc_data_manifest()
    first["artifact"]["rows"] = 0
    assert get_secc_data_manifest()["artifact"]["rows"] == 101_822
