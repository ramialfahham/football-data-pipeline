# Review — feat/description-coverage-objects — 2026-08-21

> #82 MR1: the object-level half of description coverage. 12 objects that had no description get
> one, and the gate learns to require it.
>
> ⚠ EVERY VERDICT BELOW WAS RETURNED BY THE NAMED REVIEWER. None is written on their behalf.
> One reviewer FAILED round 1 on a genuinely false description I had written, and that FAIL is
> recorded here rather than smoothed over.
>
> ⚠ THE REVIEW SURVIVED A CRASH. Claude Code died with two reviews in flight. Both were RESUMED
> rather than restarted, and the resume was only legitimate because the diff had not moved: the
> binding hash was still `6a8ab2a5…` afterwards, byte-identical to when they started. They then
> re-reviewed the round-2 delta on top.

diff_sha256: a22937b64491e605911fd5ce57cce378b7c3129c45d2f7d6ded3feed67b8e483

rounds: 2

> ⚠ REBOUND TWICE, and NEITHER time because anything reviewed changed. Reviewed value `336230f4…`,
> then `585202db…` after #84 merged, now `a22937b6…` after #84's follow-up fix merged. Each move was
> the merge-base advancing, the same mechanism recorded on `!88` and `!89`.
> ⛔ FOUR TIMES IN ONE DAY, AND THE CODE WAS NEVER INVOLVED ONCE. Every collision was the same six
> task artifacts: `contract.md`, `review.md`, `acceptance_evidence.md` and `review_input.patch` are
> rewritten wholesale by every branch, and `escalations.log` + `active_work.md` are appended by both
> sides. Any two branches open at the same time collide on them regardless of what they change.
> That is structural and worth a mechanism, not a fifth manual merge.
>
> VERIFIED RATHER THAN ASSERTED, because a rebind is not a licence to change content. Every file
> the hash covers was diffed against the pre-rebase commit `18c888b` and is byte-IDENTICAL:
> `sources.yml`, `int_team_market_value.yml`, `check_description_hygiene.py`,
> `test_description_hygiene.py` and `contract.md`. So the three verdicts below cover exactly the
> content being committed.
>
> THE CONFLICT WAS ENTIRELY TASK ARTIFACTS. #84 touched `cleanup_orphan_relations.py` and its
> tests; this branch touched the description gate and two yml files. Zero code overlap. What
> collided is the structural problem that every branch rewrites `contract.md`, `review.md`,
> `acceptance_evidence.md` and the patch, while `escalations.log` and `active_work.md` are appended
> by both. Resolved as: this task's own artifacts taken whole, `escalations.log` = #84's version
> PLUS this entry PLUS this branch's correction to the 2026-08-20 osmosis ruling re-applied, and
> `active_work.md` rebuilt from #84's handover so its orphan-cleanup section survives alongside
> #82's state.

## scope-auditor
VERDICT: PASS
> Round 1 PASS, then re-confirmed at round 2 on the amended contract.
risks_checked:
- Checked every file in the diff against `scope_paths`, including the two excluded from the patch
  by `review_exclude_paths` and read from disk instead — no drift.
- Checked the `escalations.log` edit that DELETES a false ruling from the 2026-08-20 entry:
  confirmed it removed exactly the clause claiming the CPO "explicitly" rejected dbt-osmosis and
  nothing else, left a marked and cross-referenced correction at the same site, and is therefore a
  correction rather than a silent rewrite of history.
- Checked both `decisions_taken` quotes against the log verbatim — exact quotes, not paraphrases
  strengthened past what the CPO said, which is the specific defect being corrected.
- SURFACED MY FALSE FLAG: noted `docs/data_contract.md` already carries `RAW_APIF_LEAGUES`. I
  verified further (line 65 plus two endpoint tables) and WITHDREW the claim.
- Round 2: checked both amendment entries honestly attribute discovery to reviewers rather than to
  me, and that the withdrawal does not try to salvage the original claim.
- ⚠ ONE OBSERVATION, EXPLICITLY NOT A FINDING, RECORDED BECAUSE IT IS RIGHT: the withdrawn flag
  now sits in `decisions_reserved`, which `docs/working_agreement.md` §2 defines as CPO-class OPEN
  questions; a withdrawn claim is not one. Not moved — `contract.md` is overwritten by the next
  task while three verdicts were already bound to this diff, so a third round for a bullet's
  location was not proportionate. The reasoning is in `escalations.log` so the trade is visible.

