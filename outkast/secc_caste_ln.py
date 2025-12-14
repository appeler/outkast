#!/usr/bin/env python

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import ClassVar, Self

import pandas as pd

from .utils import column_exists, fixup_columns

# Set up logging
logger = logging.getLogger(__name__)

def configure_logging(level: str = "WARNING") -> None:
    """Configure logging for the module."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def get_secc_data_path() -> Path:
    """Get the path to the SECC data file using modern importlib.resources."""
    with resources.as_file(
        resources.files(__package__)
        / "data"
        / "secc"
        / "secc_all_state_year_ln_outkast.csv.gz"
    ) as data_file:
        return data_file


SECC_COLS = ["n_sc", "n_st", "n_other", "prop_sc", "prop_st", "prop_other"]


@dataclass(slots=True)
class SeccCasteLnData:
    __df: ClassVar[pd.DataFrame | None] = None
    __state: ClassVar[str | None] = None
    __year: ClassVar[int | None] = None

    @classmethod
    def secc_caste(
        cls: type[Self],
        df: pd.DataFrame,
        namecol: str | int,
        state: str | None = None,
        year: int | None = None,
    ) -> pd.DataFrame:
        """Appends additional columns from SECC data to the input DataFrame
        based on the last name.

        Removes extra space. Checks if the name is the SECC data.
        If it is, outputs data from that row.

        Args:
            df (:obj:`DataFrame`): Pandas DataFrame containing the last name
                column.
            namecol (str or int): Column's name or location of the name in
                DataFrame.
            state (str): The state name of SECC data to be used.
                (default is None for all states)
            year (int): The year of SECC data to be used.
                (default is None for all years)

        Returns:
            DataFrame: Pandas DataFrame with additional columns:-
                'n_sc', 'n_st', 'n_other',
                'prop_sc', 'prop_st', 'prop_other' by last name

        """

        if namecol not in df.columns:
            logger.error(f"No column `{namecol}` in the DataFrame")
            return df

        # Work on a copy to avoid modifying the input DataFrame
        df_copy = df.copy()

        # Convert name column to string type to handle numeric values
        name_series = df_copy[namecol].astype(str).str.strip().str.lower()
        df_copy["__last_name"] = name_series

        if cls.__df is None or cls.__state != state or cls.__year != year:
            secc_data_path = get_secc_data_path()
            adf = pd.read_csv(
                secc_data_path,
                usecols=["state", "birth_year", "last_name", "n_sc", "n_st", "n_other"],
            )
            agg_dict = {"n_sc": "sum", "n_st": "sum", "n_other": "sum"}
            match (state, year):
                case (str(), int()):
                    adf = adf[(adf.state == state) & (adf.birth_year == year)].copy()
                    adf = adf.drop(columns=["birth_year", "state"])
                case (str(), None):
                    adf = (
                        adf.groupby(["state", "last_name"]).agg(agg_dict).reset_index()
                    )
                    adf = adf[adf.state == state].copy()
                    adf = adf.drop(columns=["state"])
                case (None, int()):
                    adf = (
                        adf.groupby(["birth_year", "last_name"])
                        .agg(agg_dict)
                        .reset_index()
                    )
                    adf = adf[adf.birth_year == year].copy()
                    adf = adf.drop(columns=["birth_year"])
                case (None, None):
                    adf = adf.groupby(["last_name"]).agg(agg_dict).reset_index()
            n = adf["n_sc"] + adf["n_st"] + adf["n_other"]
            adf["prop_sc"] = adf["n_sc"] / n
            adf["prop_st"] = adf["n_st"] / n
            adf["prop_other"] = adf["n_other"] / n
            cls.__df = adf
            cls.__df = cls.__df[["last_name"] + SECC_COLS]
            cls.__df.rename(columns={"last_name": "__last_name"}, inplace=True)
            cls.__state = state
            cls.__year = year

        rdf = pd.merge(df_copy, cls.__df, how="left", on="__last_name")
        rdf = rdf.drop(columns=["__last_name"])

        return rdf

    @staticmethod
    def list_states() -> list[str]:
        secc_data_path = get_secc_data_path()
        adf = pd.read_csv(secc_data_path, usecols=["state"])
        return list(adf.state.unique())


secc_caste = SeccCasteLnData.secc_caste


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Configure logging for CLI usage
    configure_logging("INFO")

    title = "Appends SECC 2011 data columns for sc, st, and other by last name"
    parser = argparse.ArgumentParser(description=title)
    parser.add_argument("input", default=None, help="Input file")
    parser.add_argument(
        "-l",
        "--last-name",
        required=True,
        help="Name or index location of column contains the last name",
    )
    parser.add_argument(
        "-s",
        "--state",
        default=None,
        choices=SeccCasteLnData.list_states(),
        help="State name of SECC data (default=all)",
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        default=None,
        help="Birth year in SECC data (default=all)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="secc-caste-output.csv",
        help="Output file with SECC data columns",
    )

    args = parser.parse_args(argv)

    logger.info(f"Arguments: {args}")

    if not args.last_name.isdigit():
        df = pd.read_csv(args.input)
    else:
        df = pd.read_csv(args.input, header=None)
        args.last_name = int(args.last_name)

    if not column_exists(df, args.last_name):
        return -1

    rdf = secc_caste(df, args.last_name, args.state, args.year)

    logger.info(f"Saving output to file: `{args.output}`")
    rdf.columns = fixup_columns(rdf.columns)
    rdf.to_csv(args.output, index=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
