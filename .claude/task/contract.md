# Task contract — Wave 1 items 2 and 4 (#33): CI trigger scoping and the ingest lock

> Branch `ci/scope-triggers-and-restore-ingest-lock` from `main` (`72a6a69`), in the worktree
> `D:\Projects\fdp-pipeline`. `.gitlab-ci.yml` is a PROTECTED path, so this carries BOTH
> `protected_override` AND an `impact_map`. Routes to `cto-reviewer` + `platform-reviewer` at the
> OPUS floor, plus the always-on `scope-auditor`. No `site_v2/src/`, so no `acceptance_criteria`.
>
> ⚠ **Item 3 was in this contract and is WITHDRAWN at review round 2.** See "Item 3, withdrawn"
> below. The title, objective and scope have shrunk accordingly; this MR now does strictly less
> than round 1 proposed.

objective: >
  Wave 1 items 2 and 4 of GitLab issue #33, bundled because both edit `.gitlab-ci.yml` and
  separate MRs would conflict line-for-line.

  (2) TRIGGER SCOPING. Split the single `*data_paths` anchor into an MR anchor and a prod anchor,
  and drop five entries from the PROD one — `.gitlab-ci.yml`, `scripts/check_*.py`,
  `scripts/data_trust_*.py`, `requirements.txt`, `ingestion/**/*`. None can change a compiled dbt
  artifact, and each currently triggers a FULL prod warehouse build on push to main.

  (4) THE INGEST LOCK — correctness, not cost, and #33 calls it the most serious finding in the
  assessment. Remove `API_FOOTBALL_SKIP_INGEST_LOCK=1` from all three places it appears.
  `settings.py:31` defaults the raw dataset to `raw` and `API_FOOTBALL_BIGQUERY_DATASET` is set
  nowhere in CI, so `data:build:mr` writes PRODUCTION raw from an unmerged branch, with the lock
  disabled, from a different `resource_group` than the prod writers.
  `docs/operations_guide.md:149` already forbids it: "Local debugging only; never production."

  Plus the residual #33 attaches to a CUT item: correct the false comment calling
  `get_new_league_codes.py` "a cheap BigQuery metadata lookup". It is
  `SELECT DISTINCT league_code FROM ...` (`scripts/get_new_league_codes.py:50`) — a billed column
  scan. #33 cut bounding it with a predicate (the #892 hazard) and kept only the comment fix.

  CONSULTED BEFORE BUILDING (§2 norm): enumerated the singular-test sets with `dbt ls` rather than
  trusting #33's counts; read `ingestion_lock.py` and `main.py` to confirm a held lease cannot pass
  silently; read `operations_guide.md` for the standing rule item 4 restores. What that consultation
  MISSED is recorded under "Item 3, withdrawn" — it was the right method applied to the wrong
  question.

refs: >
  GitLab issue #33, Wave 1 items 2 and 4 (+ the `get_new_league_codes.py` comment residual from the
  "Cut, deliberately" section). Item 3 withdrawn — see below. Follows MR !23 (Gate 0.2 + items
  5/6), merged 2026-08-08 as `72a6a69`. Related: #892, #667.

protected_override: >
  CPO approval of 2026-08-08, recorded durably in `.claude/task/escalations.log`, entry
  "2026-08-08 — GitLab #33: the CPO approves the whole pipeline cost/scalability plan, in advance"
  — which is ON `main` as of `72a6a69`, so a blinded reviewer can verify it independently of this
  branch. That entry names items 2/3/4 explicitly as protected-path edits covered by the approval.
  Verbatim: "Every item in #33's Gate 0, Wave 1, Wave 2 and Wave 3 is APPROVED, including the two
  that would normally be CPO-class: raw merge-on-write with the raw_archive backup first (item 8),
  and staging materialised as a table (item 9). The CPO said 'yes' to all three headline decisions
  on 2026-08-08 and then approved the full recommendation set."
  The same instruction supplies the §1 Confirm: "Work through the plan without checking in on
  anything #33 already settles."
  Note the entry's own stated limit, which round 2 proved load-bearing: "It records an approval of
  a PLAN. It does not pre-approve whatever a builder later decides an item means."

scope_paths:
  - .gitlab-ci.yml
  - tests/test_ci_data_job_invariants.py
  - tests/test_governance_hooks.py