## analytics-engineer-reviewer
VERDICT: PASS
> FAILED round 1. The finding was real, verified independently, and fixed. PASS at round 2.
risks_checked:
- ROUND 1 FAIL, CORRECT: the `raw_apif_fixture_details` description I wrote ended "the newest is
  the fullest". False. `docs/data_contract.md:134` says both versions are kept deliberately and a
  retry "can come back richer in one section and poorer in another", with fixture 1564795 yielding
  27 events of which indices 17-26 survive only in the payload the retry would have replaced;
  `base_apif__fixture_events.sql:25` dedups per `(league_code, fixture_id, event_index)`, which is
  only necessary because the newest row is NOT the fullest. A reader following my sentence would
  take the newest row and silently lose events.
- Round 2: re-verified the rewritten text against the contract and all three `base_apif__fixture_*`
  dedup grains — now accurate, and it correctly names the three real grains.
- Ruled on the §2 question I raised rather than letting me self-certify it: "versions have to be
  resolved per entity" states a property of the DATA, names no model, asserts no exclusivity, and
  will not go stale when a model is added, so it does not cross the downstream-consumer ban.
- Verified all 11 source descriptions against the staging SQL, the loaders and the data contract:
  the grain claims (whole-league versus one `(team, season)` versus team subset versus one
  fixture), append-only versus ACCUMULATING, and every stated limit — transfers returning an
  intra-league move twice, squads listing a player twice, coach stints with a club name but no id,
  statistics absent for uncovered competitions. All confirmed real.
- Verified `int_team__market_value_latest`'s description against its SQL, and that its emptiness
  claim is UPSTREAM state rather than a named-consumer claim.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Traced the shared-parse refactor's central claim and CONFIRMED it: `_collect` and
  `_object_coverage` still extract independently from the shared parse, so a broken `_walk` still
  collapses `found` toward zero and still trips `MIN_DESCRIPTIONS`. The performance fix cost no
  correctness.
- Confirmed unparseable-file handling moved intact into `_parse_ymls()`, is still checked FIRST,
  still names the file and its exception class, and still fails closed.
- Judged the fixture's floor-lowering legitimate rather than a hollowing: counted exactly the five
  pre-existing green-expecting tests that required it, confirmed both floors run at REAL values in
  dedicated tests, and confirmed from the diff that no assertion was deleted or narrowed.
- Confirmed the file walk cannot pick up macros, tests, snapshots or analyses, because none nest
  under `models/`.
- Confirmed the check ordering (unparseable, then coverage, then the floor) cannot mask a genuinely
  broken extraction.
- RAISED THE DUPLICATE GLOB, which I adopted: the success line globbed the trees a third time and
  dropped the `dbt_packages/` exclusion. Round 2 confirmed the `_on_disk()` fix leaves only one
  definition with two call sites, and — a point I had NOT realised — that the old seed glob had no
  exclusion in the ENFORCEMENT path either, so the fix closed a real asymmetry rather than a
  cosmetic one. Also confirmed the new seed filter cannot drop a legitimate seed.
- Independently derived the test count (25 definitions, one parametrised over 14) = 38, matching
  the reported run rather than taking it on trust.

## escalations
(none)

<!--
No blinded escalation was raised out of review. Four CPO rulings govern this MR and were all taken
in chat BEFORE the work, recorded in `.claude/task/escalations.log` under
`2026-08-21 feat/description-coverage-objects`: every column no exception; no thin filler, our
definitions alongside the provider's, defined upstream and reused downstream; docs blocks kept only
with a mechanism that applies them consistently; and no dbt-osmosis.

⚠ One of those rulings only exists because the CPO CORRECTED THIS LOG. It previously recorded that
he had "explicitly" rejected dbt-osmosis on 2026-08-20. He had not — his answer was the two words
"Docs blocks", and the rejection was the writer's reasoning wrapped around it. That false clause is
deleted at its own site in this diff. He then rejected osmosis on 2026-08-21 on its merits, which
is a different and later decision.
-->
