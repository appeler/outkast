Outkast: disclosure-limited SECC composition lookup
===================================================

.. image:: https://github.com/appeler/outkast/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/appeler/outkast/actions/workflows/ci.yml
.. image:: https://img.shields.io/pypi/v/outkast.svg
   :target: https://pypi.org/project/outkast/
.. image:: https://img.shields.io/badge/docs-github.io-blue
   :target: https://appeler.github.io/outkast/

Outkast returns descriptive counts and proportions for surname groups in a
filtered extract of India's 2011 Socio-Economic and Caste Census (SECC). It is a
deterministic table lookup, not a classifier. A match describes a group in the
reference data. It does not identify or estimate an individual's caste.

Safety and scope
----------------

Do not use Outkast to label people, make decisions about people, or fill a
missing sensitive attribute. A surname may be shared across castes, regions,
languages, and religions. Group proportions cannot establish any individual's
membership. The reference data and historical preprocessing may contain
coverage, recording, and selection errors.

The package releases only state, birth year, and surname cells with at least
100 reference records. It does not release national, state-only, or
birth-year-only counts. A user therefore cannot recover a suppressed detailed
cell by subtracting released children from a released parent total. All rows in
the artifact have the same fixed granularity. This guarantee applies to current
distribution artifacts. It cannot revoke data from repository history or older
package releases.

Cell retention is low by design because the removed cells are small. Support
retention measures the share of about 93.4 million reference records
represented by released state, birth year, and surname cells. At the minimum
support of 100, the artifact retains 83.45% of record support and 7.51% of
source cells. These figures measure artifact coverage, not coverage of India's
population or of new input names. The manifest rounds coverage ratios to four
decimal places and does not release the exact source or suppressed support
totals.

The threshold sensitivity below reports support retention, not cell retention.
A floor of 100 suppresses 92.49% of source cells. A floor of 200 would lower
support retention below 80%.

=========  ================  ==============
Minimum    Support retained  Cells retained
=========  ================  ==============
20         95.22%            25.99%
50         89.53%            13.53%
100        83.45%            7.51%
200        76.44%            4.03%
=========  ================  ==============

The package exposes observed counts and proportions. It does not report
multinomial intervals. Such intervals would describe sampling variation under a
sampling model, but would not capture SECC coverage error, preprocessing error,
or the uncertainty in applying a group aggregate to a person.

Installation
------------

Install Outkast in a virtual environment:

.. code-block:: console

   pip install outkast

Python API
----------

``lookup_secc_caste_composition`` preserves the input row count, order, and
index. It raises on missing or duplicate input columns and on result-column
collisions. Every call requires both ``state`` and ``birth_year`` because the
package does not distribute broader aggregates.

.. code-block:: python

   import pandas as pd
   from outkast import lookup_secc_caste_composition

   people = pd.DataFrame({"surname": ["patel", "lal", None, "notintable"]})
   result = lookup_secc_caste_composition(
       people,
       "surname",
       state="bihar",
       birth_year=1949,
   )

``list_supported_states`` returns the states the table covers, and
``get_secc_data_manifest`` returns the manifest described below. Both are useful
before a lookup, because a state or birth year outside the shipped universe
abstains the whole frame with ``unsupported_context``.

The appended fields are:

* ``secc_count_sc``, ``secc_count_st``, and ``secc_count_other``
* ``secc_total_support``
* ``secc_proportion_sc``, ``secc_proportion_st``, and
  ``secc_proportion_other``
* ``secc_lookup_status``, either ``matched`` or ``abstained``
* ``secc_abstention_reason``

An abstention reason is one of ``missing_name``, ``unsupported_script``,
``out_of_vocabulary``, ``unsupported_context``, or ``insufficient_support``.
Outkast matches only ASCII alphabetic surnames because the historical source
pipeline retained that script and format. It does not transliterate names.

Command line
------------

.. code-block:: console

   outkast-secc-lookup input.csv \
       --surname-column surname \
       --state bihar \
       --birth-year 1949 \
       --output result.csv

Data and artifact integrity
---------------------------

The typed Parquet runtime table contains one fixed-granularity hierarchy. The
package verifies the table and immutable JSON manifest by SHA-256 before the
first lookup. The manifest records the schema, hashes, release design,
provenance, reference population, supported states and years, coverage, and a
count-free surname vocabulary. That vocabulary distinguishes names absent from
the source from contextual cells withheld for insufficient support.

The source is the parsed `SECC 2011 dataset
<https://doi.org/10.7910/DVN/LIIBNB>`__. The source distribution includes
``data/secc/build_runtime_table.py``. Run it with the historical source artifact
to reproduce the packaged table and manifest. The source CSV itself is not
included.

License
-------

Outkast is released under the `MIT License
<https://opensource.org/licenses/MIT>`__.
