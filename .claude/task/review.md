# Review — fix/description-standard-and-false-claims — 2026-08-20

diff_sha256: 7832f0dba8e6bcd428c5df0f27607ddd2e7bf65f07806c2b664a48c623e2af84

rounds: 2

> MR1 of the six-MR description-drift plan (`escalations.log`, 2026-08-20). Routing gives
> analytics-engineer-reviewer (`dbt_project/**`) and the always-on scope-auditor.

## scope-auditor
VERDICT: PASS
risks_checked:
- ROUND 1 FAILED, correctly, and the finding was the sharpest of the task: every piece of authority
  this MR leans on — the six-MR plan, the MR1/MR3 split used to justify narrowing two acceptance
  criteria, the CPO's definition of a good description — existed ONLY in `contract.md`, which the
  next task overwrites. No `escalations.log` entry backed any of it. Re-checked against the new
  2026-08-20 log entry, which now carries the full chain verbatim: how the false `display_group`
  claim surfaced, the CPO's diagnosis quote, the audit's measured numbers, dbt's published rules
  separated explicitly from our own convention, the three chat rulings (readers / reuse / scope),
  and the six-MR split naming MR3 as the owner of `country_name_overrides`'s full cleanup. Durable
  and append-only. Defect resolved.
- Re-judged the acceptance-criteria narrowing now that the split has a durable record. The log
  independently corroborates what `contract.md` claimed, and the contract records that the criteria
  were wrong when written rather than softened once inconvenient. No longer an unverifiable
  assertion.
- `display_group`: diffed against the new §2 standard — states meaning and what blank means, drops
  the false downstream-consumer claim, no dates/rulings/refs/emoji, under 600 chars, and matches
  the standard's own worked example verbatim rather than merely claiming to.
- `country_name_overrides`: confirmed surgical — only the false sentence removed; the rest of the
  block (rulings, dates, refs) untouched, matching the "not cleaned here, MR3 owns it" criterion.
- `shared.yml` `entity_type`: confirmed a hardcoded count became an invariant.
- §10 check: the three chat rulings are recorded as CPO authority in the durable log, and none of
  them is IMPLEMENTED in this diff — `persist_docs` and CI docs generation stay deferred to MR6
  under `decisions_reserved`, so nothing crossed from authorised to shipped ahead of its MR.
- scope_paths vs diff: all five touched files declared; no out-of-scope file touched.
- Secrets/credential sweep across the full patch: no matches, no permission widening.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Verified the `display_group` correction against the code rather than the claim: grepped all
  readers (3 hits, all `mart_competition_index.sql`), read the filter in context (lines 73-92), and
  confirmed a blank `display_group` is excluded from the `browsable` CTE feeding the competitions
  page. Then tested the new text's harder claim — that the exclusion removes zero rows today — by
  finding the three blank-`display_group` rows in `competition_types.csv` and confirming none of
  the 48 registry entries uses any of those types. Claim holds.
- `country_name_overrides`: confirmed the false sentence is gone and that four base models plus
  `dim_country.sql` actually read it, and that the replacement text makes no new consumer claim.
- `shared.yml` `entity_type`: counted the registry independently — 48 entries, every one carrying a
  `competition_type`. "All 45" was wrong on the count itself, separately from the drift.
- Judged the new §2 standard as dbt practice: docs-block guidance, the 80-char YAML convention and
  the 600/1,024-char limits are correct, with working citations.
- Scrutinised rather than waved through: the new `display_group` text NAMES `mart_competition_index`,
  which sits close to the newly-banned downstream-consumer claim. Judged compliant — the ban targets
  exhaustive/exclusivity claims ("the only reader is X"), which rot when a consumer is added; naming
  one mart's actual filter behaviour to explain what blank means is the "known limits" content the
  standard requires and cannot go stale the same way.
- Spot-verified an illustrative number in the new standard (`league_code` documented 76 times) with
  an independent grep — exact match.
- Confirmed doc-only: no `tests:` block, column, seed CSV row or model SQL anywhere in the patch.

## escalations
(none)
