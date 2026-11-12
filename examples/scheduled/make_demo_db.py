"""Export the built-in demo data to a new DuckDB database for the patrol CLI."""
import argparse
from datetime import date, timedelta
from pathlib import Path

import duckdb

from dataranger.bench import generate, inject


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db", type=Path, help="new demo database path (must not exist)")
    args = parser.parse_args(argv)
    if args.db.exists():
        parser.error(f"{args.db} already exists; choose a new path for the demo database")

    case = inject(generate(7, "small", start=date.today() - timedelta(days=60)))
    args.db.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(args.db)) as con:
        for name, frame in [("transactions", case.warehouse["transactions"]),
                            ("customers", case.warehouse["customers"]),
                            ("control_totals", case.manifest)]:
            con.register("demo_input", frame)
            con.execute(f"create table {name} as select * from demo_input")
            con.unregister("demo_input")
    print(f"Demo database: {args.db}")


if __name__ == "__main__":
    main()
