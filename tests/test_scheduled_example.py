"""Exercise the scheduled example through its helper and the real patrol CLI."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "examples" / "scheduled" / "make_demo_db.py"


def test_scheduled_demo_patrol(tmp_path):
    db = tmp_path / "demo input" / "warehouse.duckdb"
    subprocess.run([sys.executable, str(HELPER), str(db)], check=True, capture_output=True, text=True)
    before = hashlib.sha256(db.read_bytes()).digest()

    out = tmp_path / "morning report"
    result = subprocess.run(
        [sys.executable, "-m", "dataranger.cli", "patrol", "--db", str(db),
         "--table", "transactions", "--ref-table", "customers", "--manifest-table", "control_totals",
         "--category", "category", "--out", str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "incidents" in result.stdout
    audit = [json.loads(line) for line in (out / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert audit
    assert any(r["decision"] == "auto-fixed" for r in audit)
    assert any(r["decision"] == "escalate" for r in audit)
    page = (out / "dashboard.html").read_text(encoding="utf-8")
    data = json.loads(page.split('<script type="application/json" id="data">')[1].split("</script>")[0])
    assert len(data["incidents"]) == len(audit)
    assert 'href="audit.jsonl"' in page
    assert (out / "fixed_version.csv").stat().st_size > 0
    assert hashlib.sha256(db.read_bytes()).digest() == before

    repeat = subprocess.run([sys.executable, str(HELPER), str(db)], capture_output=True, text=True)
    assert repeat.returncode == 2
    assert "already exists" in repeat.stderr
    assert hashlib.sha256(db.read_bytes()).digest() == before
