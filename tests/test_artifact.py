"""Integrity and disclosure tests for packaged SECC data."""

from __future__ import annotations

import hashlib
import json
from importlib import resources

import pandas as pd

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
    assert not table.duplicated(
        ["context_level", "state", "birth_year", "last_name"]
    ).any()


def test_manifest_records_real_coverage_floor_and_universe() -> None:
    manifest = get_secc_data_manifest()
    evidence = manifest["disclosure_policy"]["coverage_evidence"]
    sensitivity = manifest["disclosure_policy"]["threshold_sensitivity"]

    assert min(item["support_coverage"] for item in evidence.values()) >= 0.83
    assert evidence["state_birth_year"]["support_coverage"] == 0.83448
    assert manifest["artifact"]["rows"] == sum(
        item["shipped_cells"] for item in evidence.values()
    )
    assert manifest["provenance"]["source_total_support"] == 93_366_763
    assert manifest["shipped_universe"]["national_surnames"]["count"] == 6_661
    assert len(list_supported_states()) == 19
    assert sensitivity["20"]["state_birth_year"]["support_coverage"] == 0.952232
    assert sensitivity["200"]["state_birth_year"]["support_coverage"] == 0.764403


def test_manifest_callers_cannot_mutate_cached_manifest() -> None:
    first = get_secc_data_manifest()
    first["artifact"]["rows"] = 0
    assert get_secc_data_manifest()["artifact"]["rows"] == 213_531
