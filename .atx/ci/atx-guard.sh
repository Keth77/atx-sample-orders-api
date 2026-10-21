#!/usr/bin/env bash
# ATX plan guard, run by the PR validation build (buildspec-pr.yml).
#
# On branches created by the ATX factory it verifies, deterministically, that only the
# planned Lambda runtimes changed (python -m factory check-plan). Other PRs are skipped.
#
# Env:
#   CODEBUILD_WEBHOOK_HEAD_REF  set by CodeBuild webhooks (refs/heads/<branch>)
#   ATX_BRANCH_REGEX            which branches are ATX branches (default ^atx/)
#   ATX_TOOLS_URI               s3://<factory-bucket>/tools/atx-factory-tools.zip
#   ATX_PLAN_URI                s3://<factory-bucket>/plans/<owner>/<repo>/latest.json
set -euo pipefail

branch="${CODEBUILD_WEBHOOK_HEAD_REF:-${ATX_HEAD_REF:-}}"
branch="${branch#refs/heads/}"
regex="${ATX_BRANCH_REGEX:-^atx/}"

if [[ -z "$branch" || ! "$branch" =~ $regex ]]; then
  echo "atx-guard: branch '${branch:-<unknown>}' is not an ATX branch (${regex}); skipping"
  exit 0
fi

: "${ATX_TOOLS_URI:?ATX_TOOLS_URI must point at the factory tools zip}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

aws s3 cp --quiet "$ATX_TOOLS_URI" "$work/tools.zip"
unzip -q "$work/tools.zip" -d "$work/tools"
python -m pip install -q -r "$work/tools/requirements.txt"

if [[ -f .atx/last-plan.json ]]; then
  plan=".atx/last-plan.json"            # committed by the factory in exec mode
else
  : "${ATX_PLAN_URI:?no .atx/last-plan.json and ATX_PLAN_URI is not set}"
  aws s3 cp --quiet "$ATX_PLAN_URI" "$work/plan.json"
  plan="$work/plan.json"
fi

echo "atx-guard: checking branch '$branch' against $plan"
PYTHONPATH="$work/tools" python -m factory check-plan --plan "$plan" --repo-dir . --require-change
