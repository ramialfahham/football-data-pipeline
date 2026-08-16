# Review — feat/72-onboard-mens-leagues — 2026-08-16

diff_sha256: 7ebfe1c7414d5f6bebd414b11f6a78ce68cb33cc28085718ebe5e5623ba3c377

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Diff file set vs `scope_paths`: all changed files fall inside scope_paths; no SQL/model file touched, confirming the Path B / zero-SQL-changes claim.
- Scope creep / 4th league or existing-row mutation: exactly 3 new entries (BPL/TSL/EKS) added identically across registry.yml, dbt_project.yml var list, and competition_registry.csv; i18n files get exactly 3 new keys each; no existing key/entry value changed. No WSL/NWSL/Liga-Mx-Femenil/women's-league entries appear anywhere in the diff, consistent with decisions_taken §2.
- `sort_order` collision check across the full registry.yml: 170/180/190 are each unique.
- decisions_taken vs escalations.log: the three ruling summaries in contract.md match the escalation log entry line-for-line, with the CPO's verbatim quotes ("1. 5", "drop the women's league all").
- §10 decision-class check: history_seasons depth, women's-league inclusion, and provider-catalog existence are all named CPO-class calls in decisions_taken, each with an escalation record — none silently assumed by the diff.
- Credentials/secrets sweep across the full patch: none present.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `dbt_project/dbt_project.yml`: adds exactly BPL/EKS/TSL to `active_competition_league_codes` in correct alphabetical position, matching `sorted(_registry_active_codes())` in `scripts/sync_dbt_vars.py`. No other line touched.
- `dbt_project/seeds/competition_registry.csv`: three new rows match `SEED_COLUMNS` order and lexicographic placement; cross-checked field-for-field against each `docs/competition_registry.yml` entry — all match.
- `sort_order` collision check: 170/180/190 confirmed as the next free slots after VL=160, no duplicates in CSV or registry.yml.
- Zero hits under `dbt_project/models/**` — no-new-model rule satisfied.
- i18n additions are static label lookups, no computation — consistent with the Consumption-layer rule.
- No hardcoded league/competition identifier introduced in any business-logic layer.
- Impact-map applicability: no model file/grain/staging model changed; the documented no-new-model extensibility mechanism covers this, so a full lineage impact map isn't required — the contract's impact_map correctly scopes to the one piece (i18n) not covered by that mechanism.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- provider_league_id collisions: all existing IDs enumerated against the new 144 (BPL), 203 (TSL), 106 (EKS) — no collisions.
- league_code collisions and format: BPL/TSL/EKS checked against every existing code — no collision, within the 2-6 uppercase char rule; TSL correctly avoids reusing SPL (Saudi Pro League).
- Required-field completeness: each new entry carries every field the sibling pattern (VL/LMX/LP/MLS/SPL/ED) carries.
- history_seasons cost rule: value is 5, with rationale in both `notes` and `escalations.log` citing the CPO's explicit "1. 5" answer — satisfies the registry's "never increase without explicit approval, state the rationale" rule.
- api_coverage_verified dated 2026-08-16 for all three; pattern (no `api_coverage:` sub-block) matches sibling non-Big-5 entries.
- `raw_table_prefix` absent, per rule 4.
- dbt vars/seed sync: both files gained BPL/EKS/TSL in the same diff as the registry entries (single-source rule honored).
- ROUND 1 FINDING, FIXED: `done_when` originally had no line requiring the post-merge `verify_competition_ingest.py --strict` check that the onboard-competition skill documents as the gate against NULL fixture_id / stale wrong-ID fixture-details / orphaned dim_team rows — exactly the risk three brand-new provider IDs carry on first ingest. Fixed by adding a `done_when` bullet committing to that check per league before BPL/TSL/EKS are treated as onboarded-and-healthy. Re-read the amended contract: the gap is closed.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Parsed all three of `site/i18n/{en,de,fi}.json` in full: valid JSON, no trailing commas, no duplicate keys; BPL/TSL/EKS inserted inside the `competitions` block before `WC`, matching the documented skill convention.
- All three new keys present in every locale; display string identical across en/de/fi for all three, consistent with the untranslated-proper-noun convention already used for PD/SA/L1/MLS/SPL/ED.
- Cross-checked each new label against `docs/competition_registry.yml`'s `name` field — exact match, no divergence.
- No existing key's value touched, no unrelated block edited.
- `site/i18n/*.json` is the legacy retired-MVP label dictionary, disconnected from `export_site_data.py` and from site_v2 — no `rendered_page_evidence.md` required.

## escalations
(none — the three #72 CPO-class questions were escalated and answered before this diff was written; see `.claude/task/escalations.log`, 2026-08-16 entry. Nothing new escalated during review.)
