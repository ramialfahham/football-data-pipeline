# Acceptance evidence — refresh the committed export sample onto the four renamed columns

Branch `chore/refresh-export-sample-after-mr-b`, from main `b022909`.
Step 3 of the metric catalogue naming programme: MR **G**, pulled forward ahead of batch C on the
CPO's instruction ("116 merged, do the refresh").

⛔ **THE FIVE CRITERIA BELOW ARE THIS MR'S OWN.** The four criteria the CPO made STANDING are for
MRs B–F, the rename batches, and their subject is a rename being invisible. This MR's subject is the
opposite — a rename becoming visible again — so it uses the criterion he stated for it directly
("get that count back to 16 with Goalkeeping present"), expanded into commands. Criterion 5 was
REPLACED mid-task under his authority; see `contract.md` `amendments:`.

Everything below is read from the BUILT site under `site_v2/dist/`, from a test run, or from a
payload deliberately broken and watched.

criteria_demonstrated:
  - **Criterion 1 — 16 metric rows and a Goalkeeping heading are back, in all three locales.** Read structurally from the built pages, counting `<div class="mrow">` and listing every `<div class="mgroup">` inside each `<div class="cmp">` block. **BEFORE** (main `b022909`, 17 fixture pages per locale): **14 rows**, **6** group headings — `Goals, Shooting, Duels, Defending, Passing, Set pieces` — and `Goalkeeping present: NO` in EN, DE and FI alike. **AFTER** (19 fixture pages per locale): **16 rows**, **7** headings with `Goalkeeping` restored, `Goalkeeping present: YES`, in EN, DE and FI. ⚠ Those heading strings are English in all three locales — a real pre-existing defect this evidence originally reported without flagging, caught by `bi-analyst-reviewer`, verified independently, and filed as GitLab **#98**. It is not caused or fixed here; see `contract.md` `decisions_reserved`. Not a spot check: across all 19 pages the w1 row counts are `[16]` and the w2 row counts are `[16]` (min 16, max 16) in every locale, and `blocks with NO Goalkeeping heading: 0`. Every page renders both windows — 38 `cmp` blocks over 19 EN pages, exactly 2 each, so no page is silently missing from that aggregate.
  - **Criterion 2 — the 16 are confirmed by NAME, substring-safe.** Each label's occurrences on the built page minus the occurrences of any longer label containing it. EN renders exactly 16: `% Duels won, % Goals per shot on target, % Pass accuracy, % Save percentage, % Shots from box, Clean sheets, Ø Corners, Ø Corners against, Ø Defensive actions, Ø Duels, Ø Goals, Ø Goals against, Ø Key passes, Ø Passes, Ø Shots, Ø Shots on target`. DE and FI also render 16. ⭐ The method earned its keep on the BEFORE run, which reported `names a naive substring test would have FALSELY reported present: ['Ø Corners']` — the exact false positive that produced a wrong 16 on `!116`.
  - **Criterion 3 — no old key survives in the sample.** Counted as WHOLE TOKENS, because a plain count of `points_capture` also matches inside `points_capture_pct` and reported a false 25 on the first attempt. Tallying every token matching `(points_capture|clean_sheets|corner_kicks|corners|save_ratio|saves)[a-z_0-9]*` under `site_v2/src/data/`: **`corner_kicks_per_match` 0, `save_ratio` 0, `clean_sheets_share` 0, bare `points_capture` 0** — against 183 / 181 / 97 / 25 before. The new names are present in their place: `corners_per_match` 121, `saves_pct` 119, `clean_sheets_pct` 22, `points_capture_pct` 25, plus the `_this_season` / `_prev_season` / `_delta_yoy` yoy forms at 25 each.
  - **The before/after pair is NOT like-for-like, and that objection is answered rather than ignored.** The fixture SET changed underneath the measurement, so "14 became 16" could in principle mean nothing more than "the new fixtures carry more data". It does not, and the rendered-name sets settle it: EN before → after is `ADDED: ['% Save percentage', 'Ø Corners']`, `REMOVED: []`. The set difference is **exactly the two renamed fixture fields and nothing else** — `saves_pct` and `corners_per_match`. A richer-data effect would have added other names too; it added none. The causal claim rests on this and on the mutation below, never on the raw 14→16 pair.
  - **Criterion 4 — the measurement was watched FAILING.** A check that passes equally on the work and on its absence is not a check. `site_v2/src/data/fixtures/1576153.json` had its 4 occurrences of `"corners_per_match"` reverted to `"corner_kicks_per_match"`, the site was rebuilt, and the reference page went **16 → 15 rows** in both windows (the aggregate widened to `[15, 16]`). `Set pieces` kept its heading, as expected — `corners_against_per_match` is its surviving sibling. The file was restored from a byte copy (`corner_kicks_per_match` 0, `corners_per_match` 4), rebuilt, and the count returned to **16** in all three locales.
  - **Criterion 5 — the SET moves coherently.** `landing.json`, the `.gitignore` allowlist and the committed payloads all name the same 19 fixture ids. Settled by the build: `audit-seo: 67 built page(s) checked. OK.` — it fails on any internal link resolving to no emitted page, which is exactly the trap the sample's README says a local build cannot catch. Page-count driver went `/[lang]/[competition]/matches/[fixture] -> 51` before, `-> 57` after (19 × 3 locales).

