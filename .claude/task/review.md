# Review — ci/scope-triggers-and-restore-ingest-lock — 2026-08-08

> Wave 1 items 2 and 4 of GitLab #33 (item 3 WITHDRAWN at round 2 — see below). Required reviewer
> set for the staged paths: `scope-auditor` (always), `cto-reviewer` + `platform-reviewer`
> (`.gitlab-ci.yml`, a guard path, so both at the OPUS floor), `platform-reviewer` again via
> `tests/**`. `analytics-engineer-reviewer` was required at rounds 1-2 while
> `dbt_project/selectors.yml` was in scope; its round-2 PASS is recorded because that file's
> withdrawal is the substance of this MR's largest change, and its verdict is what confirms the
> withdrawal is complete.

diff_sha256: dea66f86806e624620399d2c31f56b0235685fc3783c7dea8183d9052d4c2548

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 PASS, round 2 FAIL, round 3 PASS. The round-1 PASS included an entry accepting the
  contract's claim that item 3's coverage delta was zero and "evidenced not hand-waved". That
  acceptance was MISTAKEN — the evidence counted test nodes and not whether a failing test blocks a
  write — and the three specialists caught what this reviewer did not. Recorded rather than
  quietly dropped.
- Round 2 FAIL, and it was correct: the amendment added `tests/test_governance_hooks.py` to
  `scope_paths` justified only by "no new authority is needed to do LESS", which covers the item-3
  withdrawal bundled into the same entry but not the addition. `docs/working_agreement.md:76-77`
  requires each scope extension to record CPO authority, with on-point precedent in
  `escalations.log` (2026-06-23, `feat/player-per90-metrics`) where an equivalent stale-comment fix
  was held to need the CPO.
- Round 3: verified the new `escalations.log` STANDING RULE entry (lines 1635-1675) is a genuine
  CPO §10 ruling and not builder self-authorisation — states the rule verbatim, names four
  explicit limits (no other edit to the file, no behaviour change, no widening the objective,
  protected paths still need `protected_override` + `impact_map`), records the counter-argument
  against itself, names the round-2 FAIL and the 2026-06-23 precedent as its origin, and
  explicitly declines to fold itself into `docs/working_agreement.md` §2 in this branch.
- Verified the APPLICATION against the raw diff rather than the contract's prose:
  `tests/test_governance_hooks.py` has exactly one hunk, `*data_paths` -> `*data_paths_prod` inside
  a docstring, no other line touched, no assertion or logic or config value changed. Exactly what
  the rule permits and nothing more.
- Verified `amendments:` now splits the round-2 reduction and the round-3 extension into two
  independently authorised entries, repairing the bundling defect the round-2 FAIL named.
- Checked the standing rule for general-purpose scope-escape risk: bound to the same task's own
  approved change, to the reference only, with no behaviour change, and it still requires a written
  amendment. Tight enough to hold.
- Scope: the diff touches exactly `scope_paths` plus the two authority artifacts. Item 3's
  withdrawal is reserved back to the CPO on #33 with a recommendation rather than silently dropped,
  which is §11-correct.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, and it was correct. Excluding `test_type:singular` from the `staging`/`downstream`
  selectors converted 25 DQ tests from in-DAG write-blocking gates into post-publication reports:
  `dbt build` compiles with `add_test_edges=True` (`dbt/task/build.py:134`) and marks dependents of
  a failed test as skipped (`MARK_DEPENDENT_ERRORS_STATUSES`, `build.py:80`), so a `severity=error`
  singular test failing inside the build stops the models below it from being written. The contract
  declared "coverage delta EXACTLY ZERO" and "GUARD WEAKENED? NO"; both were wrong on the axis that
  matters. Ruled an authority finding, not a platform one, because the standing #33 approval covers
  a PLAN and `escalations.log` states that limit in terms.
- Round 2: verified the withdrawal independently rather than from the brief. Read
  `dbt_project/selectors.yml` in full — `staging` and `downstream` carry no `test_type` exclusion,
  `downstream`'s only exclude is `tag: freshness_check`, i.e. main's shape. Confirmed its absence
  from the patch is real evidence and not the known `review_exclude_paths` false positive by
  checking it against `review_routing.json`.
- Verified the withdrawal was TOTAL, not relocated: the only new content at the
  `dbt build --selector` lines is a comment; `data:build:mr`'s DQ line still runs the full singular
  suite; no `--exclude test_type:singular`, no tag-based narrowing anywhere in the file.
- Item 3's future routed to the right authority — `decisions_reserved` now carries "may the prod
  warehouse be materialised over a severity=error DQ failure" as a §10 question for the CPO on #33,
  with a recommendation attached, which §11 permits.
- Guard authority: `protected_override` cites the 2026-08-08 entry, read at `escalations.log`
  lines 1581-1633; it exists on the durable record and names items 2/3/4 as protected-path edits.
  `impact_map` present and non-placeholder. Withdrawing an item needs no new authority.
- Threshold re-check on the delta: recurring cost reduced, not increased; no new mechanism (the new
  test module uses `yaml`, already imported by `tests/test_governance_hooks.py`); no dependency
  line in the diff; no credential, token or permission widening; item 4 restores a guard.
- Recorded a deliberate deviation: round 1 was a FAIL, not a PASS, so the delta-review framing is
  outside the letter of that rule. Accepted because the delta moves strictly downward and the
  material claims were re-verified against the files rather than taken from the brief.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL with five findings; all five addressed and each re-verified at round 2.
- Finding 1 (DQ gate inverted) and finding 3 (`_selectors_excluding_singular()` failing open):
  verified NOT from the patch alone — the "absence from `review_input.patch` is not evidence a file
  is unedited" trap applies — but by reading `dbt_project/selectors.yml` byte-for-byte against a
  tree that predates this branch. Identical. The parsing function is gone with item 3.
