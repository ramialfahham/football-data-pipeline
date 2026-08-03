# Review — feat/898-cause3-per-team-completeness — 2026-08-03

branch: feat/898-cause3-per-team-completeness
diff_sha256: f60efe46f041433e2988e87fe27c3c77ad1b4da7cdc7c63550bebf23cbb9359a

rounds: 5
rounds_cap_override: CPO authorised rounds 4 and 5 explicitly after the cap of 3 was reached and the
  open finding was brought to them per §2. Both overrides were granted on the same basis: every
  round-3-onward FAIL was a false FACTUAL CLAIM in `contract.md` prose, never a code defect. The
  CODE passed `data-engineer-reviewer` and `platform-reviewer` in rounds 3 AND 4 and has not changed
  since round 3. Round 5 ran `scope-auditor` ALONE and deliberately, because the only delta since
  the specialists' PASS was the `impact_map` rewrite, which is that reviewer's remit and nobody
  else's; re-running the specialists would have re-reviewed a byte-identical `completeness.py` for a
  third time.

# Required reviewer set from `.claude/review_routing.json` for the staged paths: `ingestion/**`
# routes `data-engineer-reviewer`, `tests/**` routes `platform-reviewer`, `scope-auditor` is
# always-on. NOT artifact-exempt, because `contract.md` is never artifact-exempt (F10/#409).
#
# ROUND HISTORY. Round 1: scope PASS, data-engineer FAIL (PLAYERS had no table-existence guard;
# empty `blocks` rendered invalid `FROM ()`), platform FAIL (same guard, plus the tests could not
# reach the bug and the expected-set fix sat in untested orchestrator code). Round 2: scope PASS,
# data-engineer FAIL (snapshot timestamps not paired per league, which made a real miss look
# covered), platform FAIL (same). Round 3: both specialists PASS, scope FAIL (argument miscount).
# Round 4: both specialists PASS, scope FAIL (snapshot reader count). Round 5: scope PASS.
#
# SEVEN false factual claims in `contract.md` were found across those rounds. None reached the code.
# Root cause and its durable fix are recorded in `escalations.log` and filed as #904.

## scope-auditor
VERDICT: PASS
risks_checked:
- Rewritten `impact_map` claims verified against code signatures and call sites, not against the
  builder's verification output: the two new keyword arguments on `evaluate_completeness_outcome`,
  the one on `persist_fixture_statistics_missing`, the new returned key, all four new functions and
  their production call sites, the three snapshot readers, the four tables read, and that
  `RAW_APIF_TEAMS` is genuinely never queried.
- Dropping per-test-file call-site counts judged a LEGITIMATE CORRECTION, not a narrowing that hides
  blast radius: those counts are brittle by construction, carry zero blast-radius value because a
  test is not a production consumer, and the one test whose assertion SHAPE breaks is named by
  exception rather than omitted.
- `_ts_in_list` checker FAIL independently confirmed as a false positive: the only remaining
  mentions sit in `amendments:`, recording the corrected error rather than asserting a live fact.
- Amendment scope: no permission widened, no `scope_paths` entry added, no decision taken. Only
  `contract.md` and `escalations.log` changed since round 4.
- Guard integrity: nothing loosened, and a guard was ADDED (`_raw_table_exists`). The exact-equality
  assertion was extended with the new key, never relaxed to a subset.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round-4 delta confirmed limited to one corrected sentence, verified against
  `evaluate_completeness_outcome`'s actual signature.
- Both round-1 defects fixed at the root: all four tables existence-checked (three via
  `_latest_snapshot_timestamps`'s `NotFound`, PLAYERS via `_raw_table_exists`), and the all-absent
  case skips the query rather than emitting `FROM ()`. Each path has a dedicated test.
- The round-2 dangerous-direction defect fixed: `_snapshot_block` and the PLAYERS `season_pairs`
  both pair `league_code` to its own timestamp and season rather than using independent `IN (...)`
  filters, so a stale row can no longer make a real miss look covered.
- Kill-switch inheritance: `stagnant_per_team_gaps` computed inside `evaluate_completeness_outcome`,
  after the `report["skipped"]` early return and before `fail_on_incomplete()`, so both operator
  escape hatches suppress the failure while reporting survives.
- Orchestrator wiring: prior counts read before this run's are persisted, so no self-comparison;
  `per_team_missing_by_league_entity` gates PLAYERS/SQUADS/TRANSFERS and never COACHES.
- Cost figure re-derived independently from the code shape (two-step maxima-then-literal reads,
  `RAW_APIF_TEAMS` absent from the query set) and matches the measured 0.931 GiB per run.
- Downstream lineage claim evidenced: no dbt or scripts reference to the snapshot table.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The seven tests for `per_team_expectations_from_results` genuinely exercise it, and each would
  fail under either previously-proven-wrong design. `max(seasons_list)` cross-checked as
  byte-identical to the real production call site in `competition_runner.py`.
- Poll-mode exclusion is real, not decorative: `results` structurally excludes poll-mode
  competitions in unchanged orchestrator code, and the league codes asserted absent were confirmed
  to be real registry entries.
- No leftovers from either rejected design: `_ts_in_list` gone from all source, and
  `RAW_APIF_TEAMS` survives only in comments explaining why it is not read.
- Global state isolated: fresh fakes per test, read-only class-level fixtures, `monkeypatch` for env.
  `per_team_expectations_from_results` copies `team_ids` rather than aliasing the loader's set.
- Re-run and first-run safe: prior read precedes persist, and a crash before the persist leaves the
  next run comparing against the last successfully persisted state.
- On the CPO's question about a mechanical guard: the countable sub-class is checkable and would
  have caught most instances; the semantic ones stay prose-level. Filed as #904.

## escalations
(none)
