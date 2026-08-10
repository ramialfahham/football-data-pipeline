#!/usr/bin/env bash
#
# The nightly pipeline, as run by Cloud Run Jobs. GitLab #39 Stage 1.
#
# THIS IS A 1:1 PORT of the `data:nightly` script block in `.gitlab-ci.yml` (lines 667-711).
# Same steps, same order, same gate. Nothing here is new logic — the point of Stage 1 is to
# change WHERE the pipeline runs, not WHAT it does, so that a GitLab-side event (a dropped
# cron, an exhausted minute quota) can no longer take the product's data offline.
#
# While both copies exist they can drift, and drift means the nightly silently stops doing a
# step. `tests/test_nightly_entrypoint_parity.py` fails if the two step lists diverge. Both the
# CI job and that test are removed together once this has proven itself (a follow-up governance
# MR — editing `.gitlab-ci.yml` needs a governance task; see working_agreement.md §2).
#
# Credentials: no key file and no WIF exchange. The job runs AS the service account, so
# `google.auth.default()` — which dbt-bigquery (`method: oauth`), google-cloud-bigquery and the
# ingestion package all use — resolves it natively. Only API_FOOTBALL_API_KEY is injected, from
# Secret Manager.

set -euo pipefail

export PYTHONPATH=.

# How the `new_data` signal survives the platform change, again. `write_ci_output()`
# (ingestion/api_football/completeness.py:769) writes `key=value` to whatever
# $CI_STEP_OUTPUT points at — it is read from the environment, not hardcoded to a CI
# vendor, which is why this port needs no Python change at all. GitLab set it to
# $CI_PROJECT_DIR/.ci-step-output; here it is a tmpfile.
export CI_STEP_OUTPUT="${CI_STEP_OUTPUT:-/tmp/.ci-step-output}"
: > "$CI_STEP_OUTPUT"

echo "[nightly] ingesting..."
API_FOOTBALL_INCLUDE_IN_PROGRESS=1 python -m ingestion.api_football.main

NEW_DATA=$(grep -E '^new_data=' "$CI_STEP_OUTPUT" 2>/dev/null | tail -1 | cut -d= -f2 || true)
if [ "$NEW_DATA" != "true" ]; then
    echo "[nightly] Ingestion reported new_data=${NEW_DATA:-<unset>} — nothing new landed."
    echo "[nightly] Skipping deps, seed, contract checks and the prod build."
    echo "[nightly] This is a \$0 night, not a failure."
    exit 0
fi

echo "[nightly] new_data=true — proceeding with the full prod build."
python scripts/check_layer_contract.py
python scripts/check_registry_var_sync.py

cd dbt_project
# `dbt deps` is INSIDE the gate, as it is in CI and was on GitHub. Cheap — a package fetch,
# no BigQuery — but the contract claims a quiet night runs nothing, and a claim that does not
# match the code is the defect regardless of the amount.
dbt deps
dbt seed --target prod
# `dbt build` with no selector = fqn:* (every node). freshness_check is deliberately NOT
# excluded: this run ingested first, so freshness is real.
dbt build --target prod

echo "[nightly] done."
