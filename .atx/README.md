# `.atx/` — AWS Transform settings for this repo

This folder is how the repo owner controls what the central
[ATX factory](https://github.com/Keth77/aws-atx-continuous-modernization) changes in this repo.

| File | Purpose |
|---|---|
| `lambda-runtime.yaml` | The repo spec: which functions move, to which runtime, with which managed transformation; validation commands; PR labels and reviewers; extra agent guidance; agent-minute budget. Merged onto the factory default and checked against the factory policy. Delete it to use the defaults. |
| `ci/atx-guard.sh` | Run by the PR check. On ATX branches it runs `factory check-plan` to prove only the planned runtimes changed. |
| `last-plan.json` | Written by the factory in `exec` mode only: the exact plan a PR implements. |

Project-level ATX skills live in [`.aws/atx/skills/`](../.aws/atx/skills/); ATX picks them up automatically.

## What this repo's spec does

| Function | Current | Result |
|---|---|---|
| CreateOrderFn, GetOrderFn | python3.9 (Globals) | → python3.13 with an explicit `Runtime`; Globals stays because LegacyReportFn inherits it |
| ListOrdersFn | python3.10 | → python3.12 (override) |
| StreamNotifyFn | nodejs18.x | → nodejs24.x (separate PR) |
| HealthFn | python3.13 | unchanged |
| LegacyReportFn | python3.9 | **excluded** |

Preview it from a factory checkout:

```bash
python -m factory plan --campaign demo --local-repo ../atx-sample-orders-api \
  --repository Keth77/atx-sample-orders-api --out /tmp/atx-out
cat /tmp/atx-out/summary.md
```

## Where the token is configured

Not here. The factory needs the token to clone this repo before it can read this folder, so the repo → secret
mapping lives in the factory's
[`config/repos.yaml`](https://github.com/Keth77/aws-atx-continuous-modernization/blob/main/config/repos.yaml).
See the [enrollment guide](https://github.com/Keth77/aws-atx-continuous-modernization/blob/main/docs/enrollment.md).
