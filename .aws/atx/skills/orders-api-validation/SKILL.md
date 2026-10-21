---
name: orders-api-validation
description: Validation and conventions for the orders API when an AWS Transform transformation changes Lambda code or runtimes in this repository.
---
# Orders API validation

Use this skill whenever a transformation edits `template.yaml` or anything under `src/`.

## Conventions

- Each Lambda function's `Runtime` lives in `template.yaml`. `Globals.Function.Runtime` is
  shared by several functions; only change it when the task explicitly says so.
- `src/orders_api/` is shared by CreateOrderFn, GetOrderFn and ListOrdersFn. Code there must run on
  every runtime those functions use.
- Never edit `.atx/`, `.aws/`, `pipeline/` or `buildspec*.yml`.
- API responses must keep the same status codes and JSON shapes; tests assert them.

## Validate

Run all of these from the repository root. Each must exit 0:

```bash
python -m pytest -q tests/unit
node --test tests/node/*.test.js
cfn-lint template.yaml
```

If a test fails, fix the application code, not the test, unless the test itself depends on
behaviour that the new runtime removed.
