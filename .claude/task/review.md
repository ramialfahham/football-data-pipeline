# Review — feat/team-page-overview — 2026-07-23

> Team page Overview tab (export foundation + built frontend), from CPO-approved mock
> f6348775. One PR. Blinded review over three rounds; round 1 surfaced real findings
> (consumption-layer verdict threshold, mid-season trend-line assumption, a contrived
> featured-season rule, a JS tab-toggle, a hardcoded aria-label, a tautological test,
> a triple-rendered points value), all fixed with judgment. All four required reviewers
> PASS at the final hash.

diff_sha256: 5bdaf0a0e143abc81651c66ad9cc015980ce8d7c6545e6bc86386bfdc7ab98b4

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is within scope_paths; the `amendments:` entry is a faithful glob-safe
  correction (bracketed Astro path read as fnmatch char classes → directory-prefix form), not a
  scope expansion.
- The four round-1 mechanisms resolved without unauthorized §10 decisions: featured-season rule
  reverted to the codebase's most-recent-domestic convention; verdict keyed off the catalogue's
  documented gap sign (no invented tier); tabs use the existing JS-free radio pattern; the season
  label + verdict block are in the approved mock. The two CSS additions (`.sc .gap`, `.coming`)
  stay within the token contract.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Export purity: `deserved_scatter_index` / `shape_team_payload` are selection/grouping/equality-flag
  only — no arithmetic, no re-fit; `deserved` passes through the mart's `deserved_points` verbatim;
  the three metrics are pre-existing catalogue rows (no A1).
- Verdict classification keys off the served `sot_points_gap` SIGN only (matches metric_catalogue.csv
  negative=under / positive=over) — the round-1 rounding-threshold "Inline" tier is gone.
- The trend line's colinearity precondition (deserved = fitted-rate × games ⇒ colinear only when games
  are equal) verified against int_team_season__deserved_vs_actual.sql:190-199 and numerically against
  the committed sample (slope ≈11.745 across dots); the 2-point segment is exact for this games-aligned
  sample, and the mid-season case is registered as an explicit export follow-up, not silently shipped.
- The new `test_deserved_scatter_preserves_the_fitted_line` builds independent colinear data and asserts
  exact pass-through (non-tautological; satisfies the contract's done_when).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: every field the Overview components render traces to a `select * from mart_team_profile`
  row via `shape_team_payload`; the committed sample is internally self-consistent (scatter `deserved`
  colinear in sotd; self dot's deserved = the season's `deserved_points`) — real export output, not typed-in.
- Absent states honest: null `deserved_points` → no scatter (hero absent state); absent next_fixture →
  no card; non-domestic seasons carry no scatter — never a fabricated zero.
- No number rendered twice: the actual points total now appears only in the record strip and the YoY row
  (the mock-faithful value+delta pair); the hero verdict no longer restates it in any locale.
- Token discipline + i18n: colour = meaning (direction-aware green on YoY deltas), all new strings present
  in de/en/fi, verdict is a templated factual sentence (not fabricated prose), aria-labels translated.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Tabs are JS-free (radios + `:checked ~` CSS, mirroring the fixture `.seg-in` control): default Overview
  shown, focus-visible outline live (`.fx` on <body>), no orphaned selectors, works without JavaScript;
  the appended CSS is a pure append with no shared-block regression.
- `astro build` stays green across all three locales; TS sound (no orphaned `{points}` placeholder or
  unused param after the verdict trim).
- The screenshot done_when is environmentally blocked (headless pane cannot composite); substituted with
  live-DOM/computed-style checks (de/en/fi) + a reproducible geometry assertion on the built HTML (56
  coords, 0 out-of-bounds, 20 dots, trend+gap lines, verdict no longer restates the points value) —
  accepted as adequate for the code-quality check; a human eyeball on the live dev server before merge is
  advised (non-blocking).
- Doc/code/data three-way consistency for the featured-season note (active_work.md ↔ page selection ↔
  committed sample) restored.

## escalations
(none)

<!-- Deferred follow-ups (notes, not blockers — no CPO answer required to ship this PR):
  1. Mid-season trend line: when live/mid-season data (unequal games played) is wired, the export must
     serve the fitted line itself (slope + per-match intercept) so the deserved line stays true; today's
     committed sample is games-aligned (38 each), where the 2-point segment is exact.
  2. Featured-season default is now the current season (2025/26, gap -4). The season selector (#362) will
     let a reader reach the dramatic 2024/25 underperformance (gap -16) later.
  3. A visual eyeball on the live dev server before merge is worth two minutes (screenshots are
     environmentally blocked here). -->
