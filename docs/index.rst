Outkast Documentation
=====================

Outkast is a Python library for inferring caste from Indian names using SECC 2011 data.

Installation
------------

Install outkast using pip:

.. code-block:: bash

    pip install outkast

Requirements
~~~~~~~~~~~~

- Python 3.11 or higher
- pandas
- numpy

Quick Start
-----------

Here's a simple example of how to use outkast:

.. code-block:: python

    import pandas as pd
    from outkast import secc_caste
    
    # Create a DataFrame with names
    df = pd.DataFrame({'name': ['Patel', 'Sharma', 'Singh', 'Kumar']})
    
    # Add caste predictions
    result = secc_caste(df, 'name')
    print(result)

The function will add columns with caste proportions:

- ``n_sc``: Number of Scheduled Caste individuals
- ``n_st``: Number of Scheduled Tribe individuals  
- ``n_other``: Number of Other individuals
- ``prop_sc``: Proportion of Scheduled Caste
- ``prop_st``: Proportion of Scheduled Tribe
- ``prop_other``: Proportion of Other

API Reference
-------------

.. automodule:: outkast
    :members:
    :undoc-members:
    :show-inheritance:

Main Functions
~~~~~~~~~~~~~~

.. autofunction:: outkast.secc_caste

Core Classes
~~~~~~~~~~~~

.. autoclass:: outkast.secc_caste_ln.SeccCasteLnData
    :members:
    :undoc-members:
    :show-inheritance:

Utility Functions
~~~~~~~~~~~~~~~~~

.. automodule:: outkast.utils
    :members:
    :undoc-members:
    :show-inheritance:

Command Line Interface
----------------------

Outkast also provides a command-line interface:

.. code-block:: bash

    secc_caste input.csv -l name_column -o output.csv

Options:

- ``-l, --last-name``: Name or index of the column containing last names (required)
- ``-s, --state``: Filter by specific state (optional)
- ``-y, --year``: Filter by birth year (optional)  
- ``-o, --output``: Output file name (default: secc-caste-output.csv)

Data Source
-----------

The predictions are based on the Socio Economic and Caste Census (SECC) 2011 data,
which provides comprehensive demographic information about Indian households.

Contributing
------------

Contributions are welcome! Please feel free to submit a Pull Request.

License
-------

This project is licensed under the MIT License.

Changelog
---------

Version 1.0.0
~~~~~~~~~~~~~~

- **Breaking Change**: Dropped support for Python < 3.11
- Modernized codebase with type hints and modern Python features
- Replaced deprecated ``pkg_resources`` with ``importlib.resources``
- Updated to modern packaging with ``pyproject.toml``
- Added comprehensive type annotations
- Used f-strings throughout
- Added match/case statements for cleaner conditional logic

Version 0.2.1
~~~~~~~~~~~~~~

- Previous stable release with Python 3.5+ support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`