impact_map: >
  This is a PROTECTED path, so the trace is of the GUARD, not of table lineage.

  WHAT FIRES IT. `.gitlab-ci.yml` is the entire CI definition — 5 stages, 11 jobs. Every pipeline
  on every branch, MR, web dispatch and (once item 7 lands) schedule is governed by it. Its blast
  radius is every future push to this repo.

  WHAT THE EDITED REGIONS CONTROL, and every consumer of each:
  - The `.data_paths` anchor had exactly TWO consumers, verified by
    `grep -n "data_paths" .gitlab-ci.yml`: the `changes:` clause of `data:build:mr` and that of
    `data:build:main`. A third hit is a PROSE comment naming the anchor, updated here so it does
    not go stale; a fourth lives in `tests/test_governance_hooks.py` and is updated for the same
    reason. That is the whole reference set.
  - `API_FOOTBALL_SKIP_INGEST_LOCK=1` appeared three times — once in `data:build:mr`, twice in
    `data:build:main` (the `RUN_INGEST` branch and the bootstrap branch). It appears in no other
    file except `ingestion/api_football/ingestion_lock.py:29` (the reader) and
    `docs/operations_guide.md:149` (the rule forbidding it), neither of which is edited.

  WHAT STOPS BEING ENFORCED IF THIS IS WRONG:
  - Item 2 wrong -> either prod stops rebuilding when it should (a stale warehouse, which is also
    the `--defer --favor-state` baseline for every MR build, so the staleness would propagate into
    MR validation with nothing red), or nothing changes. Two mitigations: the anchor gates only the
    `push`-to-main clause, so the `web` + `when: manual` full build is always one button away; and
    `tests/test_ci_data_job_invariants.py` now asserts the property in BOTH directions —
    `.data_paths_prod` must cover every dbt compile input, and must not exceed `.data_paths_mr`.
    The single anchor used to make that drift structurally impossible; splitting it traded the
    guarantee for a comment, so the test re-establishes it.
  - Item 4 wrong -> an ingest could run while another holds the lease. It cannot fail silently:
    `acquire_ingest_lock` returning False makes `_load_api_football` return 409, and `main.py:55-56`
    turns 409 into `SystemExit(2)`, so the job goes RED. Removing the flag converts a silent
    concurrent-write hazard into a loud failure. It does NOT stop `data:build:mr` writing prod raw —
    that is #33 item 13, still open and deliberately out of scope.

  WHAT HAPPENS ON FAILURE OF THIS CHANGE ITSELF. A YAML error fails every job immediately and
  visibly; there is no fail-open mode. The MR's own pipeline exercises both edits: it re-parses the
  file, and `data:build:mr` runs under the new MR anchor with the lock restored.

  DEPLOY ORDER / SHARED WAREHOUSE. No warehouse object changes. No model, seed, macro or test SQL
  is touched, so `state:modified+` selects nothing new and prod's tables are untouched. The nightly
  is unreachable today (no GitLab schedule; that is item 7), so nothing to sequence around.

  BLAST RADIUS on data: none. No mart, no number, no displayed value changes, and — after the
  round-2 withdrawal of item 3 — no change whatsoever to which DQ tests run, when they run, or what
  they block.

