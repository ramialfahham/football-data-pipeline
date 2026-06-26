# Review — refactor/500-corners-against — rename corners_conceded → corners_against (+ folded entity-list fix)

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set (unchanged): scope-auditor (always) + analytics-engineer (dbt_project/** incl. seeds/schema.yml)
> + football-analytics (metric_catalogue.csv) + bi-analyst (site/i18n/** + docs/wireframes/**).
>
> AMENDMENT (post first review): ci-data-build surfaced a PRE-EXISTING failure unrelated to corners —
> accepted_values_metric_catalogue_entity allowed only ["team","player"] but the catalogue carries the
> locked "team and player" entity. Folded a one-line fix into dbt_project/seeds/schema.yml. scope-auditor +
> analytics-engineer RE-RAN on the full amended diff (below). football-analytics + bi-analyst PASS CARRIED
> FORWARD from the corners-only review — their surfaces (metric_catalogue prose / i18n / docs) are
> byte-unchanged by the schema.yml fix. dbt parse (via dbt MCP) = OK on this working tree.

diff_sha256: 81751d8b14066f6df61408706c7cc73ba4ae95a7437d59e7c6a89e5fb646b9dc

## scope-auditor  (re-run on amended diff)
VERDICT: PASS
risks_checked:
- Incomplete lineage propagation across the dbt layers → UI → 3 i18n langs: traced the catalogue id through
  int_team_season__metrics → mart_team_momentum → 5 downstream marts + the macro → bindings → metric_definitions.json
  → i18n + team-season page; no stray old reference; both accepted_values yml lists carry the new id.
- Schema.yml amendment scope + integrity: the pre-existing entity test (allowed only team/player) blocks the PR
  because metric_catalogue.csv is modified; the catalogue legitimately carries "team and player" (finishing_efficiency
  row 14, duels_won_pct row 16); the one-line fix (entity description + accepted_values adds "team and player") is
  minimal, tied to the locked value, recorded in contract amendments, schema.yml added to scope. No creep; no new §10.

## analytics-engineer-reviewer  (re-run on amended diff)
VERDICT: PASS
risks_checked:
- accepted_values fix coverage: independently enumerated all catalogue entity values — exactly team×25, player×44,
  "team and player"×2 (finishing_efficiency, duels_won_pct); the new list ["team","player","team and player"] is
  neither over-permissive nor incomplete → the failing test will pass. Fix is minimal (entity description + list only).
- Corners rename warehouse-consistency: full DAG producer→consumer traced (momentum/int_team_season → matchday/
  season marts + macro + 2 accepted_values lists + UI), zero corners_conceded left in source; no-drift guard strips
  `_season` generically (no hardcoded corners) → corners_against_per_match_season resolves to the renamed catalogue
  row; catalogue change is id + label_i18n_key only (formula/description/interpretation byte-identical). dbt parse OK.
escalations: none

## football-analytics-expert-reviewer  (PASS carried forward — metric_catalogue content byte-unchanged since)
VERDICT: PASS
risks_checked:
- Pure rename of the catalogue row: id + label_i18n_key only; numerator (opponent_corner_kicks), denominator (games),
  description, interpretation, direction (neutral), format (decimal_1), group (set_pieces) all byte-identical — no
  redefinition of the metric's meaning.
- Naming + domain correctness: mirrors goals_against exactly (id uses _against while the description prose keeps
  "conceded"); "corners against" is standard football terminology for opponent corner kicks; the corner_kicks/corners
  word asymmetry is pre-existing and explicitly out of scope. The amendment touched only seeds/schema.yml's entity
  test (not the catalogue row content), so this carried-forward verdict is unaffected.

## bi-analyst-reviewer  (PASS carried forward — i18n/docs byte-unchanged since)
VERDICT: PASS
risks_checked:
- Displayed-word preservation: i18n change is key-only; label + description values under corners_against_per_match
  are byte-identical to the old corners_conceded_per_match entries in en/de/fi. No rendered word changes.
- Lockstep across manifest → bindings → metric_definitions.json → team-season page → catalogue; i18n guard resolves
  the renamed key. (The amendment touched only seeds/schema.yml — not i18n or docs/wireframes — so this verdict holds.)

## escalations
(none)
