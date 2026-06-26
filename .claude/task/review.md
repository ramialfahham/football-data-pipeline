# Review — chore/500-drop-unused-wc-metrics — delete the unused WC-pretournament metric definitions

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths
> (dbt_project/seeds/metric_definitions.csv → analytics-engineer; site/i18n/** → bi-analyst;
> always → scope-auditor; site/match-preview/metric_definitions.json matches no path pattern;
> contract.md is artifact_only_never → commit not exempt). #500 PR-d step 1: delete dead config only.

diff_sha256: 0afdd57e9f93a9d8127b3b92a117ebd71ee777497d165565ecdc682c0bc3d1ef

## scope-auditor
VERDICT: PASS
risks_checked:
- Byte-identity of the regenerated metric_definitions.json: the 13 remaining match_preview entries
  preserve their exact structure (home/away_column pairs, indent=2); only the 14-row wc_pretournament
  block is removed. Diff is pure deletion — zero modifications to kept entries.
- Consumer verification of the deleted rows: traced the 14 ids across (a) metric_manifest.json (13
  entries, none matching), (b) match-preview/index.html (binds to the manifest; no pretournament/
  single_column refs), (c) check_ui_i18n_metrics.py (one-directional, manifest→i18n), (d) no dbt model
  ref()s the seed. Rows confirmed dead.
- Scope boundary + protected i18n: exactly the 5 scope_paths files touched, no others; the protected
  live WC keys (formContextWcQualifiers/Tournament, footMissingWcDesc, wc.groupPrefix, competitions.WC)
  remain byte-identical. The one §10 decision (delete vs migrate) is CPO-ruled per the contract. No creep.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Warehouse dependency isolation: `grep ref('metric_definitions')` → zero SQL matches; the only YAML
  reference is the seed's own schema.yml. Seed is loaded but consumed by no model/test/source. Deletion
  leaves no orphaned downstream dependency.
- Drift-guard independence: assert_no_uncatalogued_season_metric.sql references only ref('metric_catalogue')
  (the separate SSoT); the metric_definitions seed is not in its graph — deletion cannot affect it.
- Schema-test survivability: schema.yml defines only not_null/unique on the kept columns; no accepted-values
  or row-count assertion requires wc_pretournament. tests/test_metric_definitions_seed.py is row-count-agnostic.
  The 13 retained rows satisfy every test.
- Live render surface + JSON/i18n integrity: zero matches for the deleted ids/contexts under site/ + scripts/
  after deletion; JSON well-formed (13 entries); i18n blocks close cleanly at save_ratio_recent.
escalations: none (noted cosmetic-only: schema.yml `context` column description still lists wc_pretournament
  as an example value — doc-only, no test binding, out of scope for this PR).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Live label broken at runtime: grepped all site/ html+js for the 14 ids — zero matches in
  match-preview/index.html and team-season/index.html. No live surface reads a removed key.
- CI guard stays green: check_ui_i18n_metrics.py loops the 13 manifest ids (manifest→i18n only); all 13
  remain present in en/de/fi — none of the 13 were touched.
- Trailing-comma / over-deletion: new last metrics key is save_ratio_recent in all three files, closing
  without a trailing comma before "competitions". Structurally valid; symmetric across EN/DE/FI.
- Protected live WC keys retained: formContextWcQualifiers/Tournament, footMissingWcDesc, groupPrefix, "WC"
  all present in every language file.
escalations: none

## escalations
(none)
