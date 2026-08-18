"""Behavior tests for the public aggregate lookup."""

from __future__ import annotations

import pandas as pd
import pytest

from outkast import lookup_secc_caste_composition
from outkast.secc_composition import OUTPUT_COLUMNS


def test_contextual_lookup_preserves_rows_index_and_input() -> None:
    frame = pd.DataFrame(
        {"surname": ["PATEL", "  lal ", "notintable"]}, index=[7, 7, 2]
    )
    original = frame.copy()

    result = lookup_secc_caste_composition(
        frame, "surname", state="bihar", birth_year=1949
    )

    pd.testing.assert_frame_equal(frame, original)
    assert result.index.tolist() == [7, 7, 2]
    assert len(result) == len(frame)
    assert result["secc_lookup_status"].tolist() == [
        "matched",
        "matched",
        "abstained",
    ]
    assert result["secc_abstention_reason"].tolist()[:2] == [pd.NA, pd.NA]
    assert result.iloc[2]["secc_abstention_reason"] == "out_of_vocabulary"
    assert result.iloc[0]["secc_total_support"] == 1_605
    assert result.iloc[0]["secc_total_support"] == sum(
        result.iloc[0][column]
        for column in ("secc_count_sc", "secc_count_st", "secc_count_other")
    )
    assert sum(
        result.iloc[0][column]
        for column in (
            "secc_proportion_sc",
            "secc_proportion_st",
            "secc_proportion_other",
        )
    ) == pytest.approx(1.0)


def test_explicit_abstention_reasons() -> None:
    frame = pd.DataFrame({"surname": [None, "   ", "पटेल", "notintable", "aade", 123]})

    result = lookup_secc_caste_composition(
        frame, "surname", state="kerala", birth_year=1985
    )

    assert result["secc_lookup_status"].tolist() == ["abstained"] * 6
    assert result["secc_abstention_reason"].tolist() == [
        "missing_name",
        "missing_name",
        "unsupported_script",
        "out_of_vocabulary",
        "insufficient_support",
        "out_of_vocabulary",
    ]
    assert result["secc_total_support"].isna().all()


def test_unsupported_context_is_explicit() -> None:
    frame = pd.DataFrame({"surname": ["patel", None]})

    result = lookup_secc_caste_composition(
        frame, "surname", state="not a state", birth_year=2200
    )

    assert result["secc_lookup_status"].tolist() == ["abstained", "abstained"]
    assert result["secc_abstention_reason"].tolist() == [
        "unsupported_context",
        "unsupported_context",
    ]


def test_supported_but_fully_suppressed_context_is_insufficient_support() -> None:
    result = lookup_secc_caste_composition(
        pd.DataFrame({"surname": ["patel"]}),
        "surname",
        state="kerala",
        birth_year=1985,
    )

    assert result.iloc[0]["secc_abstention_reason"] == "insufficient_support"


def test_detailed_context_can_match_at_disclosure_floor() -> None:
    result = lookup_secc_caste_composition(
        pd.DataFrame({"surname": ["patel"]}),
        "surname",
        state=" Bihar ",
        birth_year=1949,
    )

    assert result.iloc[0]["secc_lookup_status"] == "matched"
    assert result.iloc[0]["secc_total_support"] == 1_605


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"state": 1}, TypeError),
        ({"state": "  "}, ValueError),
        ({"birth_year": "1985"}, TypeError),
        ({"birth_year": True}, TypeError),
    ],
)
def test_context_argument_validation(
    kwargs: dict[str, object], error: type[Exception]
) -> None:
    arguments = {"state": "bihar", "birth_year": 1949, **kwargs}
    with pytest.raises(error):
        lookup_secc_caste_composition(
            pd.DataFrame({"surname": ["patel"]}), "surname", **arguments
        )


def test_state_and_birth_year_are_mandatory() -> None:
    frame = pd.DataFrame({"surname": ["patel"]})
    with pytest.raises(TypeError):
        lookup_secc_caste_composition(frame, "surname")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        lookup_secc_caste_composition(  # type: ignore[call-arg]
            frame, "surname", state="bihar"
        )


def test_frame_and_column_validation() -> None:
    frame = pd.DataFrame({"surname": ["patel"]})
    with pytest.raises(TypeError):
        lookup_secc_caste_composition(  # type: ignore[arg-type]
            [], "surname", state="bihar", birth_year=1949
        )
    with pytest.raises(KeyError):
        lookup_secc_caste_composition(frame, "missing", state="bihar", birth_year=1949)
    with pytest.raises(TypeError):
        lookup_secc_caste_composition(  # type: ignore[arg-type]
            frame, True, state="bihar", birth_year=1949
        )

    duplicated = pd.DataFrame([["patel", "lal"]], columns=["surname", "surname"])
    with pytest.raises(ValueError, match="unique column labels"):
        lookup_secc_caste_composition(
            duplicated, "surname", state="bihar", birth_year=1949
        )


@pytest.mark.parametrize("collision", OUTPUT_COLUMNS)
def test_result_column_collisions_raise(collision: str) -> None:
    frame = pd.DataFrame({"surname": ["patel"], collision: [None]})
    with pytest.raises(ValueError, match="already contains"):
        lookup_secc_caste_composition(frame, "surname", state="bihar", birth_year=1949)


def test_empty_frame_has_complete_typed_schema() -> None:
    result = lookup_secc_caste_composition(
        pd.DataFrame({"surname": []}),
        "surname",
        state="bihar",
        birth_year=1949,
    )

    assert len(result) == 0
    assert tuple(result.columns[-len(OUTPUT_COLUMNS) :]) == OUTPUT_COLUMNS
    assert str(result["secc_total_support"].dtype) == "UInt64"
    assert str(result["secc_proportion_sc"].dtype) == "Float64"
    assert str(result["secc_lookup_status"].dtype) == "string"