## Gates

| gate | result |
|---|---|
| `npm test` (site_v2) | **76 tests, 76 pass, 0 fail** |
| `node scripts/check-page-specs.mjs` | 4 pages validated against their specs — OK |
| `astro build` | 66 pages built, `audit-seo` 67 checked — OK |
| `check_layer_contract.py` | OK |
| `check_registry_var_sync.py` | OK |
| `check_competition_type_seed.py` | OK |
| `check_copy_gate.py` | OK |
| `check_description_hygiene.py` | OK |
| `sync_metric_docs_blocks.py --check` | OK |
| `check_ui_i18n_metrics.py` | OK |
| `pytest -q` (repo root) | **1009 passed, 1 skipped, 14 subtests** — identical to the baseline measured on `b022909` before any edit, so no new failure |
| `check_task_artifacts.py` | run against `gitlab/main`, not `origin/main` — `origin` here is the dormant GitHub remote |

## ⛔ THE HANDOVER'S RECIPE DID NOT WORK, AND THAT IS THE FINDING

The recipe said: run the export, the sample carries the new keys. Run verbatim from the repo root it
exited **0** and reported **3,289 team + 5,066 fixture payloads written** — and changed **exactly one
tracked file**, `teams/33.json`. Every one of the 17 committed fixture payloads was untouched, mtimes
unchanged, still serving `corner_kicks_per_match` and `save_ratio`.

`fetch_fixture_payloads` (`scripts/export_site_data.py:806`) selects
`status_short in ('NS', 'TBD') and fixture_date >= current_date()` — upcoming fixtures only — and the
committed set was the 2026-08-18 matchday. **And the ids could not be re-exported at all**:
`mart_team_momentum` and `mart_team_season_record` are keyed on `upcoming_fixture_sk` and hold
PRE-match form, so a kicked-off fixture has no row. Queried against prod rather than assumed —
`1492306` and `1622620` each return **0 rows from both marts**.

⭐ The export mechanism was never at fault, which is why the fix is a set swap and not a code change:
of the 5,083 payloads on disk after the run, **exactly the 17 stale ones** carried the old keys and
all **5,066** fresh ones carried `corners_per_match` / `saves_pct`.

⚠ **Nothing is wrong in production.** `deploy:export` runs fresh and always emits upcoming fixtures
with whatever names prod holds. The missing rows existed only in the committed CI sample.

⭐ THE RULE THIS LEAVES: **an exit code of 0 and a large "written" count are not evidence that the
files you care about were written.** The export reported 5,066 successes while doing nothing to any
of the 17 files the task was about. Diff the specific artifacts, never the summary line.

## What the CPO decided, and what it cost

Put to him as a blinded two-way fork with the measurements above: **"Roll the set forward"**. The
`.gitignore` fixture allowlist now pins the 19 ids the fresh `landing.json` links (the 2026-08-28
matchday, 13 competitions), the 17 stale payloads are removed, and built fixture pages go 51 → 57 at
new URLs. 17 of the 19 carry a fully populated W1 (29/29 non-null); `1575140` (BL1) has a null W1 —
pre-season — which exercises the absent path deliberately.

⚠ **The residual, restated because it governs the next four MRs.** This closes the gap for `!114` +
`!116` only. Batches C–F rename more fixture payload fields and the count drops again on each.
Measured now so C's expected number is known rather than guessed: of C's three names only
`danger_zone_ratio` is one of the rendered 16 — `shot_accuracy` is a payload field the 16-row
contract in `metricRows.ts` deliberately drops, and `shot_share` is not in the fixture payload at
all. **C will take 16 → 15, with no heading lost** (Shooting keeps 3 of 4). A final refresh after F
is still owed, and it must be another roll-forward, for the reason above.
