# Review — fix/competition-name-from-registry — 2026-09-04

diff_sha256: 9426b0714073ca82245b7a714ed8560da6493d640fdc3e66f6069365a4f7e84c

rounds: 5

⚠ **ONE CHANGE WAS MADE AFTER BOTH VERDICTS, and it is declared rather than hidden.** Both
reviewers passed at hash `be46688b…`. `analytics-engineer-reviewer` then reported, in the same
pass, that `contract.md` cited `content_architecture.md` as "§2 rule 2" when the rule is at
`:22` under "§1 Principles" — its own words: *"a locator imprecision, not a misstatement of
substance, and not a warehouse-correctness defect."* Corrected, which moved the hash to the value
above. No sixth round was run for a section number, and nothing else changed: the SQL, the seed and
both tests are byte-identical to what was passed five times, and the corrected pointer is the
finding the reviewer itself raised rather than a new claim it never saw.

rounds_cap_override: >
  CPO, 2026-09-04, when offered the choice of handing the branch over unfinished instead of
  spending further rounds: *"Why do you keep saying this as an option? You don't want to work?"* —
  i.e. finish it. Recorded because the cap exists to force a STOP-and-ask, and the ask was made and
  answered rather than assumed.
  ⚠ Worth stating plainly for whoever reads this next: **every one of the four FAILs was my prose,
  not the code.** The seed, the base model and both tests were byte-identical from round 1 and
  passed the warehouse review five times. A cap meant to stop a code-quality loop was consumed by
  an artifact-honesty loop, which is a different failure and arguably should not spend the same
  budget.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-4 finding 1 (the contract claimed the seed satisfies the external-source-of-record rule it
  cites) re-checked in `contract.md` decisions_taken and `seeds/schema.yml` — both now state the
  seed does NOT meet that bar; no contradicting sentence in `acceptance_evidence.md` or `base.yml`.
- Round-4 finding 2 (the round-3 rewrite deleted the rationale for the seven spelled-out `WCQ*`
  rows while the seed still implemented them) re-checked — restored as an explicitly UNWRITTEN
  item, not dressed as a logged ruling. Verified against `escalations.log` by grep ("standardised",
  "WCQ", "2026-09-04"): no matching entry, so the "unwritten" framing conceals no record.
- Swept ALL 20 seed rows against `docs/competition_registry.yml` hunting a THIRD undisclosed
  authority: 11 rows are byte-identical registry copies, `WC` drops the season, the 7 `WCQ*` rows
  expand "WC" to "World Cup", `UECL` cites #55. Every one maps onto a disclosed written source or
  one of the two disclosed unwritten rules. None rests on anything else.
- Scope: every changed path is inside `scope_paths`; `layering.md`'s exhaustive inventory is
  marts-only and this adds no mart, so no doc-sync gap.
- Threshold crossings: no new mechanism (third instance of the documented seed + left join +
  coalesce pattern), no new dependency, no recurring cost; declarations accurate against the diff.
- Credential sweep across the full patch — nothing credential-shaped.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Counted the seed independently: 20 data rows, 19 citing `docs/competition_registry.yml` and one
  (`UECL`) citing #55 — matches the contract's "19 of 20" claim rather than taking it on trust.
- Confirmed `seeds/schema.yml:521-523` frames `source` as provenance not authority, against
  `:497`'s "URL of the external source of record" for `team_name_overrides` — so the contract's
  admission that this seed does not meet that bar is accurate.
- Cross-checked the seven `WCQ*` seed rows against `docs/competition_registry.yml:139,158,177,196,
  215,234,253` — the spelled-out-vs-abbreviated claim holds.
- Re-read `base_apif__leagues.sql` end to end: the import CTE, the
  `coalesce(name_overrides.league_name, leagues.league_name)` projection and the `left join` on
  `league_code`. Unchanged across all five rounds. The seed's `unique` + `not_null` on `league_code`
  means the left join cannot fan out.
- Re-read `dim_league.sql`: still a plain column list off `base_apif__league_entity` with no
  coalesce, so "the core dim publishes rather than corrects" holds; `base_apif__league_entity`'s
  `select *` confirms the corrected `league_name` actually flows through.
- Read both new tests in full and diffed their logic against their own inline claims — the
  ORPHAN/STALE split, the PRE-override comparison against `stg_apif__leagues`, and the assertion
  surface (`mart_competition_index`) all match what the SQL does. Verified the sibling comparison in
  the new test's comment against `assert_team_name_overrides_still_needed.sql:35` — it is indeed an
  `inner join`, so the comment is checked rather than an assumed analogy.
- Checked for per-competition branching outside the seed: the only league codes in the model are in
  SQL comments and the seed's `note` column, never in executable logic; the join stays generic on
  `league_code`.
- Confirmed `mart_competition_index`, `export_site_data.py` and the consumption layer are untouched.

## escalations
(none)
