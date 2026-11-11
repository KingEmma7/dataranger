import json

import pandas as pd
import pytest

from dataranger.cli import main


def run_calibrate(audit, labels):
    return main(["calibrate", "--audit", str(audit), "--labels", str(labels)])


def test_calibrate_demo_needs_more_reviewed_incidents(tmp_path, capsys):
    out = tmp_path / "demo"
    assert main(["demo", "--out", str(out)]) == 0
    capsys.readouterr()
    records = [json.loads(line) for line in (out / "audit.jsonl").read_text().splitlines()]
    partitions = [r["partition"] for r in records if not r["table_level"] and r.get("chosen")][:3]
    assert partitions
    labels = tmp_path / "reviewed.csv"
    pd.DataFrame({"partition": partitions, "verdict": "right"}).to_csv(labels, index=False)

    assert run_calibrate(out / "audit.jsonl", labels) == 0

    message = capsys.readouterr().out
    assert f"{len(partitions)} labeled incidents are not enough to certify alpha=0.01" in message
    assert "keep escalating" in message
    assert "Use --threshold" not in message


def write_audit(tmp_path, count=400):
    audit = tmp_path / "audit.jsonl"
    records = [
        {"partition": f"partition-{i}", "table_level": False,
         "chosen": {"residual": 0.01, "changed": 1, "action": "repair", "tier": "auto"}}
        for i in range(count)
    ]
    audit.write_text("".join(json.dumps(record) + "\n" for record in records))
    return audit


def test_calibrate_certifies_large_correct_sample(tmp_path, capsys):
    audit = write_audit(tmp_path)
    labels = tmp_path / "reviewed.csv"
    pd.DataFrame({"partition": [f"partition-{i}" for i in range(400)],
                  "verdict": "right"}).to_csv(labels, index=False)

    assert run_calibrate(audit, labels) == 0

    message = capsys.readouterr().out
    assert "threshold 0.5000" in message
    assert "(400 labeled incidents)" in message
    assert "Use --threshold 0.5000" in message
    assert "not enough" not in message


def test_calibrate_does_not_count_unlabeled_partitions(tmp_path, capsys):
    audit = write_audit(tmp_path)
    labels = tmp_path / "reviewed.csv"
    pd.DataFrame({"partition": ["partition-0", "partition-1", "not-in-audit"],
                  "verdict": "right"}).to_csv(labels, index=False)

    assert run_calibrate(audit, labels) == 0

    message = capsys.readouterr().out
    assert "2 labeled incidents are not enough to certify" in message
    assert "Use --threshold" not in message


def write_labels(tmp_path, text):
    labels = tmp_path / "reviewed.csv"
    labels.write_text(text)
    return labels


def test_calibrate_rejects_missing_verdict_column(tmp_path):
    labels = write_labels(tmp_path, "partition,note\npartition-0,ok\n")
    with pytest.raises(SystemExit) as exc:
        run_calibrate(write_audit(tmp_path), labels)
    assert "missing column(s) verdict" in str(exc.value)


def test_calibrate_rejects_blank_and_unknown_verdicts(tmp_path):
    labels = write_labels(tmp_path, "partition,verdict\npartition-0,right\npartition-1,\npartition-2,yes\n")
    with pytest.raises(SystemExit) as exc:
        run_calibrate(write_audit(tmp_path), labels)
    message = str(exc.value)
    assert "verdict must be right or wrong" in message
    assert "row 3: ''" in message
    assert "row 4: 'yes'" in message
    assert "row 2" not in message


def test_calibrate_accepts_verdicts_with_spaces_and_capitals(tmp_path, capsys):
    rows = "".join(f"partition-{i},Right \n" for i in range(400))
    labels = write_labels(tmp_path, "partition,verdict\n" + rows)

    assert run_calibrate(write_audit(tmp_path), labels) == 0

    message = capsys.readouterr().out
    assert "(400 labeled incidents)" in message
    assert "Use --threshold 0.5000" in message
