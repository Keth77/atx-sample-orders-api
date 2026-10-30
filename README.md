# atx-sample-orders-api

A standard **API Gateway + Lambda + DynamoDB** app (AWS SAM) for proving the
[AWS Transform continuous modernization factory](https://github.com/Keth77/aws-atx-continuous-modernization)
end to end before using it on real repos. Several functions deliberately run on **deprecated Lambda runtimes**.

```
POST /orders      ─► CreateOrderFn (python3.9, Globals) ─┐
GET  /orders/{id} ─► GetOrderFn    (python3.9, Globals) ─┼─► OrdersTable (DynamoDB) ──stream──► StreamNotifyFn (nodejs18.x)
GET  /orders      ─► ListOrdersFn  (python3.10) ─────────┘          │
GET  /health      ─► HealthFn      (python3.13, current)            └── daily ──► LegacyReportFn (python3.9, excluded)
```

## Layout

| Path | What |
|---|---|
| `template.yaml` | SAM template; the source of truth for every function's `Runtime` |
| `src/` | Function code (`orders_api` is shared by three functions) |
| `tests/unit`, `tests/node` | pytest and `node --test` suites; ATX runs them as validation |
| **`.atx/`** | **What the factory may change in this repo**: the [spec](.atx/lambda-runtime.yaml) and the PR guard script. See [.atx/README.md](.atx/README.md). |
| `.aws/atx/skills/` | Project-level ATX skill: conventions and validation steps for the agent |
| `buildspec-pr.yml` | PR check: tests, cfn-lint, ATX plan guard (reported to GitHub as a status check) |
| `buildspec-build.yml` | Main-branch build: tests, then `aws cloudformation package` |
| `cicd/pipeline.yaml` | This app's own CI/CD stack: pipeline, PR check, roles, bucket |

## CI/CD

This app owns its CI/CD, like any existing app would; the ATX factory only opens PRs. Create the stack once, after
the factory's `atx-factory` stack exists (the PR guard reads the factory bucket from SSM `/atx-factory/artifact-bucket`):

```bash
aws cloudformation deploy --stack-name atx-sample-orders-api-cicd --template-file cicd/pipeline.yaml \
  --capabilities CAPABILITY_IAM --parameter-overrides ConnectionArn=<codeconnections-arn>
```

- Push to `main` → pipeline `atx-sample-orders-api-main`: Source → Build → Deploy stack `atx-sample-orders-api-dev`
- PR to `main` → CodeBuild `atx-sample-orders-api-pr` → status check on the PR (stack output `PrCheckName`)

| Stack | Holds | Created by |
|---|---|---|
| `atx-sample-orders-api-cicd` | Pipeline and its role, build and PR-check projects, CodeBuild role, CloudFormation deploy role, artifact bucket (emptied on delete by a small Lambda), log groups | You, once |
| `atx-sample-orders-api-dev` | The app: six functions and roles, API, `OrdersTable`, schedule, log group | The pipeline |

To remove: delete `atx-sample-orders-api-dev`, then `atx-sample-orders-api-cicd` (the app stack is deleted with a
role that lives in the CI/CD stack). Changes to `cicd/pipeline.yaml` aren't deployed automatically; update the stack
by hand.

Each app stack owns its Lambda log group, so deleting it leaves nothing behind. To enroll this repo and protect
`main`, follow the factory's [enrollment guide](https://github.com/Keth77/aws-atx-continuous-modernization/blob/main/docs/enrollment.md).

## Run locally

```bash
python -m pip install -r requirements-dev.txt
make test      # pytest + node --test + cfn-lint
```

## The demo flow

1. The factory plans this repo from `.atx/lambda-runtime.yaml`, and someone approves the plan.
2. ATX opens **two PRs**: Python (CreateOrder/GetOrder → 3.13, ListOrders → 3.12) and Node.js (StreamNotify → 24).
3. The PR check runs the tests, `cfn-lint` and `atx-guard.sh` (only planned runtimes changed, LegacyReportFn untouched).
4. A human approves and merges. The app's own pipeline deploys `atx-sample-orders-api-dev`.
5. Confirm the new runtimes:
   `aws lambda list-functions --query "Functions[?starts_with(FunctionName,'atx-sample-orders-api-dev')].[FunctionName,Runtime]"`
