"""Daily order count report.

Owned by another team and scheduled for decommission, so it is excluded from the
ATX runtime campaign in .atx/lambda-runtime.yaml.
"""
import logging
import os
from collections import Counter
from typing import Any, Dict

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def handler(event: Dict[str, Any], context: Any, table=None) -> Dict[str, Any]:
    table = table or boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    counts: Counter = Counter()
    kwargs: Dict[str, Any] = {"ProjectionExpression": "#s", "ExpressionAttributeNames": {"#s": "status"}}
    while True:
        page = table.scan(**kwargs)
        counts.update(item.get("status", "UNKNOWN") for item in page.get("Items", []))
        if "LastEvaluatedKey" not in page:
            break
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    report = dict(counts)
    logger.info("order status report: %s", report)
    return report
