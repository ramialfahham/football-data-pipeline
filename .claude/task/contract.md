# Task contract — unify the metric label scheme onto the catalogue (#500 PR-d, step 3)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> CPO §10 decision (this session): standardize metric labels on the catalogue's label_i18n_key
> ("Option 1"). The catalogue owns each stat's label key; both live pages + the i18n files use it;
> the legacy hardcoded `metric.*` scheme is retired. Visible output unchanged (same words).

objective: >
  Collapse the three coexisting label schemes to one — the catalogue's `metrics.<id>.label` keys.
  Re-key the i18n `metrics.<windowed_id>` entries to the official ids (words/descriptions unchanged);
  delete the legacy `metric.*` block; have the export stamp each stat's official label key into the
  match-preview data file so the page resolves labels from one source; point both live pages at the
  official keys; update the i18n CI guard. NOTHING ON SCREEN CHANGES — the two active schemes already
  render identical words for all 13 stats in all 3 languages (verified).

refs: #500 PR-d step 3 (follows #582 step 1, #583 step 2); CPO Option-1 ruling 2026-06-26;
  plan C:\Users\Rami\.claude\plans\scalable-snuggling-lightning.md (approved).

scope_paths:
  - site/i18n/en.json
  - site/i18n/de.json
  - site/i18n/fi.json
  - scripts/export_metric_definitions_json.py
  - site/match-preview/metric_definitions.json
  - site/match-preview/index.html
  - site/team-season/index.html
  - scripts/check_ui_i18n_metrics.py
  - site/i18n.js

impact_map: >
  WRITERS / LINEAGE:
    - site/match-preview/metric_definitions.json — sole writer scripts/export_metric_definitions_json.py;
      gains a per-entry `label` = the catalogue's label_i18n_key (looked up via the binding's
      catalogue_metric_id). DELIBERATE change to the data file (no longer byte-identical to step 2) —
      regenerated + committed; the regen test still guards (committed == fresh regen).
    - site/i18n/{en,de,fi}.json — hand-edited: the `metrics.<windowed_id>` entries are RENAMED to the
      official id (via site/match-preview/metric_bindings.csv: live_id → catalogue_metric_id); the words
      + descriptions are MOVED unchanged; the `metric.*` block is deleted.
  CONSUMERS / BLAST RADIUS:
    - Label resolution today: match-preview index.html `metricLabel()` = `metrics.<windowed>.label` with a
      `metric.*` fallback (LEGACY_METRIC_LABEL_KEYS, lines 623-643); team-season index.html = 13 hardcoded
      `t("metric.<short>", ...)` calls (lines 342-354). `metric.*` is used ONLY in those two pages + one
      doc-comment example in site/i18n.js:14 (verified by grep). After: match-preview reads `def.label`
      (the official key from the data file); team-season uses `metrics.<official>.label`; the `metric.*`
      block + LEGACY_METRIC_LABEL_KEYS are deleted.
    - VERIFIED no wording decision: for all 13 stats × en/de/fi, `metric.<short>` == `metrics.<windowed>.label`
      (zero mismatches) — so moving the values to the official keys preserves every rendered word.
    - `metrics.<id>.description` is NOT consumed by any page (only `.label` is read) — descriptions ride
      along in the rename, no consumer break.
    - scripts/check_ui_i18n_metrics.py today checks manifest windowed ids against `metrics.<windowed>`;
      after re-key it must check the OFFICIAL keys (map the shown stats through metric_bindings.csv).
  LAYER RULES: page label lookup = consumption (select/route a key → t(); NO computation); the export
    reads label_i18n_key from the catalogue (select, no derivation); i18n files = display copy. Catalogue
    is READ-ONLY (not modified). Safety property here is VISIBLE-identical (same words), not byte-identical.
  DEPLOY ORDERING: static files; regenerate + commit the data file; the deploy export runs with no args.

decisions_taken: >
  Execute CPO Option 1 (label SSoT = the catalogue's label_i18n_key). No metric definition changed; no
  word changed; the catalogue is untouched. The one §10 (which scheme) was decided by the CPO this session.

decisions_reserved:
  - corners_conceded → corners_against rename (step 4 — official id stays corners_conceded_per_match here);
    team-season `_season` column-name drop (step 5); final teardown of build_match_preview_site + any
    remaining legacy (step 6). NONE here. Dropping the unconsumed `metrics.*.description` copy is NOT done
    here (out of scope; flag only).

done_when:
  - The i18n `metrics` block is keyed by official ids; the `metric.*` block is gone; both pages render via
    the official keys; the export stamps `label` into the data file; the i18n guard checks official keys.
  - Proof: the 13 rendered words per language are IDENTICAL before vs after (captured + compared); the
    updated guard passes; the regen-matches-committed test passes; JSON validity holds.
  - validate-local green. Routes to: scope-auditor (always) + bi-analyst (site/i18n/**) +
    analytics-engineer (scripts/export_*.py) + cto (scripts/export_*.py + scripts/** + tests-adjacent).
    Commit carries contract.md → NOT artifact-exempt. CPO merges; never self-merge.

amendments: (none)
