# Review — refactor/500-unify-metric-labels — unify the metric label scheme onto the catalogue

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths:
> site/i18n/** → bi-analyst; scripts/export_*.py → analytics-engineer + cto; scripts/** → cto;
> always → scope-auditor; site/match-preview/** + site/team-season/** + site/i18n.js match no path
> pattern; contract.md is artifact_only_never → commit not exempt. #500 PR-d step 3 (Option 1).
>
> POST-REVIEW DELTA (transparency): after the 4 PASS verdicts below, the analytics-engineer's
> non-blocking docstring nit was fixed — 2 docstrings in scripts/export_metric_definitions_json.py
> updated to mention `label_i18n_key`. Behavior-neutral (the generated data file regenerates
> byte-identical; verified). diff_sha256 below is the post-fix hash.

diff_sha256: 2de4b7c3fc5d68d402739f4e90ef4a4099e843d79bf160732f64a0001e068f63

## scope-auditor
VERDICT: PASS
risks_checked:
- Label key → i18n resolution chain: all 13 stats have a matching catalogue label_i18n_key; all 13
  official ids exist in all 3 i18n files with non-empty labels; the export stamps the key; the page
  resolves it via t() — renders the same words before/after (zero mismatch across 13 × 3 langs).
- Scope boundaries + reserved decisions: all 10 touched files within scope_paths; metric_catalogue.csv
  unmodified; no windowed id renamed (corners_conceded_per_match stays; team-season `_season` reads
  unchanged); the one §10 (which scheme) was CPO-pre-decided — no silent decisions, no reserved item invaded.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Word-preservation across 3 languages: the patch shows only key renames; the label + description VALUES
  are byte-for-byte identical between the removed windowed entries and the added official entries in all
  three files; the `metric.*` block is absent from all three (grep); no windowed `_recent.label` survives.
- No broken label at runtime: zero live `t("metric.` calls remain (grep); match-preview resolves
  live_id → data-file `label` (e.g. metrics.goals_per_match.label) → t(def.label, metricId) (call site
  passes def correctly); team-season uses t("metrics.<official>.label", <fallback>) for all 13.
- CI guard correctness: the updated guard maps manifest live ids → official via metric_bindings.csv and
  checks metrics.<official>.label/.description in every i18n file; fails-closed on any missing entry.
escalations: none

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Consumption-layer compliance: the export reads label_i18n_key as a verbatim string passthrough (.strip()
  only) and assigns it to entry["label"]; metricLabel routes the key through t() — no metric math / no
  derivation introduced anywhere.
- Catalogue integrity + 13-binding resolution: metric_catalogue.csv is absent from the patch (unmodified);
  all 13 catalogue_metric_ids resolve to rows with a non-empty label_i18n_key; every `label` in the data
  file equals the catalogue's label_i18n_key; the regen-matches-committed test covers the new field.
note: flagged 2 stale docstrings in export_metric_definitions_json.py (non-§10, mechanical) → FIXED post-review
  (see POST-REVIEW DELTA). No CPO involvement needed.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No orphaned LEGACY_METRIC_LABEL_KEYS reference (grep across .html/.js = zero); metricLabel(def, metricId)
  call-site arity consistent (site/match-preview/index.html:661 passes (def, metricId)); fallback path safe.
- check_ui_i18n_metrics.py end-to-end: all 13 manifest live ids present in metric_bindings.csv → 13 official
  ids present with non-empty label+description in all 3 i18n files; fails-closed on any missing entry.
- Export serialization unchanged (json.dumps(..., ensure_ascii=False, indent=2)+"\n"); both no-arg callers
  (pages-match-preview.yml:129, export_matchday_insights.ps1:14) still work; stdlib-only, no new deps.
escalations: noted the pre-existing stale `metric_definitions.csv` trigger in pages-match-preview.yml:25 is
  a harmless cosmetic dead path (the JSON is itself a trigger) — already a contract-acknowledged step-6
  follow-up, out of scope here. Not a CPO blocker.

## escalations
(none requiring CPO — the two reviewer notes are an in-scope docstring fix, applied; and a known
out-of-scope workflow-trigger tidy tracked for a later step.)
