# `.atx/` — AWS Transform campaign settings for this repo

This folder is how the repo owner controls what the central ATX factory
([aws-atx-continuous-modernization](../../aws-atx-continuous-modernization)) does to this repo.

| File | Purpose |
|---|---|
| `lambda-runtime.yaml` | Repo spec: which functions move, to which runtime, with which managed transformation, plus validation commands, PR labels/reviewers, extra agent guidance and an agent-minute budget. Merged onto the factory default and validated against the factory policy. Delete it to use the defaults. |
| `ci/atx-guard.sh` | Run by the PR build. On ATX branches it runs `factory check-plan` to prove only the planned runtimes changed. |
| `last-plan.json` | Written by the factory in `exec` mode only. The exact plan this PR implements. |

Project-level ATX skills live in [`../.aws/atx/skills/`](../.aws/atx/skills/) (ATX discovers them automatically).

## What this repo's spec does

| Function | Current | Result |
|---|---|---|
| CreateOrderFn, GetOrderFn | python3.9 (Globals) | → python3.13, explicit `Runtime` (Globals stays because LegacyReportFn inherits it) |
| ListOrdersFn | python3.10 | → python3.12 (override) |
| StreamNotifyFn | nodejs18.x | → nodejs24.x (separate PR) |
| HealthFn | python3.13 | unchanged |
| LegacyReportFn | python3.9 | **excluded** |

Preview it locally from the factory repo:

```bash
python -m factory plan --campaign demo --local-repo ../atx-sample-orders-api --repository <owner>/atx-sample-orders-api --out /tmp/atx-out
cat /tmp/atx-out/summary.md
```

## Enrolling (repo owner, one time)

See the factory's [enrollment guide](../../aws-atx-continuous-modernization/docs/enrollment.md): ruleset on `main`,
fine-grained PAT for this repo only, stored as `atx-factory/github/<owner>/<repo>` in Secrets Manager.
