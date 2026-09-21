# Task contract — #109 step 3, MR D: the projection check, wired

objective: >
  Every column a model `.yml` lists exists in that model's projection, checked against the prod
  catalogue after every merge: `scripts/check_yml_vs_projection.py --catalog <path>` (the reverse
  of `declare_missing_columns.py`), its pytest, one line in `data:build:main` right after
  `dbt docs generate`, one line in `validate:governance` running the relationships gate MR B
  built, one pin in `test_persist_docs_policy.py`, the `validate-local` table rows, and §3.5 saying
  both mechanisms are in place. No model SQL, no model yml, no seed; no number on the site moves.

refs: >
  #109, "Step 3 — the mechanisms and the sweep", the MR D line (plan approved in chat 2026-09-20,
  quoted in `decisions_taken`). `scripts/declare_missing_columns.py` for the helpers' shape
  (models on disk, listed columns, `_catalog_columns`, the partial-catalogue abort);
  `scripts/check_relationships_coverage.py` for the gate shape and the floors precedent;
  `dbt_project/docs/engineering_standards.md` §3.5. Measured read-only on this branch against
  the prod catalogue of the `data:build:main` after !213 (generated 2026-09-20 12:29 UTC): 101
  models on disk, 101 in the catalogue, 1,915 listed columns, 5 struct entries
  (`recent_meetings.*` in `shared.yml`), 0 absent — the check lands green.
  `check_relationships_coverage.py` exits 0 on the tree today, printing its 3 soft links.

scope_paths:
  - scripts/check_yml_vs_projection.py
  - tests/test_check_yml_vs_projection.py
  - .gitlab-ci.yml
  - tests/test_persist_docs_policy.py
  - .claude/skills/validate-local/SKILL.md
  - dbt_project/docs/engineering_standards.md
  - scripts/check_relationships_coverage.py
  - tests/test_check_relationships_coverage.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

protected_override: >
  `.gitlab-ci.yml` is a protected path. The authority is the dated plan approval recorded in
  `decisions_taken` below — the MR D line on #109, approved in chat on 2026-09-20, which names
  the two CI lines and calls this a governance MR. The commit message and the MR head repeat it
  under `Locked files`; his merge is the approval (working_agreement §11).

impact_map: >
  writers: none — no raw writer, no dbt model, no seed, no export script. The structural surface
  is the protected CI file and the two gate scripts it runs.
  what fires it: line 1 (`check_yml_vs_projection.py`) runs inside `data:build:main`, which runs
  on a push to `main` whose changes match `data_paths_prod`, or as a manual web button; never on
  a schedule (`*not_on_schedule` first) and never in an MR pipeline — so a hit turns `main` red
  after prod is built and tested, and costs signal, never data. Line 2
  (`check_relationships_coverage.py`) runs inside `validate:governance`, every non-schedule
  pipeline, MR and `main` alike.
  what imports the file: `tests/test_governance_hooks.py` (the `if:` classifier raises on an
  unknown spelling — no `rules:` change here; the schedule guard checks every job — none added),
  `tests/test_persist_docs_policy.py` (`data:build:main`'s shape: docs generated once and only
  there, `--static --target prod`, no `allow_failure`, the catalogue published — all untouched;
  gains the pin that the projection check runs in that job after the docs line),
  `tests/test_governance_doc_parity.py` (keeps the file in the protected set). The projection
  check reads `dbt_project/target/catalog.json`, which `dbt docs generate` writes two lines
  earlier in the same job, so in CI it can never see a partial catalogue; its partial-catalogue
  abort exists for a dev machine. The `data:build:main` script ends inside `dbt_project/`, so
  the line starts with `cd "$CI_PROJECT_DIR"`; the artifact paths are relative to
  `CI_PROJECT_DIR` already and do not move.
  what stops being enforced if it is wrong: nothing that is enforced today — both jobs keep
  every existing line verbatim. What starts: a listed column that the model no longer emits is a
  red `data:build:main`; a foreign key without `relationships` or a declared soft link is a red
  `validate:governance` on every MR — a second place, since MR B's pytest already runs that gate
  on the real tree inside `test:python`.
  failure behaviour: no `allow_failure` on either job; a red line fails the job like any other.
  Both scripts are offline, stdlib plus PyYAML (already in `requirements.txt`), under a second
  each. No image, dependency or `rules:` change. Not in it: `stop_gate.py`'s FAST_GATES, a
  second protected path the issue line excludes.
  layer_rules: none touched (`check_layer_contract.py` reads models, not this).
  deploy_order: nothing reaches a host or a dataset; the nightly (Cloud Scheduler) is untouched.
  blast_radius: none on data — 0 of 1,915 listed columns absent, so the first run on `main` is
  green; `check_relationships_coverage.py` exits 0 today, so `validate:governance` cannot go red
  on the merge itself. Recurring cost: none — two offline lines.

