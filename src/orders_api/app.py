"""Orders API handlers (create, get, list).

Targets Python 3.12+ (shared by functions on python3.12 and python3.13).
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_table = None


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"not serializable: {type(value)!r}")


def _response(status: int, body: Any) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_json_default),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any] | None:
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


def create_order(event: dict[str, Any], context: Any) -> dict[str, Any]:
    body = _parse_body(event)
    if body is None:
        return _response(400, {"message": "body must be a JSON object"})

    items: list[dict[str, Any]] = body.get("items") or []
    if not items or not all(isinstance(i, dict) and i.get("sku") and int(i.get("qty", 0)) > 0 for i in items):
        return _response(400, {"message": "items must be a non-empty list of {sku, qty>0}"})

    order = {
        "orderId": str(uuid.uuid4()),
        "customerId": str(body.get("customerId") or "anonymous"),
        "items": [{"sku": str(i["sku"]), "qty": int(i["qty"])} for i in items],
        "status": "NEW",
        "createdAt": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
    }
    table().put_item(Item=order)
    logger.info("created order %s", order["orderId"])
    return _response(201, order)


def get_order(event: dict[str, Any], context: Any) -> dict[str, Any]:
    order_id = (event.get("pathParameters") or {}).get("orderId")
    if not order_id:
        return _response(400, {"message": "orderId is required"})
    item = table().get_item(Key={"orderId": order_id}).get("Item")
    if item is None:
        return _response(404, {"message": f"order {order_id} not found"})
    return _response(200, item)


def list_orders(event: dict[str, Any], context: Any) -> dict[str, Any]:
    params = event.get("queryStringParameters") or {}
    try:
        limit = max(1, min(int(params.get("limit", "20")), 100))
    except ValueError:
        return _response(400, {"message": "limit must be an integer"})

    scan_args: dict[str, Any] = {"Limit": limit}
    if params.get("nextToken"):
        scan_args["ExclusiveStartKey"] = {"orderId": params["nextToken"]}
    result = table().scan(**scan_args)
    next_key = (result.get("LastEvaluatedKey") or {}).get("orderId")
    return _response(200, {"orders": result.get("Items", []), "nextToken": next_key})
