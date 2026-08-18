# Review — feat/shared-competition-order — 2026-08-18

diff_sha256: 6f1c42db62095806e0ba2ae3f88c695124247890c632ad130cadba31699de6a8

rounds: 4

rounds_cap_override: The cap exists to stop a builder grinding a contested finding. That did not
happen here — the one contested finding (the layer classification of the matchday selection) was
NOT ground on: after analytics-engineer-reviewer FAILed it twice I escalated it to the CPO per §10,
who ruled "ship as-is, register the gap" (GAP-32 + `escalations.log` RULING 3). Rounds 3 and 4 carry
ZERO open findings. Round 4 exists solely because round 3 surfaced a regression I introduced and
missed — removing `group_upcoming_fixtures`'s `limit` broke two tests in a second file, which I did
not catch because I ran one test file instead of the suite — and platform-reviewer's round-1 PASS
predated three substantive changes in its own remit, so reusing it would have been dishonest. The
alternative to round 4 was shipping on a stale PASS with a self-inflicted regression fixed but
unreviewed. CPO instruction for the session: "get it done, but really done, not your liar version
of done."

## scope-auditor
VERDICT: PASS
risks_checked:
- Escalation mechanics (§10/§11): `escalations.log` RULING 3 records the premise, both conflicting positions (the reviewer's two FAILs with reasoning, and the builder's counter that the same WHERE clause has carried an unflagged window filter since #367), and the CPO's answer as a direct quote rather than paraphrased into something stronger.
- Reviewer-not-overruled distinction: both RULING 3 and GAP-32 state explicitly that this is "a decision to PROCEED, not a finding that the reviewer was wrong" — the dispute is preserved for inheritance, not resolved in the builder's favour.
- Scope: every delta-touched path is in `contract.md`'s `scope_paths`; the two mid-task amendments (`site_v2/src/data/fixtures/*.json` + `.gitignore`; then `tests/test_export_landing.py`) are both recorded, the first as the documented "refresh as a set" procedure the build gate enforced, the second as fixing the builder's own breakage.
- Test deletion checked against the never-loosen-a-guard rule: the removed assertion pinned string text, not behaviour, so no guard was weakened.
- Under-cover decisions: checked GAP-32 and the SQL comment for scope creep beyond the ruled question — only the WHERE-clause placement is addressed; no other mechanism, metric or naming change rides along. The 57-fixture worst case is left genuinely unbounded in code, matching `decisions_reserved`.
- Secrets sweep: no credential-shaped content; no new recurring cost.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- GAP-32 checked against my own round-1/round-2 finding, the #846 precedent and the builder's counter — recorded faithfully, with the ruling correctly framed as "proceed, not vindicated"; no softening, misattribution or strawman.
- `escalations.log` RULING 3 checked against the same — consistent content, no drift from the register entry.
- Proposed disposition (serve the matchday as a warehouse fact; the hero's direct `core.fct_fixture` read is a separate, already-flagged defect that must be fixed with it) is technically coherent and complete for a future implementer.
- Deleted placement test confirmed to be a source-grep (`"min(fixture_date)" in inspect.getsource(...)`), not a behavioural assertion; the two remaining tests cover the function's real behaviour with no coverage regression.
- `fixture_date` (`stg_apif__fixtures_next.sql:27`) is `DATE(kickoff_datetime)` in UTC, so the field switch from the deleted Python filter introduces no timezone divergence.
- Objection ON RECORD but not re-litigated per the ruling: in my view SQL window-selection authored in `export_site_data.py` remains consumption-layer logic under `layering.md`. Settled by CPO ruling 2026-08-18, not reopened.
- Found outside my judging scope and flagged for follow-up (since fixed): `tests/test_export_landing.py` still called `group_upcoming_fixtures(..., limit=...)`, a parameter this branch removed.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Reworked `test_group_upcoming_fixtures_caps_nothing`: still discriminates, and the strong boundary case (13 fixtures vs the retired 12-cap) is separately pinned by `test_hero_grouping_truncates_nothing` — between the two the no-truncation property is genuinely exercised, not asserted by name.
- Reworked `..._omits_a_competition_with_no_fixture_in_the_window`: traced the property it now exercises — a competition in `_META` but absent from the fixture list must not produce a phantom group. That is a real branch of the `groups.setdefault` logic, and the docstring matches the assertions.
- Coverage hole from the deleted placement test: grepped `tests/` — no test exercised `fetch_landing_payload`'s SQL before this delta either (the deleted one asserted placement, never SQL correctness), so no behavioural coverage was lost; consistent with the file's documented "no BigQuery, fabricated rows only" boundary.
- The CTE rewrite: `fixture_date` is selected inside the CTE and referenced in the outer WHERE without being in the outer SELECT — valid BigQuery Standard SQL; no consumer reads it, so dropping it from the projection is correct. All 7 projected columns match what the shaping helpers consume.
- Signature fallout: grepped every call site repo-wide — no stray `limit=` kwarg remains anywhere, and no leftover reference to `_HERO_FIXTURE_LIMIT`, `_kickoff_date` or `_earliest_kickoff_date` in `scripts/` or `tests/`.
- Re-run safety: the new CTE is a pure read gated on `current_date()`, idempotent on re-run, introducing no partial-write state.
- Earlier round, still standing: test discrimination verified by inspection for all 7 new tests (6 add real discrimination, 1 redundant but not decorative and not misrepresented); `compareCompetitions` byte-unchanged so the competitions page cannot regress; the `.gitignore` allowlist matches the committed fixture files 1:1; no CI job invokes the changed export path.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round-1 FAIL closed: `10_home.md` §10's stale "next 12 fixtures by kickoff" is struck and replaced, and agrees with §5(1) and `99_gaps_register.md` GAP-02.
- Swept for a fourth stale instance across `docs/`, `site_v2/src/` and the repo root — no remaining place states the retired count as current; all hits are struck-through history, the labelled measurement table, or false-positive CSS pixel values.
- The new "OPEN, BOTH DIRECTIONS" note checked against the committed `landing.json`: 2 groups, 4 fixtures, one date — matches its claim exactly, and it explicitly does NOT close the product question ("whether a 4-match day is an acceptable home page is nonetheless a PRODUCT question and is not decided"). Fair characterisation, not a rationalisation.
- `HeroFixtures.astro`'s corrected header now matches behaviour: it states the component DOES sort, and `const ordered = orderUpcomingGroups(groups)` confirms it. The old "sorts nothing" claim is gone.
- `region_rank` traced end-to-end: served from `mart_competition_index`, never derived from the registry's `confederation`; used only inside the comparator, never rendered as text.
- Rendered evidence is from built output (group order read from `dist/{de,en,fi}/index.html`, geometry measured live, a caught-and-fixed dead-link regression), not a source-only claim.
- No new user-facing copy and no new metric on any display surface.

## escalations
- question: Is selecting "the next matchday" inside `scripts/export_site_data.py` — first as a Python `min()`, then as `where fixture_date = (select min(fixture_date) from upcoming)` in the export's own SQL — forbidden window selection under `layering.md` §Consumption layer, or an allowed filter? analytics-engineer-reviewer FAILed twice, citing the #846 precedent where an identical "pick from a set" was moved into a mart column. The builder's counter: the same WHERE clause has carried `status_short in ('NS','TBD') and fixture_date >= current_date()` since #367 without being flagged, and the contract explicitly allows "select, filter". `working_agreement.md` §10 makes an unclear layer classification the CPO's call.
  CPO ANSWER: "ship as-is, register the gap." Shipped with the SQL selection; registered as GAP-32 with both positions and the disposition recorded, explicitly as a decision to proceed rather than a finding that the reviewer was wrong.
