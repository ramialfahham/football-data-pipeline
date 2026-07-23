# Review — feat/team-page-performance — 2026-07-23

> Team page Performance tab (frontend only; no export/dbt/test change), from CPO-approved mock
> f6348775, reusing the locked `METRIC_ROWS`. Three rounds. Round 1 caught the header/rank display
> (locked spec `14_team_stats.md` §5 forbids a single peer-count header, §4 requires per-row
> "{rank} of {team_count}") and the per-panel caption; round 2 caught the missing "below the games
> floor" absent state (§6). All fixed. All three required reviewers PASS at the final hash.

diff_sha256: f5e943aee347462742dd71bc07c0ed75bd9635b10dbf52873945a80ae810a3f9

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is within scope_paths (10 site_v2 files + the two task/handover artifacts); no
  export/dbt/test/guard/workflow path touched — consistent with the "frontend only" impact_map.
- No new §10 decision: the direction-aware rank conversion, the per-row "of {team_count}", the
  per-panel captions, and the §6 absent-state guard all IMPLEMENT the locked display spec
  (metrics_display.md + 14_team_stats.md) and match two existing sibling components — no new metric,
  naming, threshold, or mechanism. The dropped interpretive lede was approved with the plan.
- decisions_reserved intact: Squad deferred (#480), lede templating deferred, per-locale metric
  labels (#370) unchanged.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: all 16 rows in both panels trace to the committed sample (`benchmarks[]` +
  `{field}_delta_yoy`), which come from the mart via the export, not hand-typed; absent states honest
  (null save_ratio YoY → en-dash; below-floor season → the "not enough games" message; metric-absent →
  row omitted, never a zero bar).
- Direction-aware rank/fill/green verified against real data: goals against (lower_better) raw 14/20 →
  "7th of 20", 70%, green; corners against raw 13/20 → "8th"; save % (sparse) 13/16 → "13th of 16",
  25%, not green; 12 green fills total on the featured season. Green = beats median in the better
  direction only; red stays reserved for Loss.
- Per-row honest sample size (§5): no single peer-count header remains; each row carries its own
  "of {team_count}", so the save % row shows its true 16, not the 20 the other rows carry.
- The below-the-games-floor guard (§6) matches the sibling DeservedHero/YearOverYear pattern and fires
  for the sample's real `benchmarks: []` cup seasons; no naked % beyond the documented save_ratio
  exception; i18n complete de/en/fi with localized ordinals.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The JS-free segment survives the absent-state fragment restructuring: built-HTML child sequence is
  input#pf-league, input#pf-season, div.seg, div.win.pf-league, div.win.pf-season — all direct
  siblings (the `<>` fragment emits no node), so `#pf-*:checked ~ .pf-*` resolves; no collision with
  the outer `#tab-*` tab namespace or the fixture `#seg-w1/2`.
- `astro build` green across all three locales; empirical dist grep finds no `{team}`/`{n}`/`{rank}`/
  `undefined`/`NaN`/`[object` leaks; DE/FI strings render.
- TS sound: `benchByKey.size`, the `hasYoY` `.some`, the `leagueGroups`/`seasonGroups` split, the new
  `teamName` prop + call site, the `{field}_delta_yoy` Record cast (read only via `asNumber`); no
  leftover `groups`/`teamCount`/`rankedWithin` references; helpers null-safe (no divide-by-zero,
  degrade to en-dash).
- No CSS double-define: every `.vs-*`/`.ss-*`/`#pf-*` selector defined once; the grid-column widen +
  `.vs-rank` nowrap were in-place edits, not appends; shared blocks (`.seg-in`/`.win`/`.pagecap`/
  `.coming`) reused, not redefined.

## escalations
(none)

<!-- Non-blocking follow-up (raised by bi-analyst, not a defect — both fields are real and bound):
  The vs-league row follows the APPROVED MOCK f6348775 — the league MEDIAN VALUE column + a rank-based
  fill bar. The older wireframe `14_team_stats.md` §4/§5 (and 00_overview.md) instead describe a
  vs-median DELTA column + a p25–median–p75 spread bar. `league_p25`/`league_p75` are exported and
  typed but currently unread; `vs_median_delta` drives only the green colour. The mock is the CPO-
  approved design and §1's own "rank over percentile, honest at N≈18" rationale favours what was built,
  so this shipped as-is — but the wireframe doc should be reconciled to the approved mock. A doc task,
  not a code change. -->
