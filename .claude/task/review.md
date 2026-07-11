# Review — feat/site-v2-team-profile — 2026-07-11

> v2 frontend Phase E, increment 2: the Team profile Overview (wireframe 02) in site_v2/,
> reusing #672's design system + new team components as consistent extensions. Renders ONE
> real exported team (Arsenal 42, default season) across de/en/fi, behind /v2/. Flagship
> deserved-vs-actual DEFERRED (CPO-ruled). Round 3 — both required reviewers (scope-auditor +
> cto-reviewer per review_routing.json for `site_v2/**`) PASS after rounds 1-2 fixes.

diff_sha256: 267ed56bf9a5c2fce5d095d80a5f5e858172d0c2394569261657ee017a3ebfed

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + §10: all staged paths are `site_v2/**` + `.claude/task/{contract.md,escalations.log}`; no PROTECTED/out-of-scope edit (`.github/workflows/**`, `scripts/**`, root `.gitignore`, `site/**`, `dbt_project/**`). The flagship deserved-vs-actual is DEFERRED (not rendered); new components are consistent extensions of the locked #672 rules (colour = meaning only — single-team surface has no comparison-green; YoY delta is direction-driven; winless = a negative streak); no invented metric/mechanism/name. Season metrics reuse the LOCKED 16-row `metricRows.ts`.
- Consumption-layer + resolved findings: no fact derivation in the frontend (`pickDefaultSeason` = selection; slugs from the payload + registry-derived `competitions.json`; arithmetic in `lib/bars.ts`/`format.ts`). Round-2 ESCALATE resolved: Q1 (sample-team) — classified TEMPORARY demo data, not §10, with the CPO-approved-plan fallback authorization recorded in `contract.md` decisions_taken 5 + a provenance entry in `escalations.log`; Q2 — `SeasonStats.astro` now renders the FULL 16-row table (no data-filter), `StatRow` shows honest "–" for missing (wireframe 02 §6).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Number-formatting class FULLY closed: every nullable served count now routes through `integer()`/`signedInteger()` (`RecordBlock` rank/points/played/W-D-L/goals/goal-diff/clean-sheets; `Streaks` run count; `TeamFixtureRow` goals; `YearOverYear` now/prev/delta). The only raw interpolations left are YEARS (`founded_year`, `season_api_year`) — correctly ungrouped; `yoy_games_played_cutoff` is gated before the i18n template so a null never reaches it. `SeasonStats.astro` has no leftover `has()`-filter or unused `asNumber`/`MetricRowDef` imports; renders all 16, `StatRow` → "–" on null (cross-checked against `42.json` — all 16 present, so the 16-`.srow`/zero-"null" build is data-consistent, not luck).
- Build-completeness + isolation: every imported sibling exists with a matching Props signature; `lib/team.ts` is tracked (the `!src/lib/` re-include) and no new `.gitignore` shadow covers `src/components/team`/`src/data/teams`; the 16-file diff is entirely `site_v2/**` + `.claude/task/**` — `.github/workflows/**` (incl. ci-site-v2.yml, byte-identical on disk), `scripts/**`, `site/**`, `astro.config.mjs` (`base:"/v2/"`), `package*.json` all untouched; no new dependency. `verbatimModuleSyntax` honored (type-only imports separated); the `as unknown as` casts mirror the existing fixture-page precedent.

## escalations
(none)
