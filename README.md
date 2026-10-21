# atx-sample-orders-api

A standard **API Gateway + Lambda + DynamoDB** app (AWS SAM) used to prove the
[AWS Transform continuous modernization factory](../aws-atx-continuous-modernization) end to end
before pointing it at real application repos. Several functions intentionally run on **deprecated
Lambda runtimes**.

```
POST /orders ─► CreateOrderFn (python3.9, Globals) ─┐
GET  /orders/{id} ─► GetOrderFn (python3.9, Globals) ├─► OrdersTable (DynamoDB) ──stream──► StreamNotifyFn (nodejs18.x)
GET  /orders ─► ListOrdersFn (python3.10) ──────────┘                │
GET  /health ─► HealthFn (python3.13, already current)                └─ daily ► LegacyReportFn (python3.9, excluded)
```

## Layout

| Path | What |
|---|---|
| `template.yaml` | SAM template. The source of truth for every function's `Runtime`. |
| `src/` | Function code (`orders_api` is shared by three functions). |
| `tests/unit`, `tests/node` | pytest and `node --test` suites. ATX runs them as validation. |
| **`.atx/`** | **ATX campaign settings for this repo**: [`lambda-runtime.yaml`](.atx/lambda-runtime.yaml) spec, PR guard script. See [.atx/README.md](.atx/README.md). |
| `.aws/atx/skills/` | Project-level ATX client skill (conventions and validation steps for the agent). |
| `buildspec-pr.yml` | PR validation: tests, cfn-lint, ATX plan guard. Reported to GitHub as a status check. |
| `buildspec-build.yml` | Main-branch build: tests and `aws cloudformation package`. |
| `pipeline/app-pipeline.yaml` | CodePipeline V2 (CodeConnections): main → dev → manual approval → prod, plus the PR validation project. |

## Run locally

```bash
python -m pip install -r requirements-dev.txt
make test      # pytest + node --test + cfn-lint
```

## Deploy the pipeline (once)

Prerequisites: an AVAILABLE CodeConnections GitHub connection, and the factory stack deployed (for `AtxFactoryBucket`).

```bash
aws cloudformation deploy \
  --stack-name atx-sample-orders-api-pipeline \
  --template-file pipeline/app-pipeline.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ConnectionArn=arn:aws:codeconnections:us-east-1:111122223333:connection/xxxx \
    RepositoryId=my-org/atx-sample-orders-api \
    AtxFactoryBucket=<factory ArtifactBucketName output>
```

Pushing to `main` deploys `atx-sample-orders-api-dev`, waits for approval, then deploys `-prod`.

## Protect `main` (repo admin, no org admin needed)

Create a **repository ruleset** targeting the default branch:

- Require a pull request before merging, with **1 approval**, dismissing stale approvals
- Require status checks: `AWS CodeBuild <region> (atx-sample-orders-api-pr)`
- Block force pushes and deletions

## The demo flow

1. The factory plans this repo from `.atx/lambda-runtime.yaml`, and someone approves the plan in the factory pipeline.
2. ATX opens **two PRs**: one for Python (CreateOrder/GetOrder → 3.13, ListOrders → 3.12) and one for Node.js (StreamNotify → 24).
3. The PR build runs the tests, `cfn-lint` and `atx-guard.sh` (only planned runtimes changed, LegacyReportFn untouched).
4. A human reviews and approves the PR, then merges it. The main pipeline deploys to dev, waits for manual approval, then deploys to prod.
5. Confirm in the Lambda console or with
   `aws lambda list-functions --query "Functions[?starts_with(FunctionName,'atx-sample-orders-api-dev')].[FunctionName,Runtime]"`.
