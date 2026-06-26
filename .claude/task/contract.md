# Task contract — drop the unused WC-pretournament metric definitions (#500 PR-d, step 1)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> CPO-directed (2026-06-26): the WC-pretournament metric block is dead config — DELETE it,
> do not migrate/register it. This overrides the handover's earlier "register
> qualifier_games_played" assumption (CPO §10 product ruling: that unbuilt screen is not happening).

objective: >
  Remove the 14 unused World Cup "pretournament" stat definitions from the legacy
  metric_definitions feed and everywhere they echo. They were set up for a WC preview screen
  that was never built and have NO live consumer (the match-preview JS only renders the 13
  metrics listed in metric_manifest.json). Purely deletes dead data — no code, no logic moves.
  Self-contained low-risk first step of #500 PR-d; the bigger migration (repoint the live site
  at metric_catalogue.csv) is a separate later step and is untouched here.

refs: #500 PR-d step 1; CPO ruling 2026-06-26 (WC-pretournament block is dead → delete);
  plan C:\Users\Rami\.claude\plans\scalable-snuggling-lightning.md (approved).

scope_paths:
  - dbt_project/seeds/metric_definitions.csv
  - site/match-preview/metric_definitions.json
  - site/i18n/en.json
  - site/i18n/de.json
  - site/i18n/fi.json

impact_map: >
  WRITERS / LINEAGE:
    - dbt_project/seeds/metric_definitions.csv — hand-edited config seed. Consumed ONLY by
      scripts/export_metric_definitions_json.py (a pure CSV→JSON transform). Evidence:
      `grep -r "ref('metric_definitions')" dbt_project` → ZERO model refs; the seed is loaded
      to the warehouse but no dbt model selects it.
    - site/match-preview/metric_definitions.json — the ONLY writer is
      scripts/export_metric_definitions_json.py. Regenerated from the trimmed seed (NOT
      hand-edited). Baseline verified byte-identical to the seed export today.
    - site/i18n/{en,de,fi}.json — hand-edited. Carry the `metrics.<id>.label/.description`
      entries for the dead rows (orphaned once the rows go).
  CONSUMERS / BLAST RADIUS:
    - site/match-preview/index.html iterates ONLY metric_manifest.json (the 13 `*_recent`
      match_preview metrics) → the 14 `wc_pretournament` rows are NEVER read. Evidence: grep
      of index.html for `pretournament|single_column` → no binding logic; grep across site/
      for `single_column|pretournament|qualifier_games_played|points_capture` → matches only in
      i18n + the generated JSON + the seed, never in render JS.
    - scripts/check_ui_i18n_metrics.py validates ONLY that the manifest's 13 ids have i18n
      entries (one-directional). Evidence: read of the script — it loops `metric_ids` from the
      manifest, never the reverse. Removing unused i18n keys keeps it green.
    - tests/test_metric_definitions_seed.py — row-count-agnostic (uniqueness + paired/single
      column invariants); removing rows keeps it green.
    - build_match_preview_site.{sh,ps1} COPY the committed JSON (do not regenerate) → unaffected.
  LAYER RULES: seed = config (not a model); deletion is warehouse-clean (no model dependency).
    No new logic, no layer placement decision — data deletion only.
  DEPLOY ORDERING: static files; regenerate the JSON in-repo and commit it so the committed
    artifact stays in sync with the trimmed seed. No migration / no full-refresh.
  EXPLICITLY OUT (live WC previews depend on these — DO NOT TOUCH): i18n
    matchPreview.formContextWcQualifiers / formContextWcTournament / footMissingWcDesc,
    the wc.groupPrefix labels, and competitions.WC.

decisions_taken: >
  Delete the dead WC-pretournament block rather than migrate it (CPO §10 product ruling,
  2026-06-26). No metric definitions added or changed; the metric_catalogue.csv SSoT is NOT
  touched. The 13 live on-screen metrics are left byte-identical.

decisions_reserved:
  - The bigger #500 PR-d migration (repoint export_metric_definitions_json.py at the catalogue;
    single i18n scheme; corners naming; retire the legacy seed) — separate later steps, NOT here.

done_when:
  - The 14 `wc_pretournament` rows are gone from metric_definitions.csv; the regenerated
    metric_definitions.json contains ONLY the 13 match_preview entries, each byte-identical to
    today; the 14 orphaned `metrics.*` keys are gone from en/de/fi.json.
  - `git diff site/match-preview/metric_definitions.json` shows only the 14 deletions.
  - `python scripts/check_ui_i18n_metrics.py` green; `pytest tests/test_metric_definitions_seed.py`
    green; validate-local gates green.
  - Routes to: scope-auditor (always) + cto (scripts/site build config touched by the JSON regen
    path) + bi-analyst (i18n labels touched). The commit carries contract.md → NOT artifact-exempt.
    CPO merges; never self-merge.

amendments: (none)
