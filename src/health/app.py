import json
import os
import platform


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok", "stage": os.environ.get("STAGE"), "python": platform.python_version()}),
    }
