# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Entries for releases before this file existed are reconstructed from the
release dates on [PyPI](https://pypi.org/project/outkast/#history) and are
deliberately brief: the record of *what* changed in them was not kept at the
time, and inventing one here would be worse than saying so.

## [Unreleased]

### Changed

- Replace `secc_caste` with the breaking
  `lookup_secc_caste_composition` aggregate lookup API.
- Return explicit match status, abstention reasons, and total support while
  preserving input row count, order, and index.
- Reject invalid columns, duplicate labels, invalid context types, and output
  column collisions.
- Replace the full-resolution runtime CSV with a typed Parquet table that
  excludes every contextual cell with support below 100.
- Release only state, birth year, and surname cells. Requiring both contexts and
  withholding all parent aggregates prevents complementary differencing of
  suppressed cells.
- Add a hash-verified manifest with schema, provenance, disclosure evidence,
  reference population, and shipped-universe metadata.
- Include the reproducible artifact builder in the source distribution without
  including its historical source CSV.
- Remove classifier, prediction, and individual-inference language.

## [1.0.0] - 2025-10-07

Modernization release, five years after 0.2.1.

## [0.2.1] - 2020-08-27

## [0.1.0] - 2020-02-16

Initial release.

[Unreleased]: https://github.com/appeler/outkast/compare/v.0.2.1...HEAD
[1.0.0]: https://pypi.org/project/outkast/1.0.0/
[0.2.1]: https://github.com/appeler/outkast/releases/tag/v.0.2.1
[0.1.0]: https://pypi.org/project/outkast/0.1.0/
