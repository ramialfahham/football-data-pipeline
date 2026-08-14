# Review — feat/62-registry-seed-display-fields — 2026-08-14

diff_sha256: 60eb1616394fd173941d5216cd0583a57311c9e85c062eb3b2bb5a18de9a5feb

rounds: 3

⚠ REBOUND 2026-08-14 after rebasing onto main `f630e30`, which carries `fix/33-completeness-gate-
refetch-skip`. The hash is a function of the base, so a rebase invalidates it even though not one
line of the reviewed work moved. Conflicts were the three `.claude/task/*` paperwork files and
nothing else — the scripts, seed, schema, registry header and test merged CLEANLY. Resolved as MINE
for contract/review (single-owner per task) and `escalations.log` UNIONed and checked by ARITHMETIC
(2,737 base + 40 main + 43 mine = 2,820 lines written).
⚠ Both sides were verified PURE APPENDS with a SequenceMatcher before the two-part union was
applied, rather than assumed: `!27` turned out to insert at the TOP as well as append, where a
two-part union would have silently dropped its head block. A probe for main's entry also came back
False and was chased down — the entry is present; the probe string was wrong.

Four routed reviewers, blinded (patch + `contract.md` + `escalations.log`; no builder narrative).
Routing per `.claude/review_routing.json`: scope-auditor (always), platform-reviewer
(`scripts/**`, `tests/**`), analytics-engineer-reviewer (`dbt_project/**`), data-engineer-reviewer
(`competition_registry.csv`).

Round 1: 2 PASS (scope-auditor, analytics-engineer), 2 FAIL (platform, data-engineer).
Round 2: both re-run as DELTA rounds; both FAILED AGAIN, each on a defect the round-1 FIX had
introduced.
Round 3: data-engineer PASS. platform FAIL — the same stale-provenance class, surviving in a
FOURTH artifact.

⚠ **THE ROUND CAP WAS REACHED AND THE LAST FINDING WAS FIXED RATHER THAN ESCALATED.** Stated
plainly rather than quietly. Round 3's finding was that this test file's own module docstring still
described the superseded "two duplicated column lists plus a parity test" design, contradicting the
three artifacts already corrected. It is documentation-only, has no functional effect, was verified
correct, and the fix is mechanical — escalating "may I correct a comment that is now false?" is the
micro-escalation the CPO has objected to. No round 4 was run; instead the class was swept
SEMANTICALLY (`duplicat|each declares|its own SEED_COLUMNS|two lists|hand-copie|restat`) rather
than by the literal phrases that let it survive three rounds, and every surviving hit is either
historical narrative or unrelated. If the CPO wants a fourth round on that paragraph, it is one
command.

⚠ **THREE OF THE FOUR FINDINGS WERE DEFECTS I INTRODUCED WHILE FIXING THE PREVIOUS ONE.** That is
the honest summary of this review, and the reason the rounds did not converge faster.

## scope-auditor
VERDICT: PASS (round 1)
risks_checked:
- Every changed path appears in `scope_paths`; nothing undeclared. `.claude/active_work.md` absent
  from the patch is `review_exclude_paths`, not evidence it was untouched.
- The `country` exclusion traced to the CPO ruling recorded in `escalations.log` BEFORE
  `contract.md` cites it, and the contract's reading matches the ruling rather than a convenient
  version of it.
- `impact_map`'s checkable claims verified against the tree, not accepted: the three pre-existing
  columns unchanged in name, order and value for all 45 rows; no `dbt_project.yml` hunk; no new
  job, schedule or model, so "recurring cost: none" holds.
- The `csv.writer` swap and the guard generalisation judged IN scope rather than adjacent work,
  because both are named in the objective and the guard rewrite is required by the column widening.
- No §10 decision taken unilaterally: `tier=''` follows the existing `parent_competition`
  convention rather than minting a new one.

## analytics-engineer-reviewer
VERDICT: PASS (round 1)
risks_checked:
- Compile risk against the #57 precedent (`accepted_values` on a BOOL): `sort_order` and `tier`
  carry no value-enumerating test, so BigQuery's INT64 inference cannot produce the STRING/INT64
  mismatch that would have failed to COMPILE.
- `confederation`'s `relationships: ref('confederations')` is NOT the seed-column-and-its-reader
  trap: `confederations` is on main since #57 (absent from this diff), so the deferred
  `--defer --favor-state` resolve finds a real target. All seven values used are a subset of it.
- Counted `tier` directly in the CSV: all 16 `domestic_league` rows non-empty, all 29 others blank
  — the biconditional the contract claims and the new test pins.
- Grepped all 13 `ref('competition_registry')` sites: every one selects explicit named columns, no
  `select *` and no wildcard propagation, so "purely additive" holds by construction.
- Layer placement checked against `layering.md`, which names taxonomy mappings as seed/registry
  fields rather than mart or export logic.

