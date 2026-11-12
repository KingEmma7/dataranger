# Scheduled patrol with GitHub Actions

[patrol.yml](patrol.yml) runs a daily patrol on generated demo data, then saves
`dashboard.html` and `audit.jsonl` together as a downloadable artifact. It uses
the released DataRanger 0.3.0 package, Python 3.12 and no credentials or paid API.
The job has a ten-minute timeout and keeps artifacts for seven days.

## Set up

1. In your repository, keep [make_demo_db.py](make_demo_db.py) at
   `examples/scheduled/make_demo_db.py` and copy `patrol.yml` to
   `.github/workflows/dataranger-patrol.yml`.
2. Commit both files to your default branch and enable GitHub Actions. The YAML
   under `examples/scheduled/` is only a template; it does not activate a schedule.
3. Open **Actions → Nightly DataRanger patrol → Run workflow** for a first run.
   Once enabled, the schedule requests a run each day at 06:17 UTC. Change the
   cron expression to a time after your nightly load. GitHub runs schedules from
   the default branch and may delay them; the schedule does not wait for your
   load to finish. See [GitHub's schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
4. Download `dataranger-patrol-<run-id>` from the run's **Artifacts** section,
   extract it, and open `dashboard.html`. Keep `audit.jsonl` beside it so the
   dashboard's audit link works.

## Try the same commands locally

From the repository root, with Python 3.12 available:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install dataranger==0.3.0
python examples/scheduled/make_demo_db.py /tmp/dataranger-demo.duckdb
dataranger patrol --db /tmp/dataranger-demo.duckdb \
    --table transactions --ref-table customers --manifest-table control_totals \
    --category category --out patrol-report
```

Choose a fresh database path on each local run; the helper refuses to overwrite
an existing file. It exports the same generated tables and planted problems used
by `dataranger demo` (seed 7, 60 days). The `patrol` CLI has no source-row input
for backfills, so it may escalate incidents that `demo` can repair.

Some incidents intentionally need review. A successful job means the patrol
completed, not that the data is clean. To fail a job when review is needed, add
`--fail-on-escalate` to the `patrol` command (exit code 2). The upload step uses
`always()` so reports are still uploaded when the patrol returns that status.
Other command failures also fail the job; an upload with no report files fails.
The file check requires both reports and allows an empty audit for a clean patrol.

## Point it at real tables

Replace **Generate demo tables** with a step that makes a consistent DuckDB
snapshot available on the runner after the load completes. Replace the patrol
command with your database path, table names and column mapping, for example:

```bash
dataranger patrol --db warehouse.duckdb \
    --table payments --ref-table customers --manifest-table control_totals \
    --key payment_id --reference customer_id --ref-key customer_id \
    --date booking_date --segment channel --amount amount --out patrol-report
```

The fact table needs a unique row key, reference key, date, segment and amount.
The reference table supplies valid reference keys. The control-totals table must
come from the source system, independently of the potentially faulty fact table:
one row per date and segment, plus a `*` segment row for each day's totals. In the
example above its columns are `booking_date`, `channel`, `n` (row count) and
`amount` (sum). Add `--category` if your fact table has a category column.

You can also use exported files; see the [main README](../../README.md#try-it)
for file inputs and calibration. The default repair threshold comes from the
benchmark; calibrate it on reviewed incidents from your own data before relying
on it for real tables. DataRanger leaves inputs unchanged and writes a separate
`fixed_version.csv`; this workflow uploads only the dashboard and audit log and
does not write repairs back to your warehouse.

If fetching your real data needs credentials, use repository secrets in that
fetch step. Reports can contain sensitive data: choose a repository and artifact
retention policy suitable for your team before uploading them.
