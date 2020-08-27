outkast: estimate caste by last name, year, and state
-----------------------------------------------------

.. image:: https://travis-ci.org/appeler/outkast.svg?branch=master
    :target: https://travis-ci.org/appeler/outkast
.. image:: https://ci.appveyor.com/api/projects/status/uh8be9gytjo88d6f/branch/master?svg=true
    :target: https://ci.appveyor.com/project/appeler/outkast
.. image:: https://img.shields.io/pypi/v/outkast.svg
    :target: https://pypi.python.org/pypi/outkast
.. image:: https://pepy.tech/badge/outkast
    :target: https://pepy.tech/project/outkast


Using data on more than 140M Indians across 19 states from the `Socio-Economic Caste Census <https://github.com/in-rolls/secc>`__ (parsed data `here <https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LIIBNB>`__), we estimate the proportion `scheduled caste, scheduled tribe, and other` for a particular last name, year, and state.

Why?
====

We provide this package so that people can assess, highlight, and fight unfairness.

How is the underlying data produced?
====================================

1. The `script <outkast/data/secc/01_download_secc.ipynb>`__ downloads the `clean version <https://github.com/in-rolls/secc>`__ of the SECC posted `here <https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LIIBNB>`__.

2. `Infer the last name <outkast/data/secc/02_clean_secc_recode.ipynb>`__

  * remove names with non-alphabetical characters
  * remove records with missing last names
  * remove < 2 char last names
  * remove rows with birth_date < 1900
  * last name shared by at least 1000

3. `Group by last name, state, and year <outkast/data/secc/03_outkast_dataset_state.ipynb>`__ and produce the `underlying data <outkast/data/secc/secc_all_state_year_ln_outkast.csv.gz>`__

Base Classifier
~~~~~~~~~~~~~~~

We start by providing a base model for last\_name that gives the Bayes
optimal solution providing the proportion of `SC, ST, and Other` with that last name.
We also provide a series of base models where the state of
residence is known.

Installation
~~~~~~~~~~~~

We strongly recommend installing `outkast` inside a Python virtual environment (see `venv documentation <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`__)

::

    pip install outkast


Usage
~~~~~

::

    usage: secc_caste [-h] -l LAST_NAME
                    [-s {arunachal pradesh,assam,bihar,chhattisgarh,gujarat,haryana,kerala,madhya pradesh,maharashtra,mizoram,odisha,nagaland,punjab,rajasthan,sikkim,tamilnadu,uttar pradesh,uttarakhand,west bengal}]
                    [-y YEAR] [-o OUTPUT]
                    input

    Appends SECC 2011 data columns for sc, st, and other by last name

    positional arguments:
    input                 Input file

    optional arguments:
    -h, --help            show this help message and exit
    -l LAST_NAME, --last-name LAST_NAME
                            Name or index location of column contains the last
                            name
    -s {arunachal pradesh,assam,bihar,chhattisgarh,gujarat,haryana,kerala,madhya pradesh,maharashtra,mizoram,odisha,nagaland,punjab,rajasthan,sikkim,tamilnadu,uttar pradesh,uttarakhand,west bengal}, --state {arunachal pradesh,assam,bihar,chhattisgarh,gujarat,haryana,kerala,madhya pradesh,maharashtra,mizoram,odisha,nagaland,punjab,rajasthan,sikkim,tamilnadu,uttar pradesh,uttarakhand,west bengal}
                            State name of SECC data (default=all)
    -y YEAR, --year YEAR  Birth year in SECC data (default=all)
    -o OUTPUT, --output OUTPUT
                            Output file with SECC data columns



Using outkast
~~~~~~~~~~~~~

::

    >>> import pandas as pd
    >>> from outkast import secc_caste
    >>>
    >>> names = [{'name': 'patel'},
    ...             {'name': 'zala'},
    ...             {'name': 'lal'},
    ...             {'name': 'agarwal'}]
    >>>
    >>> df = pd.DataFrame(names)
    >>>
    >>> secc_caste(df, 'name')
        name    n_sc    n_st  n_other   prop_sc   prop_st  prop_other
    0    patel    5681  112302   631393  0.007581  0.149861    0.842558
    1     zala     667      14    34550  0.018932  0.000397    0.980670
    2      lal  703595  241846  1314224  0.311371  0.107027    0.581601
    3  agarwal      39      12     4375  0.008812  0.002711    0.988477


    >>>
    >>> help(secc_caste)
    Help on method secc_caste in module outkast.secc_caste_ln:

    secc_caste(df, namecol, state=None, year=None) method of builtins.type instance
        Appends additional columns from SECC data to the input DataFrame
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


Authors
~~~~~~~

Suriyan Laohaprapanon and Gaurav Sood

License
~~~~~~~

The package is released under the `MIT
License <https://opensource.org/licenses/MIT>`__.
