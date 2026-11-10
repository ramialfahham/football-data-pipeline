#!/usr/bin/env bash
#
# The nightly as Cloud Run Jobs runs it: the steps, order and gate of the `data:nightly` job in
# `.gitlab-ci.yml`, which tests/test_nightly_entrypoint_parity.py keeps in step.
# The job runs as its service account, so google.auth.default() needs no key file; only
# API_FOOTBALL_API_KEY is injected, from Secret Manager.

set -euo pipefail

export PYTHONPATH=.

# write_ci_output() in ingestion/api_football/completeness.py writes key=value to $CI_STEP_OUTPUT.
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
# dbt deps stays inside the gate so a night with no new data runs nothing.
dbt deps
dbt seed --target prod
# freshness_check is not excluded: this run ingested first, so freshness is real.
dbt build --target prod

echo "[nightly] done."
