# Task contract — Clone and continue: one setup command (#161)

objective: >
  After `git clone`, one command (`python scripts/bootstrap.py`) sets up everything that needs no
  credentials, and `python scripts/bootstrap.py --verify` proves it: tests, pre-commit on all files,
  the site build from sample data. The README says what the credentialed level needs and where it
  goes. Generic config is committed, personal config stays out, and old-machine paths are gone.
refs: >
  GitLab #161 (the requirement, its checklist and its plan; approved in plan mode 2026-09-24).
  Plan produced by an independent expert review from the requirement and the measurements in the
  issue's exploration fold. Doc wording reused from the parked branch
  `parked/fix/dbt-profile-local-to-this-repo--profile-root`; its guard script is NOT reused.

scope_paths:
  - scripts/bootstrap.py
  - tests/test_bootstrap.py
  - tests/test_lint_config.py
  - tests/test_governance_hooks.py
  - README.md
  - CLAUDE.md
  - AGENTS.md
  - .gitignore
  - .claude/launch.json
  - .mcp.json
  - .gitlab-ci.yml
  - .pre-commit-config.yaml
  - .ruff-ci.toml
  - requirements-dev.txt
  - .python-version
  - .nvmrc
  - site_v2/package.json
  - site_v2/package-lock.json
  - dbt_project/profiles.example.yml
  - .claude/skills/onboard-endpoint/SKILL.md
  # end-of-file / trailing-whitespace fixes the new pre-commit config requires (whitespace only)
  - requirements.txt
  - dbt_project/packages.yml
  - dbt_project/models/3_core/.gitkeep
  - dbt_project/models/4_intermediate/.gitkeep
  - dbt_project/models/5_marts/.gitkeep
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - ingestion/api_football/loads/competition_runner.py
  - design-mocks/rows.py
  - design-mocks/interaction.py
  - .claude/task/**
  - docs/tracker/**

protected_override: >
  `.gitlab-ci.yml` and `.mcp.json` are protected paths. Authority: the plan for GitLab #161,
  approved in plan mode on 2026-09-24, whose How names both ("`.gitlab-ci.yml`: `lint:python` runs
  pre-commit, the two site jobs move to `node:24`, and the new setup job (never on a schedule ...)"
  and "`.mcp.json` (relative paths, `${DBT_PATH:-.venv/Scripts/dbt.exe}`)"), and whose header says
  the contract quotes that approval for the two protected files. The item-by-item answers in chat
  the same day: Node 24 in CI "ok"; the CI job on Linux, on setup-file MRs and manual, "ok". The
  commit message and the MR head repeat this under `Locked files`; his merge is the approval
  (working_agreement §11).

impact_map: >
  writers: none. No raw writer, dbt model logic, seed or export script changes. Structural paths
  touched are whitespace only: `dbt_project/models/**` (three `.gitkeep` files that hold a single
  CRLF, and `domestic_league.yml` gains a final newline) and
  `ingestion/api_football/loads/competition_runner.py` (final newline). A final newline changes no
  parsed YAML, no compiled SQL and no Python AST: blast radius none, checked by `dbt parse` and
  pytest staying green.
  .gitlab-ci.yml, what fires it: (1) `lint:python` (every non-schedule pipeline, `*not_on_schedule`
  first, unchanged) now runs `pre-commit run --all-files`; its name is unchanged, so
  `build:nightly-image`'s `needs:` on it (pinned by
  `test_governance_hooks.py::...required_gates`) still holds. (2) `build:site-v2` and
  `deploy:site-v2` image `node:22` -> `node:24`; rules, scripts and artifacts unchanged;
  `validate:ui` still needs `build:site-v2` (pinned by `test_design_inventory.py`). (3) new job
  `setup:clean-clone`: `*not_on_schedule` as its FIRST rule (pinned by
  `test_every_job_except_the_nightly_is_guarded_against_schedules`, because any GitLab schedule
  also starts the prod `data:nightly`), then MR pipelines whose changes touch the setup inputs,
  then `web` manual. No GCP auth, no `id_tokens`, no warehouse, no deploy, no `resource_group`.
  What imports the file: `tests/test_lint_config.py` (requires a `ruff check --config .ruff-ci.toml`
  invocation; the invocation moves to `.pre-commit-config.yaml`, so the test reads both files),
  `tests/test_governance_hooks.py` (schedule guard, required gates, the `DBT_PROFILES_DIR` pin:
  untouched properties), `tests/test_design_inventory.py`, `tests/test_ci_data_job_invariants.py`,
  `tests/test_persist_docs_policy.py`, `scripts/check_task_artifacts.py` (none of their jobs change).
  What stops being enforced if wrong: if pre-commit in `lint:python` failed to run ruff with the CI
  config, CI's Python lint would weaken silently; the updated `test_lint_config.py` pins the hook's
  entry, its `--config` and the absence of `--select`/`--ignore`, and pins the hook's ruff version
  to the `requirements-dev.txt` pin. Failure behaviour: no `allow_failure` anywhere; a red hook is a
  red job.
  .mcp.json, what fires it: Claude Code launches the `dbt` MCP server at session start. Today it
  fails to connect (old-machine paths). After: relative `DBT_PROJECT_DIR`/`DBT_PROFILES_DIR` and
  `${DBT_PATH:-.venv/Scripts/dbt.exe}`. Nothing imports it; no guard depends on it; its failure mode
  is the dbt tool not starting, which is the state today. The enabled tool list is unchanged
  (read-only lineage/list/parse tools).
  layer_rules: none touched (`check_layer_contract.py` reads models; whitespace only).
  deploy_order: nothing reaches a host or a dataset. The nightly (Cloud Scheduler `fdp-nightly`) is
  untouched; no GitLab schedule is created.
  blast_radius: none on data. Developer-facing: every clone that runs the setup gets pre-commit
  (pre-commit + post-commit hook types) installed into `.git/hooks`; the post-commit hook is the
  existing `.githooks/post-commit`, unchanged.

decisions_taken: >
  Every item below is a line of GitLab #161, approved in plan mode 2026-09-24, or an item answered
  in chat that day.

  pre-commit (item 1, "ok"): runs exactly what CI runs offline. In: file hygiene with generated or
  frozen trees excluded (`site_v2/src/data/`, `site/` retired and frozen, `.github/workflows/`
  protected and kept unedited, `.claude/task/` generated review artifacts), ruff check at CI's
  version with `--config .ruff-ci.toml`, the secret scan. Out: `ruff-format` (never enforced; would
  reformat 112 files) and `sqlfluff` (needs BigQuery; CI's data jobs still lint SQL). CI's
  `lint:python` runs pre-commit, so there is one config. This reverses the documented choice to
  keep the two independent (`.ruff-ci.toml` header, `.gitlab-ci.yml` lint comment); both are
  rewritten, not appended.

  Windows path limit (item 2, "ok", as corrected the same turn): setup stops only when long paths
  are off AND the repo path is too long. Measured: the deepest installed file is 150 characters
  below the root (`.venv\Lib\site-packages\google\cloud\bigquery_storage_v1alpha\...`); Windows
  allows 259; the limit is set at 80 for margin. The script never changes the system setting.

  Node 24 (item 3, "ok"): `.nvmrc` `24`, `engines.node` `>=24 <25`, CI site jobs on `node:24`.

  npm install scripts (item 4, "ok"; #161 line): denied if the site builds without them, allowed
  otherwise; the build is the test.

  Parked guard script (item 5, "ok"): left out; the root-anchored `.gitignore` entry is the control.

  CI setup job (item 6 as revised, "ok"): Linux only, MR pipelines touching setup inputs plus
  manual, never on a schedule. No Windows runner, no scheduled run.

  Proof folder (item 7, "ok"): `C:\01_Projects\fdp-proof`, cloned from GitLab, deleted after.

  Git hooks (independent review, his "yes" 2026-09-24 to "Should every clone, including yours,
  auto-push each commit and open an MR?"): pre-commit installs both hook types; the existing
  `.githooks/post-commit` runs as a pre-commit post-commit hook. No `core.hooksPath`: the agent
  guard blocks setting it and AGENTS.md already says to unset it; setup stops with that instruction
  if it finds one set.

  `.mcp.json`: Claude Code documents `${VAR}` and `${VAR:-default}`; `${CLAUDE_PROJECT_DIR}` is
  documented only for plugin servers and a project server's working directory is undocumented, so
  relative paths are used and the proof shows the tool connecting.

  `--fetch-key` (#161 line "`python scripts/bootstrap.py --fetch-key` puts the API key from Secret
  Manager into `.env` without printing it; you run it, Claude never does"): it reads the EXISTING
  secret `api-football-key` with the caller's own gcloud login and writes it into `.env` only where
  `API_FOOTBALL_API_KEY` is empty. No IAM change, no new secret, no key printed or logged.

  Secret scans keep full coverage: `detect-private-key` and `check-no-secrets` carry no path
  exclusion; only the whitespace fixers skip the generated or frozen trees. `API_KEY_SECRET_NAME`
  in `scripts/bootstrap.py` holds the secret's NAME, spelled so the scan does not read it as a value.

  THRESHOLD DECLARATIONS. NEW MECHANISM: `scripts/bootstrap.py` (setup script) and CI job
  `setup:clean-clone`, both lines of #161 as approved; the pre-commit post-commit wiring (his "yes"
  above). No new runtime dependency: `pre-commit` joins `requirements-dev.txt` (developer-only,
  named in his requirement). RECURRING COST: `setup:clean-clone` uses the existing self-hosted
  runner (roughly 5-8 minutes) only on MRs that change setup inputs or on a manual run; no money,
  no BigQuery, no API-Football calls. `lint:python` gains the pre-commit hook-environment install
  (cached).

decisions_reserved:
  - none open: every choice in this task was put to the CPO item by item on 2026-09-24 and is
    recorded above; a new CPO-class question found while building is brought to him, not decided.

done_when:
  - fresh clone from GitLab into C:\01_Projects\fdp-proof; `python scripts/bootstrap.py` exits 0;
    a second run exits 0 and changes no file
  - in that clone `python scripts/bootstrap.py --verify` exits 0 (pytest, pre-commit --all-files,
    site build) and `dbt debug` passes from the root with the written profile
  - the dbt MCP tool connects from this repo
  - `.venv/Scripts/python.exe -m pytest tests/ -q` green in the working repo
  - blinded review cycle PASS; MR opened with the `Default` head; CI green
  - output of the proof pasted into the MR

amendments: (none)