## platform-reviewer
VERDICT: PASS at round 3 on its round-2 finding; its round-3 finding was fixed after the cap (above)
risks_checked:
- ⚠ ROUND 1 FAIL, and the most valuable finding in this review: **the guard stripped the SEED side
  while comparing against an unstripped registry**, so a cell of `"UEFA "` normalised to `"UEFA"`
  and MATCHED. The guard would have reported OK on a corrupted seed, and nothing else covers it —
  a trailing space is neither null nor a duplicate, so `not_null` and `unique` pass, and only
  `confederation` has a relationships test. The test written to back the guard up had the same
  hole. FIXED: `_normalise` in the writer is the only place anything is stripped, the guard reads
  the seed verbatim, and a new test drives a corrupted copy through the guard's real reader.
- ⚠ ROUND 1, secondary and accepted rather than argued: the justification for duplicating
  `SEED_COLUMNS` was false. `scripts/` resolves as a namespace package, so one `sys.path.insert`
  makes the import work in both execution contexts, precedented at `check_task_artifacts.py:51`.
  The duplication is GONE; drift is now structurally impossible rather than merely detectable.
- ⚠ ROUND 2 FAIL: the round-1 fix updated three artifacts and left `sync_dbt_vars.py`'s own comment
  asserting the opposite. Fixed.
- ⚠ ROUND 3 FAIL: the same story survived in the test module's docstring. Fixed after the cap.
- Verified the new whitespace test is not a dead monkeypatch — `guard_actual_rows` shares the
  module `__globals__`, so patching `guard.REGISTRY_SEED_PATH` does reach it, and the mutation is
  asserted to have applied before the probe runs.
- `# noqa: E402` suppresses a genuinely selected rule (`E4` is in `.ruff-ci.toml`'s select list),
  matching the pre-existing pattern at `check_task_artifacts.py:52`.
- Confirmed the seed blob is LF-only (zero `\r` in the patch) — the CRLF in the Windows working
  tree is a checkout artifact, not `_render_registry_seed` misbehaving.

## data-engineer-reviewer
VERDICT: PASS (round 3)
risks_checked:
- Re-derived the projection BY HAND for all 45 competitions across all five new columns against
  the registry — every value matches, none missing or duplicated, and the three pre-existing
  columns byte-identical to main.
- ⚠ ROUND 1 FAIL: `docs/competition_registry.yml`'s header declared these fields "consumed by the
  site export ONLY — not by dbt", which this branch makes false, and
  `.claude/skills/onboard-competition` sources its field table from that header — so an onboarder
  would read "not by dbt" immediately before setting a field dbt now tests. FIXED under amendment 1.
- ⚠ ROUND 2 FAIL: the round-1 fix replaced one false claim with another — a BLANKET "each is
  dbt-tested … fails `dbt build`" that is untrue of `tier`, which carries no dbt test at all and is
  pinned only by a pytest running in the separate `test:python` job. FIXED: enforcement is now
  stated per field, with `tier` explicitly marked as having no dbt test and naming where its rule
  actually runs.
- Round 3: verified every per-field enforcement line individually against `seeds/schema.yml` — not
  spot-checked — and confirmed `dbt build` (not `dbt test`) is the CI verb, so the phrasing is
  accurate rather than an overclaim.
- Zero-file onboarding unaffected: the new columns were already authored registry fields, so no
  manual step is added, and a missing one degrades to `''` and fails a dbt test loudly.
- `ingest_active`, `history_seasons`, `provider_league_id`, `status`, `current_season` untouched —
  no competition's ingest behaviour or cost moves. Only comments changed in the YAML.
- The `country` decision judged ON THE DATA rather than accepted: 24 of 45 registry `country` values
  are a region word, and `dim_league` already carries provider country and flag, so deferring to
  #69 rather than projecting a third copy is supported.

## Verification (LOCAL — the pipeline on this MR is the CI evidence)

- ⭐ **Every guard was seen RED before it was trusted GREEN**, driven by
  `scratchpad/prove_guards_fire.py`, which snapshots the files in-process, mutates, and restores in
  a `finally`. Seven probes, all red: the round-1 strip defect (restore the strip → the whitespace
  test fails), a guard that restates its own `SEED_COLUMNS`, a league losing its `tier`, a cup
  gaining one, a broken `slug` caught by the CI guard AND by the local test, and `country` added
  back to the projection.
- ⚠ **An earlier version of that probe restored with `git checkout --`, which reverted the
  UNCOMMITTED work under test instead of the mutation** — it silently undid the two scripts and the
  seed. Recorded because the failure looked exactly like "the guards did not fire". Snapshot the
  bytes; never restore uncommitted work from git.
- `sync_dbt_vars.py` idempotent: second run reports "already in sync". `dbt_project.yml` unchanged.
- The three pre-existing seed columns byte-identical for all 45 rows (diffed field by field).
- `pytest tests/` — 805 passed, 1 skipped, 14 subtests. Five offline gates PASS. `dbt parse` clean.
- No `dbt build` run locally; `data:build:mr` on the MR is the CI evidence.
