# Changelog

## 0.3.0 (2026-11-11)

DataRanger's first community release: every change below came from outside contributors.

- `patrol` reads CSV, TSV and Parquet files, not only DuckDB tables. (#24, thanks @Hayabusa-YL)
- Schema-qualified table names such as `gold.payments` work with `patrol --db`. (#23, thanks @bfs2021)
- `patrol` prints the fixed / left alone / escalated breakdown, like `demo`. (#25, thanks @kunal-dangi)
- `patrol --json` prints a machine-readable summary, and `--fail-on-escalate` exits with code 2 when a person needs to look. (#27, thanks @Sarbajit-Sengupta)
- `calibrate` validates the labels file and reports bad verdicts with their spreadsheet row numbers. (#34, thanks @sarankumar1325)
- Reports and audit files are written as UTF-8 on every platform. (#33, thanks @jwalith4418-Mj)
- Each patrol also writes `incidents.csv`, one row per incident, for spreadsheet triage. (#36, thanks @Mnvv08)
- Tests for `calibrate` (#26, thanks @Sarbajit-Sengupta), and CI on Python 3.10 to 3.13 (#35, thanks @Mnvv08).

## 0.2.1 (2026-10-30)

- First public release on PyPI.