decisions_taken: >
  The MR D line on #109, approved in chat on 2026-09-20 and written to the issue, is the spec and
  the authority for the protected edit: "MR D — the projection check, wired (plan approved in
  chat 2026-09-20 …). `scripts/check_yml_vs_projection.py --catalog <path>` … Two lines in
  `.gitlab-ci.yml`: the projection check in `data:build:main` right after `dbt docs generate`
  (post-merge, where the catalogue is whole; a red there costs signal, never data — prod is built
  and tested first), and `check_relationships_coverage.py` in `validate:governance`; one pin in
  `test_persist_docs_policy.py` … `validate-local`'s CI table gains the row; §3.5 says both are
  in place. A governance MR: `protected_override` resting on this approval, an impact map of the
  guard, CTO and platform at opus. Not in it: `stop_gate.py`'s FAST_GATES."

  Taken here as implementation. The check is self-contained: it copies the SHAPE of
  `declare_missing_columns.py`'s helpers and imports nothing from it — a CI gate must not hang
  on a generator script's module constants (`IN_SCOPE_DIRS` there is three layers; this check
  covers every model yml in every layer, because a staging or base yml can list a dead column
  too). A `parent.field` struct entry is matched by its full path, not by its parent: the
  issue line's "or, for a `parent.field` struct entry, its parent" rested on the premise that
  the catalogue holds only the parent, and the prod catalogue disproves it — dbt-bigquery 1.7.2's
  catalogue macro reads `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`, and `mart_head_to_head` holds
  `recent_meetings` plus its five leaf paths (which is how `declare_missing_columns.py` wrote
  the dotted entries into `shared.yml` in the first place). Full-path matching is strictly
  stronger (a leaf present implies its parent present) and catches a mistyped or removed field;
  the parent rule would have let one through. A yml block for a model with no `.sql` on disk is
  a finding (`dbt parse` only warns on it, and `check_description_hygiene.py` walks the `.sql`
  files, so nothing else catches it). Models match by name, columns case-insensitively, as
  `declare_missing_columns.py` and BigQuery do. Floors `MIN_MODELS = 50` and
  `MIN_LISTED_COLUMNS = 800`, well under 101 and 1,915 and well over zero, the
  `check_relationships_coverage.py` precedent. The partial-catalogue abort is the same rule as
  `declare_missing_columns.py`'s: any model on disk absent from the catalogue refuses the run.
  The relationships CI line gets no new pytest pin: the issue names one pin, for the projection
  line, and the relationships gate is already run on the real tree by its own pytest in
  `test:python` on every MR; the CI line is listed in the `validate-local` table. No new
  mechanism beyond the issue line; no recurring cost.

decisions_reserved:
  - none: the MR D line on #109 names every file and both CI lines; the measurement shows the
    first run green; his merge is the ruling.

done_when:
  - `python scripts/check_yml_vs_projection.py --catalog <prod catalogue>` exits 0 with the census `101 models, 1915 listed columns, 0 absent`; against the dev `dbt_project/target/catalog.json` it exits 1 with the partial-catalogue abort.
  - Mutation: one fake column entry added to a model yml → exit 1 naming the yml, model and column; restored → 0. `MIN_LISTED_COLUMNS` raised above 1,915 → exit 1.
  - `python -m pytest tests/test_check_yml_vs_projection.py tests/test_persist_docs_policy.py tests/test_governance_hooks.py -q` green; the new pin seen RED against the pre-edit CI file first.
  - `python scripts/check_relationships_coverage.py` exits 0 on the branch.
  - The validate-local gates green; `data:build:mr` green on the MR.

amendments:
  - 2026-09-21: + `scripts/check_relationships_coverage.py`, + `tests/test_check_relationships_coverage.py` — authority: the standing rule that a correction replaces the old text (CLAUDE.md "Reasoning lives in git"; memory "corrections replace"), and the issue's How ("§3.5 says both are in place"); content: docstring prose only — the script's module docstring and its real-tree test's docstring both say the `validate:governance` line is "a separate governance change" / "until the script has its own line", which this MR makes false. No code moves in either file.
