import json
import os
import subprocess
import sys


def run_with_legacy_locale(code, tmp_path):
    env = dict(os.environ, PYTHONUTF8="0", PYTHONCOERCECLOCALE="0", LC_ALL="C")
    result = subprocess.run([sys.executable, "-c", code, str(tmp_path)], env=env,
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr


def test_reports_are_utf8_with_non_ascii_title_and_category(tmp_path):
    run_with_legacy_locale(r'''
import sys
from pathlib import Path
import pandas as pd
from dataranger.patrol import PatrolResult, write_outputs

value = "Caf\u00e9 S\u00e3o Paulo \u6771\u4eac"
res = PatrolResult(incidents=[{"partition": "2026-01-01", "category": value,
                              "candidates": [], "decision": "escalate"}],
                   fixed_table=pd.DataFrame({"category": [value]}), days=["2026-01-01"])
write_outputs(res, Path(sys.argv[1]), title=value, table=value)
''', tmp_path)
    value = "Café São Paulo 東京"
    page = (tmp_path / "dashboard.html").read_text(encoding="utf-8")
    assert f"<title>{value}</title>" in page
    data = json.loads(page.split('<script type="application/json" id="data">')[1].split("</script>")[0])
    assert data["incidents"][0]["category"] == value
    assert data["meta"]["table"] == value
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert json.loads(audit)["category"] == value
    assert value in (tmp_path / "fixed_version.csv").read_text(encoding="utf-8")


def test_calibration_reads_utf8_audit_with_legacy_locale(tmp_path):
    record = {"partition": "Café São Paulo 東京", "table_level": False,
              "chosen": {"residual": 0.01, "changed": 1, "action": "repair", "tier": "auto"}}
    (tmp_path / "audit.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    (tmp_path / "labels.csv").write_text("partition,verdict\nCafé São Paulo 東京,right\n", encoding="utf-8")
    run_with_legacy_locale('''
import contextlib
import io
import sys
from pathlib import Path
from dataranger.cli import main

out = Path(sys.argv[1])
message = io.StringIO()
with contextlib.redirect_stdout(message):
    assert main(["calibrate", "--audit", str(out / "audit.jsonl"),
                 "--labels", str(out / "labels.csv")]) == 0
assert "1 labeled incidents are not enough" in message.getvalue(), message.getvalue()
''', tmp_path)
