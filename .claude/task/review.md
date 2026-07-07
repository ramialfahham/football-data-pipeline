# Review — feat/competition-header-identity — 2026-07-07

> G3 Lock artifact. Surface the registry identity fields (country, confederation, tier) on the competition-season
> hub payload — they already flow through `_registry_competitions` but were dropped when the `meta` dict is built
> in `fetch_competition_payloads`; `shape_competition_payload` now surfaces them. Export-only registry pass-through
> (the GAP-01/#613 pattern), no BigQuery, no model. + 2 unit tests + a content_architecture.md §3 board flip
> (Competition header partial → green). Required set (routing): scope-auditor (always) + analytics-engineer +
> cto (scripts/export_*.py + tests/**).

diff_sha256: a046cbae48ad4aca16b9e2fdff6a788816eab4ef65ea1819cc27620568d277c3

## scope-auditor
VERDICT: PASS
risks_checked:
- **Consumption-layer contract (A5).** The three fields are pure pass-throughs from the registry `meta` via `.get()`
  — no computation, derivation, conditional logic, or taxonomy mapping in either `fetch_competition_payloads` or
  `shape_competition_payload`. Two unit tests cover presence + absence-as-None. No derived facts.
- **Board-status honesty (A6).** The content_architecture.md flip partial → green is accurate and precedented
  (GAP-01/#613: same shape — add registry/dim identity → flip green). The note "name/slug + country/confederation/
  tier surfaced" matches exactly what shipped; not aspirational. Scope 100% surgical (only the declared files);
  no §10 decision invented (the field set was CPO-approved via the plan).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- **Safe-default (None-on-absent).** Verified `tier` is genuinely absent from non-domestic_league registry entries
  (WC/qualifying) per the registry's own contract; the `.get()` chain (3 hops) yields None, not a crash or a wrong
  0/1 — exercised by `test_shape_competition_payload_identity_absent_is_none`.
- **Second meta-dict collision.** Two structurally identical `meta = {...}` comprehensions exist
  (`fetch_competition_payloads` + `fetch_leaderboard_payloads`, ~80 lines apart); confirmed by direct read that only
  the first was touched — the leaderboards meta still carries only name/slug.
- **Consumption-layer computation.** Every added expression is a bare `.get(key)` — no transform/lookup/fallback;
  no taxonomy mapping introduced (the pre-existing `_by_tier`/nav logic is untouched). Matches layering.md.
- **Governance/scope-inflation.** The doc change is a single one-line status flip on a row that shipped in the same
  diff; the contract's impact_map/blast_radius (no writers, no dbt, one export entity, three fields, safe `.get`)
  matches the actual diff exactly.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **Blast radius.** `fetch_leaderboard_payloads`'s meta dict is byte-for-byte unchanged; `shape_competition_payload`
  has exactly one production call site (line 838), so no second differently-shaped caller drops/breaks on the new keys.
- **Field-name correctness + None-safety.** `_registry_competitions` reads country/confederation/tier from the same
  registry YAML keys the meta comprehension uses (no typo/drift); international/qualifier entries genuinely omit
  `tier` — the None-test covers it, not a fabricated edge case.
- **JSON serialization.** `_payload_bytes` uses `json.dumps(..., default=str, ensure_ascii=False)`; str/str/int + None
  all serialize natively, no encoder gap.
- **Hidden downstream coupling.** No `site_v2` consumer of `shape_competition_payload`/`competitions.json` exists yet;
  no jsonschema/strict-key validator gates the export — additive keys are safe.
- **Test-suite integration.** Both new test names unique; python-ci runs `pytest tests/ -v` unfiltered, so both are
  collected regardless of the `-k competition` shorthand.

## escalations
- None open. No ESCALATE. The {country, confederation, tier} field set was CPO-approved via the plan; the board flip
  is directly-coupled doc-sync (GAP-01 precedent). Pure consumption-layer pass-through — no computed fact.