- Finding 2 (the lock guard ignored `variables:`): `_declared_variables()` now collects the global
  block plus `.get("variables")` on every top-level mapping. Since PyYAML flattens `<<:` merge keys
  and `default:`/`.python`/`.data_build_base`/each job are all top-level mappings, every route that
  reaches a job's environment through a `variables:` mapping is scanned.
- Finding 4 (item 2 unpinned): the new `test_the_prod_trigger_still_covers_every_dbt_compile_input`
  asserts both directions and is not vacuous — reverting the split makes both anchors `None` and
  both `isinstance` assertions fail; both lists are asserted non-empty.
- Finding 5 (stale docstring): fixed; repo-wide grep for `data_paths` leaves hits only in
  `.gitlab-ci.yml`, the two test files, the contract, the patch, and `.claude/active_work.md`
  (the handover, unedited here and out of remit).
- Two residual evasion routes on the lock guard, stated rather than failed on: `script:` given as a
  scalar string rather than a list would make the loop iterate characters and match nothing, and
  the `rules: - if: … variables:` conditional form is not walked. Both require rewriting an existing
  multi-line block into an unusual shape; the realistic reintroduction routes — the inline
  assignment and a job/global `variables:` entry, the one `orchestrator.py:95` actually instructs —
  are both caught.
- Blind spot named on the new item-2 test: it asserts anchor CONTENTS, not that the jobs reference
  those anchors. Repointing `data:build:main`'s `changes:` at an inline list would orphan
  `.data_paths_prod` and leave both assertions green. Today's wiring is correct
  (`*data_paths_mr` on `data:build:mr`, `*data_paths_prod` on `data:build:main`, checked by hand),
  so this is future-drift exposure, not a present defect.
- Fail direction: the new pins run in `test:python`, which carries no `changes:` filter, so they
  fire on every MR and every push to main and redden the pipeline — fail CLOSED, correct for a CI
  backstop. `yaml.safe_load` raises on an unknown tag rather than skipping, also closed.
- Re-run and interruption safety for item 4: a job killed mid-ingest leaves a lease that
  self-expires (`ingestion_lock.py:83`, 180 minutes) and `data:build:mr`'s 2h timeout sits inside
  that window, so a stuck bootstrap surfaces as a loud 409/exit-2, never a silent skip.
- `.ruff-ci.toml` selects `E4,E7,E9,F`; the new module has no unused imports or shadowed names, so
  `lint:python` is unaffected. Both new test names are unique in `tests/`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, and it was correct, on the same defect as `cto-reviewer` reached independently: in
  `dbt build` tests are edges in the DAG, so excluding singular tests from the two prod selectors
  moved the DQ gate from "block publication" to "report after publication" for 24 tests in
  `downstream` and 1 in `staging`, several on high-fan-out nodes (`fct_fixture`,
  `base_apif__fixtures_next`, `dim_team`). Also flagged that `engineering_standards.md:126`
  prescribes `dbt build --selector staging` as the local pre-commit gate and would have lost its
  singular test silently.
- Round 2: confirmed the withdrawal by reading `dbt_project/selectors.yml` on the branch against a
  reference copy — identical, no `test_type:singular` exclusion in either selector. The mechanism
  behind the round-1 FAIL no longer exists on this branch, and is gone rather than relocated.
- Confirmed no DQ enforcement change survives anywhere else: the three dbt invocations in
  `data:build:main` match the pre-change copy line-for-line (only comments inserted); no
  `allow_failure`, no `--warn-error`, no severity override added to any data job;
  `dbt_project/dbt_project.yml` unchanged including all `+materialized` layer settings; no seed,
  model, schema.yml, macro or singular test file in the diff. `engineering_standards.md` therefore
  needs no change and is untouched.
- Checked `.data_paths_prod` against the full set of inputs that determine compiled SQL and the DQ
  test population: `models/**`, `macros/**`, `seeds/**`, `snapshots/**`, `dbt_project/tests/**`,
  `dbt_project/*.yml` and `docs/competition_registry.yml` are all retained — so a new singular
  test, a metric-catalogue seed row, a selector edit, or a league added by registry entry alone
  (the zero-file rule) all still trigger a prod rebuild. The five dropped entries define no dbt
  node.
- The `requirements.txt` exposure (a dbt version bump not rebuilding prod) is real, is disclosed in
  both the contract and the file comment, and changes WHEN a recompile happens rather than what any
  model computes — not a layer-contract defect.
- No model, mart, metric, seed or `scripts/export_*.py` content in the delta, so layer placement,
  catalogue governance, same-window and consumption-layer rules have no subject here.

## escalations
- question: >
    The round-2 amendment added `tests/test_governance_hooks.py` to `scope_paths` for a one-word
    docstring fix — it names the `*data_paths` anchor this MR renames. `scope-auditor` FAILed
    because §2 requires each scope extension to record CPO authority and the amendment's stated
    authority ("no new authority is needed to do LESS") covered only the item-3 withdrawal bundled
    into the same entry. Grant authority for this one file, or decide the general case: is
    repairing a reference that an approved change itself broke part of that change, or a scope
    extension? Recommended the general case, because every rename breaks references and Waves 2
    and 3 will raise it again.
  CPO ANSWER: >
    Do as recommended — settle the class. Standing rule adopted 2026-08-08 and recorded in
    `.claude/task/escalations.log` under "STANDING RULE: a reference broken by an approved change
    is part of that change": "Updating a reference that an approved change itself breaks is part of
    that change, not a scope extension — provided the update is confined to the reference and
    changes no behaviour." Limits, protected-path carve-out and counter-argument are in that entry.
