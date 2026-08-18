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

The package does not ship a cell with fewer than 100 reference records. It
aggregates each supported context independently and then suppresses cells, so a
broad cell is not the sum of the detailed cells that remain. The threshold
retains the following share of reference-record support:

======================  ================  ==============
Context                 Support retained  Cells retained
======================  ================  ==============
Surname                 100.0%            100.0%
State and surname       99.47%            32.85%
Birth year and surname  88.93%            16.77%
State, year, surname    83.45%            7.51%
======================  ================  ==============

Cell retention is low by design because the removed cells are small. Support
retention measures the share of the 93,366,763 records represented by retained
cells at each context level. These figures measure artifact coverage, not
coverage of India's population or of new input names.

The threshold sensitivity below reports support retention, not cell retention.
A floor of 100 keeps more than 83% of support at every context level while
suppressing 92.49% of the most detailed cells. A floor of 200 would lower
detailed-context support retention below 80%.

=========  ========  ======  ==========  =====================
Minimum    Surname   State   Birth year  State and birth year
=========  ========  ======  ==========  =====================
20         100.0%    99.87%  98.23%      95.22%
50         100.0%    99.71%  94.02%      89.53%
100        100.0%    99.47%  88.93%      83.45%
200        100.0%    99.06%  82.92%      76.44%
=========  ========  ======  ==========  =====================

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
collisions.

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

The typed Parquet runtime table contains four independently aggregated context
levels. The package verifies the table and immutable JSON manifest by SHA-256
before the first lookup. The manifest records the schema, hashes, disclosure
rule, provenance, reference-record count, supported states and years, context
cell counts, coverage, and a hash of the sorted national surname universe.

The source is the parsed `SECC 2011 dataset
<https://doi.org/10.7910/DVN/LIIBNB>`__. The historical source artifact has
SHA-256
``b190982755a5bf1e577ebde75fa9334f8d94fed27c2ce0ea7b255b31d22c991c``.
Run ``data/secc/build_runtime_table.py`` with a verified copy of that artifact
to reproduce the packaged table and manifest.

License
-------

Outkast is released under the `MIT License
<https://opensource.org/licenses/MIT>`__.