decisions_taken: >
  AUTHORITY: see `protected_override` — the durable record is the 2026-08-08 entry in
  `.claude/task/escalations.log`, on `main` at `72a6a69`, independently checkable by a blinded
  reviewer. Quoting a ruling only in this file is not recording it (`scope-auditor` FAILed !23
  round 1 for exactly that).

  ITEM 3, WITHDRAWN AT REVIEW ROUND 2 — the most important thing in this contract.
  Round 1 implemented it and all three specialist reviewers independently FAILed it on the same
  defect. They were right, and I verified the mechanism in the installed dbt before accepting it:
      dbt/task/build.py:134      compiler.compile(self.manifest, add_test_edges=True)
      dbt/task/build.py:80       MARK_DEPENDENT_ERRORS_STATUSES = [NodeStatus.Error, NodeStatus.Fail]
      dbt/compilation.py:203-206 add_test_edges makes an upstream test a dependency of the node
  So inside `dbt build`, a `severity: error` test that fails SKIPS the models below it, and prod
  keeps its last good data. Excluding singular tests from the `staging`/`downstream` selectors left
  the same 28 assertions running on the trailing `dbt test` line — but by then the entire warehouse
  has been materialised into the bare prod datasets. Several of the 25 sit on high-fan-out nodes
  (`fct_fixture`, `base_apif__fixtures_next`, `dim_team`). The test COUNT was unchanged; the GATE
  was removed.
  My round-1 contract asserted "Coverage delta is EXACTLY ZERO … What changes is 25 duplicate
  executions, nothing else" and "GUARD WEAKENED? NO". Both were wrong, and wrong in the way this
  repo logs repeatedly: I measured the thing that was easy to count (how many tests execute) and
  not the property that mattered (whether a failure blocks the write). `dbt ls` cannot see that
  difference, so a correct-looking measurement certified a regression.
  The alternative de-duplication — keep the tests in the builds, narrow the trailing line to the
  three seed-only catalogue tests — was considered and ALSO rejected: naming that set durably needs
  a tag, and a future singular test whose author forgets the tag would then never run on the prod
  build at all. That trades a cheap duplicate for a silent hole, which is the worse bargain.
  So the duplication STAYS. It cost 9.7s of a 7m29s prod build (measured on MR !23's pipeline).
  #33's item 3 is not implementable as specified (its mechanism is a no-op — `dbt` ignores a CLI
  `--exclude` under `--selector`; measured: `dbt ls --selector downstream --resource-type test`
  returns 770 with and without it, while the same flag against `--select` drops 870 to 840), and the
  obvious alternative inverts a DQ gate. It needs its own scoped decision, not a rushed round-2
  patch, and it is reported back to the CPO on #33 rather than quietly dropped.

  THRESHOLD DECLARATIONS (no gate parses this field; an omission is a defect, not an oversight).
  - GUARD WEAKENED? NO — and unlike round 1 this is now true rather than asserted. With item 3
    withdrawn, `dbt_project/selectors.yml` is byte-identical to `main` (`git diff main --
    dbt_project/selectors.yml` is empty), so nothing about DQ enforcement moves. Item 4 RESTORES a
    guard CI had disabled. Item 2 narrows when an expensive job runs, only for paths that cannot
    change a compiled dbt artifact, and adds a test that pins the narrowing in both directions.
  - RECURRING COST: reduced. Item 2 removes prod builds triggered by paths that cannot change dbt
    output. No new job, schedule or cadence. Item 7 is Wave 2 and NOT in this MR.
  - NEW MECHANISM: none in CI. One new test file, declared below.

  SCOPE JUDGEMENTS I made rather than escalated (all below §10):
  - I ADDED `tests/test_ci_data_job_invariants.py`, which #33 does not ask for. `platform-reviewer`'s
    standing hunt item is "does a test pin this changed behaviour", and for item 2 the honest
    round-1 answer was no — it was the item with the silent-failure mode and it was the one left
    unpinned. Two assertions, both proven to fail (see done_when).
  - I updated two PROSE references to the renamed anchor — the comment at the top of
    `.gitlab-ci.yml` and a docstring in `tests/test_governance_hooks.py:2040`. A comment naming a
    nonexistent anchor is the stale-reference failure this repo logs repeatedly, and round 1 fixed
    one copy while missing the other, which is the same half-correction pattern.
  - I did NOT touch `docs/operations_guide.md:149`. It already states the rule correctly; item 4
    makes CI comply with it.
  - I did NOT remove the bootstrap ingest from `data:build:mr` (#33 item 13, "Later, still open").

  RESIDUAL RISK IN ITEM 2, flagged rather than silently accepted. Dropping `requirements.txt` from
  the PROD anchor means a dbt version bump merged to main will not by itself rebuild prod, and a
  dbt upgrade can change compiled SQL. Prod would serve old-compiled tables until the next model
  change or (once item 7 exists) the nightly. #33 approved the drop explicitly and the exposure is
  small and self-healing, so I implemented it as specified rather than narrowing it on my own
  judgement — but the reviewer should see it named, and the reasoning is also in the file itself.

decisions_reserved:
  - #33 ITEM 3's FUTURE. Whether to pursue the de-duplication at all, and if so by which mechanism,
    now that the specified one is a proven no-op and the obvious alternative inverts a DQ gate. My
    recommendation, for the CPO to accept or reject on #33: DROP IT. The measured prize is ~9.7s of
    test time per prod build; the cheapest safe mechanism introduces a silent-hole class. This is
    reserved rather than decided because "may the prod warehouse be materialised over a
    severity=error DQ failure" is a §10 question and `cto-reviewer` said so explicitly.
  - #33 item 13 — taking the bootstrap ingest out of `data:build:mr` entirely. Item 4 restores the
    lock; it does not stop the write. Whether an MR pipeline may write production raw at all is §10.
  - #33 item 12 — scoping `data:build:main` to `state:modified+` via a moving `prod-built` tag.
    Blocked on item 7 and not attempted.
  - Whether `.gitlab-ci.yml` should stay in the MR anchor. Kept deliberately: a change to CI must
    revalidate CI. #33 only asks for it to leave the PROD anchor.

done_when:
  - `.gitlab-ci.yml` parses (`yaml.safe_load`), and the MR pipeline accepts it.
  - No `.gitlab-ci.yml` SCRIPT LINE **or `variables:` ENTRY** sets `API_FOOTBALL_SKIP_INGEST_LOCK`.
    Check by parsing, not grepping: `grep -c` over the file returns 1, because the comment block
    documenting the fix names the flag. A text grep would flag the documentation as the defect.
  - `git diff main -- dbt_project/selectors.yml` is EMPTY — item 3 fully withdrawn, no DQ
    enforcement change anywhere in this MR.
  - `python -m pytest tests/test_ci_data_job_invariants.py -q` exit code read DIRECTLY; green.
  - EVERY assertion proven load-bearing by breaking the thing and watching it go red, then
    reverting. DONE, all four, and two of them mattered:
      · re-added the flag as a script line       -> FAILED naming the line. Reverted; green.
      · set the flag via a `variables:` mapping  -> FAILED naming `data:build:mr.API_FOOTBALL_
        SKIP_INGEST_LOCK`. This hole was REAL and was found by `platform-reviewer` at round 1: the
        round-1 test read only script text, and `orchestrator.py:95` literally tells an operator to
        set that variable. Reverted; green.
      · removed `dbt_project/models/**/*` from `.data_paths_prod` -> FAILED naming it. Reverted.
      · added a path to `.data_paths_prod` absent from `.data_paths_mr` -> FAILED naming it.
        Reverted.
    A round-1 assertion that did NOT survive this step is recorded here rather than deleted
    quietly: the item-3 pairing test PASSED while its subject was broken, because it searched every
    job's script and `data:build:mr` has a singular-test line of its own. It was rewritten to be
    per-job, then removed entirely with item 3.
  - `python -m pytest tests/ -q` exit code read directly; green, and no lower than the 665 tests on
    `main` plus the new ones.
  - CI green on the MR, with `data:build:mr` showing "All leagues already have raw tables —
    skipping bootstrap ingest", i.e. no ingest runs with or without the lock.

amendments:
  - 2026-08-08 (round 1): + `dbt_project/selectors.yml` — for item 3. SUPERSEDED by the round-2
    amendment below; the file is now byte-identical to `main` and has left `scope_paths`.
  - 2026-08-08 (round 2, part A — a scope REDUCTION): item 3 WITHDRAWN and
    `dbt_project/selectors.yml` reverted and removed from `scope_paths`. Authority: none needed to
    do LESS — the round-2 change touches strictly less than round 1 did, which is the direction an
    amendment is always free to move. The withdrawal is forced by three independent reviewer FAILs,
    verified against dbt's own source before being accepted.
  - 2026-08-08 (round 3, part B — a scope EXTENSION, and it needed its own authority):
    + `tests/test_governance_hooks.py`, for a ONE-WORD docstring fix — line 2040 names the
    `*data_paths` anchor that item 2 renames. Authority: the CPO's standing ruling of 2026-08-08,
    recorded in `.claude/task/escalations.log` as "STANDING RULE: a reference broken by an approved
    change is part of that change" — "Updating a reference that an approved change itself breaks is
    part of that change, not a scope extension — provided the update is confined to the reference
    and changes no behaviour." This edit is exactly that: one identifier in a docstring, no
    behaviour touched, and the only edit made to that file.
    WHY PART B IS SEPARATE FROM PART A, since bundling them is what went wrong. Round 2 wrote both
    moves under one "Authority:" line reading "no new authority is needed to do LESS". That
    justified the reduction and silently carried the addition along with it. `scope-auditor` FAILed
    it, correctly, citing §2 ("each recording the CPO authority") and on-point precedent from
    2026-06-23 where an equivalent stale-comment fix was held to need the CPO. The CPO then chose
    to settle the CLASS rather than this instance, because every rename breaks references and Waves
    2 and 3 will raise the same question again.
    Both parts written on a clean tree, riding INTO the reviewed commit rather than arriving later
    (F10/F11, #409).
