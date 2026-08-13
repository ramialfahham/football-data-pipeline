# Review — feat/57-competition-taxonomy-seed — 2026-08-12

diff_sha256: 1ccafbfc690df9fc7c9467ff341c9c036b1b6c8f340556ee09f023aae94251f3

rounds: 3

⚠ `diff_sha256` above is the CUMULATIVE branch number over `base...HEAD`, and since **#63** it
hashes `git diff --raw` — CONTENT IDENTITY (mode, blob SHAs, status, path), not rendered patch
text. `--staged-hash` now produces exactly this number on any commit; both were verified equal
here (`1ccafbfc…`, 1,459 bytes). The older warning that `--staged-hash` was "the wrong number on a
second commit" described the pre-#63 implementation and no longer applies.

⚠ REBOUND 2026-08-13 after rebasing onto main `b4b2414`, which carries **!35/#63**. TWO reasons the
old number is dead: the base moved, and the ALGORITHM changed. The verdicts below stand — the
rebase touched only the four `.claude/task/*` paperwork files, resolved as MINE for
contract/review/review_input (single-owner), and `escalations.log` UNIONed and checked by
ARITHMETIC (base 289,386 + main's #63 4,392 + this branch's #57 7,224 = 301,002, written 301,002),
never by eye. No code, seed, model or doc content moved in the rebase.

Four routed reviewers, blinded (patch + contract.md + escalations.log; no builder narrative).
Routing per `.claude/review_routing.json`: scope-auditor (always), analytics-engineer-reviewer
(`dbt_project/**`), data-engineer-reviewer (`docs/competition_registry.yml`,
`dbt_project/seeds/competition_registry.csv`), platform-reviewer (`tests/**`).

Round 1: 2 PASS, 2 FAIL. Round 2: 3 PASS, 1 FAIL. Round 3: platform only, PASS.
⚠ Both round-1 failures were real defects that this contract's own `done_when` would NOT have
caught. Round 3 re-ran ONE reviewer rather than the panel — the only one whose findings were acted
on after its verdict (CPO in session: correct the false lines and stop, rather than re-review prose
with all four).

## scope-auditor
VERDICT: PASS
risks_checked:
- Checked every file in the diff against `scope_paths` (base list + amendment 1) — no out-of-scope
  file. Amendment 1's cited authority ("I would include the three -> do it") verified independently
  against the escalations.log entry rather than taken from the contract.
- Traced each substantive `docs/metrics_context_model.md` change — the knockout after-window
  removal, per-team phase detection, the section 8.4 table deletion — against escalations.log
  rulings 3 to 6 line by line; each edit traces to a verbatim ruling and none exceeds it.
- Checked all four `decisions_reserved` items against the diff: `display_group` untouched,
  `world_championship` unrenamed, no mart built, no registry fields projected. None silently decided.
- Checked the four threshold declarations (new mechanism / recurring cost / guard loosened /
  shipped numbers) against what the diff actually does — all four hold.
- ROUND 1 FAIL, fixed: `decisions_reserved` reserved the English label copy for the CPO while the
  same diff shipped all 21 strings as non-null, unique, test-enforced content. Moved to
  `decisions_taken` item 9, which now names which 5 of 14 category strings are CPO-attributable,
  which 9 plus all 7 confederation labels are builder-authored, flags the two judgement calls
  (`FIFA -> World`, normalising CONCACAF), and records that no per-string approval was obtained.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: no model, macro or SQL file touched; `dbt_project/docs/layering.md:339` places
  taxonomy mappings in seeds/registry fields, which is where this landed.
- Rename join-integrity: `continental_club -> continental_cup` and the `CWC` re-type applied
  identically on both sides, backed by the existing `relationships` test
  (`dbt_project/seeds/schema.yml`), so a one-sided rename fails immediately. Repo-wide grep found
  no live SQL/TS/Python branching on the old literal.
- New-column typing: confirmed `single_country`'s `true`/`false` literals load as native BigQuery
  BOOL under dbt seed inference with no `column_types` override, and that `not_null` alone is
  correct — matching the `metric_catalogue.lower_is_better` precedent.
- ROUND 1 FAIL, fixed: the first draft put `accepted_values: ["true","false"]` on that BOOL column.
  BigQuery has no implicit BOOL/STRING coercion, so the test would not merely fail — it would fail
  to COMPILE on the first `dbt build`. Removed, `not_null` retained, reasoning recorded in the
  column description so it is not re-added.
- ROUND 2, both corrected: the impact_map subtotal read "14 intermediate + 21 marts" where the
  pasted list is 18 + 17 (total 35 and the list itself were right); and a `done_when` grep claim
  was not true of the whole tree.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Re-derived the single-source lockstep rather than accepting it: all 45 registry rows diffed
  against the 45 seed rows, the 8 re-typed competitions matching exactly, with `provider_league_id`,
  `ingest_active`, `history_seasons` and `parent_competition` unmoved on every one.
- Confirmed `dbt_project.yml` is correctly untouched — its active-code list derives from `status`,
  which no row changed — consistent with `sync_dbt_vars.py`'s logic.
- Confirmed `entity_type` stays `club` across the rename and the re-type, so no club/national
  classification moves downstream.
- Confirmed no `ingestion/**` path appears and no new `provider_league_id` is introduced, so the
  onboarding cost and provider-identity rules have no surface here.
- Surfaced `site_v2/src/data/teams/33.json` — 9 stale `continental_club` values in a committed
  sample export, missed by the builder's original sweep which excluded `.json`. Judged inert
  (`types.ts:185` types the field as a bare `string | null`, nothing branches on it) and out of
  scope; now disclosed in `done_when` and carried to #62's export repoint.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Traced the new `test_display_group_of_type_covers_the_renamed_and_new_types` against
  `_display_group_of_type`, which reads the committed seed from disk with no mocking, and confirmed
  its assertions would go RED on a revert of the rename — genuine coverage of the changed behaviour.
- Read both guard scripts in full: `check_competition_type_seed.py` fails on any registry type
  missing from the seed; `check_registry_var_sync.py` compares
  `(league_code, competition_type, parent_competition)` symmetrically. Both `sys.exit(1)` on drift
  with no exception swallowing, and both are wired into `.gitlab-ci.yml`.
- Checked every `done_when` claim against the real files: both seed shapes, no blanks in any new
  column, `confederations.csv` keys equal to the registry header enum AND to the `confederation`
  values actually used across the registry, and the corrected repo-wide grep result.
- ROUND 2 FAIL finding 1, fixed: the edited `build_nav` fixture pinned nothing — `build_nav()`
  never branches on `competition_type`, so reverting the whole rename left it green. The new test
  above replaces that as the pin, and was proved RED against a reconstructed pre-#57 seed rather
  than trusted on a green run (`scratchpad/prove_seed_test_fails.py`).
- ROUND 2 FAIL finding 2, DEFERRED not fixed: `confederations.csv` has no guard tying it to the
  registry's `confederation` values, where `competition_type` has one. All 44 registry values match
  the 7 seed rows today, so it is a coverage gap rather than a break. CPO decision in session: the
  seed is read by nothing, so the guard has nothing to protect until #62 builds its consumer, and
  `scripts/**` is outside these scope_paths. Recorded as an explicit gap in `done_when`.

## Post-review increment — stated rather than hidden

Three changes post-date the verdicts above and are covered by this hash but by no reviewer:

1. **Two corrections to `contract.md`** flagged by analytics-engineer in round 2 — the impact_map
   subtotal (14+21 to 18+17) and a `done_when` grep claim that was not true of the whole tree.
   CPO decision in session: correct the false lines and stop, rather than re-review prose with the
   full panel. Neither touches `scope_paths` nor adds work.
2. **contract.md amendment 2** — adds `.claude/active_work.md` to `scope_paths`. Not a CPO ruling
   but a standing `docs/working_agreement.md` §3 requirement, enforced by the post-commit workflow
   hook. Recorded as an amendment rather than edited quietly, because the contract gate is right
   that an out-of-scope edit is drift however routine it feels.
3. **The handover rewrite.** Its header claimed "NOTHING IN FLIGHT — no open MRs" while `!27` and
   `!33` are both open; a fresh session handed only that file would have re-scoped from scratch.
   ⚠ Capped at 16,000 CHARACTERS and sitting at 15,971, so this was a TRADE, not an addition: the
   audit section is compressed to its durable lesson plus the GitLab #30 pointer, and the cost
   section to its measured baseline plus the traps. Final size 15,951.

None of the three touches code, seeds, models or any model-facing path.

## Verification (LOCAL at review time)

`check_competition_type_seed` OK · `check_registry_var_sync` OK · `check_layer_contract` passed ·
`check_copy_gate` OK · `check_task_artifacts` OK · `dbt parse` clean · `pytest tests/` 764 passed
1 skipped (42 in the touched file after the new test) · both seeds parse at their declared shapes ·
`sync_dbt_vars.py` idempotent on a second run with `dbt_project.yml` unchanged.

⚠ **The above is LOCAL evidence and is never CI evidence.** CI was unrunnable at review time (zero
minutes, account-wide); a self-hosted runner has since restored it, so the pipeline on this MR is
the CI evidence — read the job log, not the colour.
