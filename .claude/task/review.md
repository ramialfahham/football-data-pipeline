# Review — feat/site-v2-fixture-page — 2026-07-11

> v2 frontend, Phase E, increment 1: shared design system (tokens + components + Layout)
> in site_v2/ + a fixture template rendering ONE real exported fixture (BSA Palmeiras vs
> Atlético-MG, 1492306), built as the /v2/ preview artifact. Live MVP + its Pages deploy
> untouched (Option A). Round 2 — re-run fresh after the round-1 fixes (see below) changed
> the hash. Required reviewers per review_routing.json for `site_v2/**`: scope-auditor
> (always) + cto-reviewer. Both PASS.

diff_sha256: 10b6472cb352e44385a74746f536bbf1103f51a10c141adada46ded8a3bb1d5a

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + PROTECTED paths: all 28 staged files are within scope_paths (`site_v2/**`, `.claude/task/**`); the root `.gitignore` was NOT touched (the lib re-include is in-scope `site_v2/.gitignore`), and nothing under `.github/workflows/**`, `pages-match-preview.yml`, `scripts/**`, `site/**`, `dbt_project/**`, or `.claude/{hooks,agents,commands,settings}` is edited. Option A (defer live deploy) honoured.
- Consumption-layer contract (anti-pattern A3/A5): the display helpers (`lib/bars.ts`, `lib/format.ts`, `components/fixture/MetricRow.astro`) are display-only — `betterSide()` returns null (no green) on missing/neutral/equal, nulls render the en-dash "–" (never a fabricated 0), slugs come from the payload + registry-derived `competitions.json` (no frontend slug generation). No metric math, ranking, window selection, or taxonomy mapping in components/pages.
- LOCKED 16-row table fidelity (§10 binding): `lib/metricRows.ts` is exactly the 16 rows of `docs/wireframes/metrics_display.md` (CPO-locked 2026-06-11) in the fixed group/row order with the catalogue `format`/`direction`; the intentional field≠display-id case (row 6 `shots_on_goal_per_match`) is documented; zero drift/reorder/addition. Design + deploy (Option A) + sample-league (BSA; BL1 off-season) choices are all grounded/flagged, no unlabelled CPO-class decision.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Build-completeness / gitignore shadow (the round-1 FAIL) — RESOLVED: the diff now contains all 5 `site_v2/src/lib/{format,bars,href,metricRows,types}.ts` as tracked new files (`site_v2/.gitignore` `!src/lib/` re-include counters the unanchored root `lib/`); `git check-ignore` clears them; a fresh clone/`ci-site-v2` checkout has every imported file. Checked the root `.gitignore` for other unanchored shadows over `site_v2/src/**` (`data/`, `build/`, `target/`…) — none match this diff's new paths. Build no longer relies on untracked files.
- `base: "/v2/"` does not break the CI gate: Astro `base` only prefixes emitted URLs/asset links, not the `outDir` tree, so `ci-site-v2.yml`'s `dist/index.html` + `dist/{de,en,fi}/index.html` assertions still hold (re-verified: build emits the CI four plus the 3 fixture pages); the workflow file itself is untouched.
- JS-free `:checked` toggle is structurally sound + accessible: radios, the `.seg` labels, and both `.win-w1`/`.win-w2` blocks are direct siblings so the `~` selector binds; radios are hidden via absolute/opacity (not `display:none`) so they stay tab-focusable with a `:focus-visible` outline; both windows are always in the DOM (crawlable, no-JS safe). The round-1 robustness fixes are present: `[fixture].astro` getStaticPaths throws on a missing `competitions.json` slug, and `FormSegment.astro` guards W/D/L chips on all three counts non-null.
- Consumption-layer + TypeScript: grep of `components/**` + `pages/**` finds zero `.sort(`/`.reduce(`/`Math.` (arithmetic confined to `lib/bars.ts` + `lib/format.ts`); under `verbatimModuleSyntax` every type is imported via a separate `import type`, so nothing throws at transpile. No PROTECTED/live-artifact path touched.

## escalations
(none)
