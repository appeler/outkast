#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import pandas as pd

from pkg_resources import resource_filename

from .utils import column_exists, fixup_columns

SECC_DATA = resource_filename(__name__, "data/secc/secc_all_state_year_ln_outkast.csv.gz")
SECC_COLS = ['n_sc', 'n_st', 'n_other', 'prop_sc', 'prop_st', 'prop_other']


class SeccCasteLnData():
    __df = None
    __state = None
    __year = None

    @classmethod
    def secc_caste(cls, df, namecol, state=None, year=None):
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
            print("No column `{0!s}` in the DataFrame".format(namecol))
            return df

        df['__last_name'] = df[namecol].str.strip()
        df['__last_name'] = df['__last_name'].str.lower()

        if cls.__df is None or cls.__state != state or cls.__year != year:
            adf = pd.read_csv(SECC_DATA, usecols=['state', 'birth_year',
                              'last_name', 'n_sc', 'n_st', 'n_other'])
            agg_dict = {'n_sc': 'sum', 'n_st': 'sum', 'n_other': 'sum'}
            if state and year:
                adf = adf[(adf.state==state) & (adf.birth_year==year)].copy()
                del adf['birth_year']
                del adf['state']
            elif state:
                adf = adf.groupby(['state', 'last_name']).agg(agg_dict).reset_index()
                adf = adf[adf.state==state].copy()
                del adf['state']
            elif year:
                adf = adf.groupby(['birth_year', 'last_name']).agg(agg_dict).reset_index()
                adf = adf[adf.birth_year==year].copy()
                del adf['birth_year']
            else:
                adf = adf.groupby(['last_name']).agg(agg_dict).reset_index()
            n = adf['n_sc'] + adf['n_st'] + adf['n_other']
            adf['prop_sc'] = adf['n_sc'] / n
            adf['prop_st'] = adf['n_st'] / n
            adf['prop_other'] = adf['n_other'] / n
            cls.__df = adf
            cls.__df = cls.__df[['last_name'] + SECC_COLS]
            cls.__df.rename(columns={'last_name': '__last_name'}, inplace=True)
        rdf = pd.merge(df, cls.__df, how='left', on='__last_name')

        del rdf['__last_name']

        return rdf

    @staticmethod
    def list_states():
        adf = pd.read_csv(SECC_DATA, usecols=['state'])
        return adf.state.unique()


secc_caste = SeccCasteLnData.secc_caste


def main(argv=sys.argv[1:]):
    title = ('Appends SECC 2011 data columns for sc, st, and other by last name')
    parser = argparse.ArgumentParser(description=title)
    parser.add_argument('input', default=None,
                        help='Input file')
    parser.add_argument('-l', '--last-name', required=True,
                        help='Name or index location of column contains '
                             'the last name')
    parser.add_argument('-s', '--state', default=None,
                        choices=SeccCasteLnData.list_states(),
                        help='State name of SECC data '
                             '(default=all)')
    parser.add_argument('-y', '--year', type=int, default=None,
                        help='Birth year in SECC data (default=all)')
    parser.add_argument('-o', '--output', default='secc-caste-output.csv',
                        help='Output file with SECC data columns')

    args = parser.parse_args(argv)

    print(args)

    if not args.last_name.isdigit():
        df = pd.read_csv(args.input)
    else:
        df = pd.read_csv(args.input, header=None)
        args.last_name = int(args.last_name)

    if not column_exists(df, args.last_name):
        return -1

    rdf = secc_caste(df, args.last_name, args.state, args.year)

    print("Saving output to file: `{0:s}`".format(args.output))
    rdf.columns = fixup_columns(rdf.columns)
    rdf.to_csv(args.output, index=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
