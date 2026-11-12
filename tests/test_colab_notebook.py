"""Run the tutorial cells with the installed source package and inspect the outputs."""
import base64
from html.parser import HTMLParser
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "examples" / "try_dataranger.ipynb"


class Tags(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def test_notebook_demo_audit_and_dashboard(tmp_path, monkeypatch, capfd):
    pytest.importorskip("IPython", reason="Install the test extra to run the notebook cells")
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    monkeypatch.chdir(tmp_path)
    namespace = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and "install" not in cell["metadata"].get("tags", []):
            # CI already installs the checkout. Do not replace it with the PyPI package.
            exec(compile("".join(cell["source"]), str(NOTEBOOK), "exec"), namespace)

    records = namespace["records"]
    summary = capfd.readouterr().out
    assert f"{len(records)} incidents:" in summary
    assert any(r["decision"] == "auto-fixed" for r in records)
    assert any(r["decision"] == "escalate" for r in records)
    preview = namespace["audit_preview"]
    assert len(preview) == 5
    assert preview["Decision"].tolist() == [r["decision"] for r in records[:5]]
    assert preview["Chosen candidate"].tolist() == [(r.get("chosen") or {}).get("fix", "None") for r in records[:5]]

    frames = [attrs for tag, attrs in Tags(namespace["dashboard_view"].data).tags if tag == "iframe"]
    assert len(frames) == 1
    frame = frames[0]
    assert frame["title"]
    assert set(frame["sandbox"].split()) == {"allow-scripts", "allow-downloads"}
    page = frame["srcdoc"]
    data = json.loads(page.split('<script type="application/json" id="data">')[1].split("</script>")[0])
    assert len(data["incidents"]) == len(records)
    tags = Tags(page).tags
    assert ("base", {"href": "about:srcdoc"}) in tags
    download = next(attrs for tag, attrs in tags if tag == "a" and attrs.get("download") == "audit.jsonl")
    assert base64.b64decode(download["href"].split(",", 1)[1]) == namespace["audit_path"].read_bytes()
    original = (namespace["report_dir"] / "dashboard.html").read_text(encoding="utf-8")
    assert 'href="audit.jsonl"' in original
    assert "about:srcdoc" not in original


def test_colab_badge_targets_the_notebook():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    url = "https://colab.research.google.com/github/akshaysharma1088/dataranger/blob/main/"
    assert f"]({url}{NOTEBOOK.relative_to(ROOT).as_posix()})" in readme
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            assert index and notebook["cells"][index - 1]["cell_type"] == "markdown"
