# Review — feat/description-coverage-wire-blocks — 2026-08-23

diff_sha256: 2746131ae46aeff72e769d5940bb9d6611c6f80eed9389bf089ba2151f1b984e

rounds: 4

rounds_cap_override: CPO, 2026-08-23, at the round-3 cap. analytics-engineer-reviewer had FAILed three consecutive rounds, finding six wrong `league_code` sites in total. Rather than loop, the open findings were taken to him as `docs/working_agreement.md` requires, and his answer was "drop league_code, ship the 146". Round 4 therefore reviews a materially smaller and different diff — 49 fewer wired columns and a narrowed gate rule — not a re-run of round 3's contents. The decision and its reasoning are in `contract.md`'s `amendments:`.

## scope-auditor
VERDICT: PASS
risks_checked:
- Verified the staging/base layer-scope decision against the plan file itself rather than the
  contract's summary of it, and confirmed it is a different question from the 2026-08-21 coverage
  ruling, which governs authoring rather than reuse.
- Verified the new gate rule against the literal text of `engineering_standards.md` §2 Form
  bullet 2 — it mechanises the existing standard rather than extending it.
- Checked `scope_paths` against every file in the diff across all four rounds; no file entered the
  diff that was not already declared, and no protected path or credential-shaped content appears.
- Ruled on whether the repeated content corrections needed a contract amendment before round 4:
  they did not, being generator accuracy rather than a §10 decision, and `done_when` requires "a
  docs block" rather than a specific one.
- Confirmed the false "the reviewer's three is the complete set" line was deleted at its own site
  in `escalations.log` rather than contradicted below, matching the precedent that file already
  set for correcting its own durable record.
- ROUND 4, on the amendment: read the `_shared_block_coverage` / `_ambiguous_names` code rather
  than the amendment's description, and confirmed the skip is narrowly bounded to names that
  already reference more than one block, with the count printed unconditionally on every run.
- ROUND 4, on the bundling: independently checked that the gate narrowing was FORCED by the scope
  answer, since the gate scans the whole repo rather than the diff, so "ship the 146, drop the 49"
  cannot be honoured while leaving the previous rule in place. Judged disclosed, not smuggled.
- ROUND 4, on the override: confirmed it quotes the CPO verbatim and follows the escalation
  protocol — stop, escalate, record — rather than being used to push a repeat of round 3.
- ROUND 4, on the guard: judged the narrowing to be "narrow it to where it still holds" rather
  than a deleted assertion, since the excluded case is one where the old rule mandated a guess.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: every changed line is a column-only addition inside the five layers; no SQL
  touched; `IN_SCOPE_DIRS` matches the CPO's documented layer scope.
- Description-hygiene gate compatibility: read `check_description_hygiene.py` end to end rather
  than trusting the contract, confirming a bare column name cannot turn the gate red.
- Catalogue governance, competition-agnosticism, seeds and config, consumption layer, same-window
  ratios: none touched by this diff.
- ROUNDS 1-3 WERE FAILS, and each was correct. Six columns were pointed at the wrong one of
  `league_code`'s two meanings: three staging sites in round 1, the coach family in round 2, and
  `base_apif__teams_global` in round 3, the last by a different mechanism from the others. Each
  was verified against the model's own description, its base-layer SQL, and the downstream
  consumer that drops the column.
- Round 3 also established that the "complete set" claim in `escalations.log` was unsupported.
- ROUND 4: confirmed `league_code` is absent from every wired site, all 49 blanks intact, and the
  pre-existing 99 wired plus 2 provenance sites untouched.
- ROUND 4: tested each of the seven remaining wired names individually against the same defect
  class. They are deterministic surrogate keys or inherently provenance concepts, so no
  ingest-order collapse can give them a second meaning. Specifically checked the one structurally
  analogous site — `base_apif__league_entity` retaining `season_api_year` through a latest-row
  collapse — and found it protected, because `dim_league` drops that column downstream, which is
  exactly the protection `base_apif__teams_global` lacked. No seventh instance.

## platform-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 WAS A FAIL and it was right: the per-file commit used a truncating open, so a crash
  mid-write would have left a tracked yml half-written, which `_verify` cannot see because it
  compares two in-memory strings and has already returned. Fixed with temp file, `fsync` and
  `os.replace`, and the fix re-read from the patch rather than taken on trust.
- The `.tmp` suffix sits outside `_declared()`'s `*.yml` glob, checked against the actual glob
  semantics, so a crash leftover cannot be misread as a second declaration of every model.
- The bounded `DOC_BLOCK_RE` traced by hand against the stray-opener repro, confirming it cannot
  match past a second opener; block discovery restricted to `models/` confirmed against dbt's
  unset `docs-paths`, and confirmed to drop no live block.
- Round 1's maintainability finding about the two hand-copied regexes closed by a behaviour parity
  test pinning agreement AND correctness, rather than by coupling a gate to a generator.
- Re-run safety and idempotency: planning is recomputed from disk each run, so a partial run is
  resumable; a second run reports nothing to do and exits non-zero.
- Line-ending preservation and the mixed-ending refusal traced against `core.autocrlf=true` and
  `.gitattributes`, covered by two tests seen red before the fix.
- Append-only re-verified on every round by grepping the whole patch for deletion lines: zero in
  any yml file, all deletions confined to `contract.md` and the two scripts.
- ROUND 2 raised, and ROUND 4 resolved, that the diff was not reproducible by a fresh tool run.
  Traced the reproducibility claim by hand against the unchanged generator logic and could not
  break it, then independently counted the additions in the real yml files: exactly 146, with zero
  non-provenance `league_code` wirings anywhere outside a test fixture.
- ROUND 4: the gate's `_ambiguous_names` compared line by line against the generator's and found
  identical; the skip ordering and the placement of the "NOT POLICED" block traced for
  correctness, confirming it fires on exactly the runs where a silent exemption would matter.
- ROUND 4: the three new tests confirmed red-provable by tracing what each does if its code is
  reverted, and the autouse fixture checked so an unrelated floor cannot mask them.
- Dependencies, credentials, CI and hosting surfaces: none touched in any round.

## escalations
(none)
