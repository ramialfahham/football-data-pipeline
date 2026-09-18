# Task contract — #109, step 1: the connective testing rules written into `engineering_standards.md` §3

objective: >
  The dbt testing policy has per-layer minimums and no connective rules (#109). The census posted
  on #109 on 2026-09-18 measured the gaps; the draft posted beneath it wrote the rules; the CPO read
  the draft and said "open the MR". This MR puts those rules into `engineering_standards.md` §3 as
  §3.1–§3.5 beneath the existing minimums: the column-class rule for what a column's tests are,
  the rate rule (one definition, the gate derived from the inputs, a range test on every rate, a
  guard generated from the catalogue), the severity question, `store_failures` on singular tests,
  and the four mechanisms that hold the rules. The severity guideline's three example rows become
  worked examples of the question. Text only: no model, test, script or seed changes — those are
  #109's steps 2 and 3, and #111.

refs: >
  #109 ("dbt test strategy: per-layer minimums exist, the connective rules do not", filed by the
  CPO 2026-09-11; the census and the draft as comments of 2026-09-18); #111 (the formula test);
  `docs/metric_layer.md` "Incomplete data is not calculated" (the rule §3.2 builds on, not
  restates); the nightly of 2026-09-18 (`momentum_team_shots_on_goal_pct_in_range`, 14 rows,
  `mart_matchday_insights` skipped) as the instance §3.2 names.

scope_paths:
  - dbt_project/docs/engineering_standards.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The rules as drafted on #109 and read by the CPO before "open the MR" (2026-09-18, in chat):
  the four column classes and their tests; "a `not_null` is added because the description says
  the column is never NULL"; a listed column without a description is a defect; a rate's gate is
  derived from its inputs, one definition per rate, a range test on every rate, the catalogue
  guard under #111; severity by the one question "would a fan see a wrong number"; `store_failures`
  on every singular test; the four holding mechanisms named as work to come, not built here. The
  merge is the approval of the rule text — a rule extension is the CPO's class (§10) and the MR
  head says so under Locked files.

decisions_reserved:
  - The form window's seven player-derived rates average over the games that carry the player feed, against `metric_layer.md`'s rule. The draft says the existing rule decides it (they go to "—" on partial coverage) unless the CPO says otherwise; this MR changes no model, so nothing is decided here — the fix or the rule change is step 2's.
  - Whether the pipeline's 941 `error` tests are re-graded by the new severity question is step 2's audit, not this text.

done_when:
  - `engineering_standards.md` §3 carries §3.1–§3.5 as drafted; the hard rule and the per-layer minimums unchanged; the severity table kept as worked examples under the question.
  - `python -m pytest tests/test_governance_doc_parity.py tests/test_persist_docs_policy.py -q` green; `python scripts/check_description_hygiene.py` green; the fast gates green.
  - The MR open against `main`, its head linking the census and the draft on #109 and naming the two reserved items.

amendments: (none)
