import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "orders_api"))
os.environ.setdefault("TABLE_NAME", "orders-test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import app  # noqa: E402


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[Item["orderId"]] = Item

    def get_item(self, Key):
        item = self.items.get(Key["orderId"])
        return {"Item": item} if item else {}

    def scan(self, Limit, ExclusiveStartKey=None):
        keys = sorted(self.items)
        if ExclusiveStartKey:
            keys = [k for k in keys if k > ExclusiveStartKey["orderId"]]
        page = keys[:Limit]
        result = {"Items": [self.items[k] for k in page]}
        if len(keys) > Limit:
            result["LastEvaluatedKey"] = {"orderId": page[-1]}
        return result


@pytest.fixture
def table(monkeypatch):
    fake = FakeTable()
    monkeypatch.setattr(app, "_table", fake)
    return fake


def _event(body=None, path=None, query=None):
    return {"body": json.dumps(body) if body is not None else None, "pathParameters": path, "queryStringParameters": query}


def test_create_order_persists_and_returns_201(table):
    resp = app.create_order(_event({"customerId": "c-1", "items": [{"sku": "A", "qty": 2}]}), None)
    assert resp["statusCode"] == 201
    order = json.loads(resp["body"])
    assert order["status"] == "NEW"
    assert order["createdAt"].endswith("Z")
    assert table.items[order["orderId"]]["items"] == [{"sku": "A", "qty": 2}]


@pytest.mark.parametrize("body", [{}, {"items": []}, {"items": [{"sku": "A", "qty": 0}]}, {"items": [{"qty": 1}]}])
def test_create_order_rejects_invalid_items(table, body):
    assert app.create_order(_event(body), None)["statusCode"] == 400


def test_create_order_rejects_non_object_body(table):
    assert app.create_order({"body": "[1,2]"}, None)["statusCode"] == 400
    assert app.create_order({"body": "not json"}, None)["statusCode"] == 400


def test_get_order_found_and_missing(table):
    created = json.loads(app.create_order(_event({"items": [{"sku": "A", "qty": 1}]}), None)["body"])
    assert app.get_order(_event(path={"orderId": created["orderId"]}), None)["statusCode"] == 200
    assert app.get_order(_event(path={"orderId": "nope"}), None)["statusCode"] == 404
    assert app.get_order(_event(), None)["statusCode"] == 400


def test_list_orders_paginates(table):
    for _ in range(3):
        app.create_order(_event({"items": [{"sku": "A", "qty": 1}]}), None)
    first = json.loads(app.list_orders(_event(query={"limit": "2"}), None)["body"])
    assert len(first["orders"]) == 2 and first["nextToken"]
    second = json.loads(app.list_orders(_event(query={"limit": "2", "nextToken": first["nextToken"]}), None)["body"])
    assert len(second["orders"]) == 1 and second["nextToken"] is None


def test_list_orders_rejects_bad_limit(table):
    assert app.list_orders(_event(query={"limit": "x"}), None)["statusCode"] == 400
