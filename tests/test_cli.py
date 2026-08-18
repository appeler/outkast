"""Command-line tests for the aggregate lookup."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from outkast.secc_composition import main


def test_cli_writes_explicit_lookup_fields(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    pd.DataFrame({"surname": ["patel", "notintable"]}).to_csv(source, index=False)

    status = main(
        [
            str(source),
            "--surname-column",
            "surname",
            "--output",
            str(output),
        ]
    )

    result = pd.read_csv(output)
    assert status == 0
    assert result["secc_lookup_status"].tolist() == ["matched", "abstained"]
    assert result.iloc[1]["secc_abstention_reason"] == "out_of_vocabulary"


def test_cli_rejects_unknown_state(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    pd.DataFrame({"surname": ["patel"]}).to_csv(source, index=False)

    with pytest.raises(SystemExit):
        main([str(source), "--surname-column", "surname", "--state", "unknown"])
