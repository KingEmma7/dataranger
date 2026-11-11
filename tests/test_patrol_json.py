import json

import pytest

from dataranger.bench import generate, inject
from dataranger.cli import main


@pytest.fixture
def patrol_args(tmp_path):
    case = inject(generate(7, "small", n_days=40))
    for name, frame in (("facts", case.warehouse["transactions"]),
                        ("refs", case.warehouse["customers"]),
                        ("manifest", case.manifest)):
        frame.to_csv(tmp_path / f"{name}.csv", index=False)
    return ["patrol", "--facts-file", str(tmp_path / "facts.csv"),
            "--ref-file", str(tmp_path / "refs.csv"),
            "--manifest-file", str(tmp_path / "manifest.csv"),
            "--out", str(tmp_path / "report with spaces")]


@pytest.mark.parametrize("fail_on_escalate, expected_code", [(False, 0), (True, 2)])
def test_json_summary_matches_written_audit(patrol_args, tmp_path, capsys,
                                          fail_on_escalate, expected_code):
    args = patrol_args + ["--json"]
    if fail_on_escalate:
        args.append("--fail-on-escalate")

    assert main(args) == expected_code

    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert captured.err == ""
    out = tmp_path / "report with spaces"
    audit = [json.loads(line) for line in (out / "audit.jsonl").read_text().splitlines()]
    assert summary == {
        "incidents": len(audit),
        "auto_fixed": sum(r["decision"] == "auto-fixed" for r in audit),
        "no_action": sum(r["decision"] == "no action needed" for r in audit),
        "escalate": sum(r["decision"] == "escalate" for r in audit),
        "report": str(out / "dashboard.html"),
    }
    assert summary["escalate"] > 0
    assert (out / "dashboard.html").exists()


def test_fail_on_escalate_keeps_human_summary(patrol_args, capsys):
    assert main(patrol_args + ["--fail-on-escalate"]) == 2
    message = capsys.readouterr().out
    assert "incidents:" in message
    assert "Report:" in message


@pytest.mark.parametrize("json_output", [False, True])
def test_fail_on_escalate_succeeds_without_escalations(tmp_path, monkeypatch,
                                                     capsys, json_output):
    # Exercise the CLI's successful no-incident path without depending on detector thresholds.
    from types import SimpleNamespace

    import dataranger.patrol as patrol_module

    monkeypatch.setattr(patrol_module, "from_files", lambda *args: (None, None, None))
    monkeypatch.setattr(patrol_module, "patrol", lambda *args, **kwargs: SimpleNamespace(incidents=[]))
    monkeypatch.setattr(patrol_module, "write_outputs", lambda *args, **kwargs: None)
    args = ["patrol", "--facts-file", "facts.csv", "--ref-file", "refs.csv",
            "--manifest-file", "manifest.csv", "--out", str(tmp_path), "--fail-on-escalate"]
    if json_output:
        args.append("--json")

    assert main(args) == 0

    message = capsys.readouterr().out
    if json_output:
        summary = json.loads(message)
        assert summary["incidents"] == summary["escalate"] == 0
    else:
        assert "0 incidents: 0 fixed" in message
