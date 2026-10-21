import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


health = _load("health_app", "src/health/app.py")
legacy = _load("legacy_report_app", "src/legacy_report/app.py")


def test_health_ok(monkeypatch):
    monkeypatch.setenv("STAGE", "dev")
    body = json.loads(health.handler({}, None)["body"])
    assert body["status"] == "ok" and body["stage"] == "dev"


class PagedTable:
    def __init__(self, pages):
        self.pages = pages
        self.calls = 0

    def scan(self, **kwargs):
        page = self.pages[self.calls]
        self.calls += 1
        return page


def test_legacy_report_counts_across_pages():
    table = PagedTable([
        {"Items": [{"status": "NEW"}, {"status": "NEW"}], "LastEvaluatedKey": {"orderId": "2"}},
        {"Items": [{"status": "SHIPPED"}, {}]},
    ])
    assert legacy.handler({}, None, table=table) == {"NEW": 2, "SHIPPED": 1, "UNKNOWN": 1}
    assert table.calls == 2
