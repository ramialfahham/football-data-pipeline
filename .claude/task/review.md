# Review — chore/refresh-export-sample-after-mr-b — 2026-08-28

> Step 3 of the metric catalogue naming programme, MR **G** pulled forward ahead of batch C on CPO
> instruction. Refreshes the committed export sample onto the four columns `!114` and `!116`
> renamed. Branched from main `b022909`.
>
> Mid-task the handover's recipe was found to be impossible — the export emits upcoming fixtures
> only and the committed ids' form rows no longer exist in prod — so on CPO authority
> ("Roll the set forward") the sample's fixture SET was replaced: 17 stale payloads out, 19 current
> ones in, `landing.json` regenerated, the `.gitignore` allowlist rewritten.

diff_sha256: 42f009ab1b56c643b97afa893cb5e8cb77ae87051e25116b4420296171ef129e

rounds: 2

> **Round 1: both reviewers FAILed, and both findings were real.**
> `scope-auditor` caught the contract contradicting itself — the amendment authorising the
> `.gitignore` edit left a neighbouring `done_when` bullet still asserting "no new tracked file and
> no `.gitignore` edit". Re-reading the whole block rather than the one line it named found **two
> more** false bullets, both fixed.
> `bi-analyst-reviewer` caught a pre-existing i18n defect the evidence file had been reporting
> without flagging: the seven metric group headings render in ENGLISH on DE and FI pages. Verified
> independently, filed as **GitLab #98**, and deliberately NOT fixed here — the components are
> outside `scope_paths` and the German/Finnish wording is a §10 naming decision. Disclosed in
> `decisions_reserved`, which previously said "none". Its secondary finding (a stale
> "reduced by hand" claim in the sample README, contradicted by `shape_landing_payload`) was
> confirmed and corrected.
>
> ⚠ **A ROUTING DEVIATION, DECLARED RATHER THAN LEFT IMPLICIT.** `acceptance_evidence.md` is in
> `review_exclude_paths` — reviewers are not normally shown it. Both were pointed at it directly
> this time. That is what surfaced #98, since the defect was visible in the evidence's own output
> and nowhere in the diff. Worth knowing before anyone reads this as standard routing.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-1 finding (falsified `done_when` bullet) re-verified against the current diff by independently recounting the 17-removed/19-added fixture set — now accurate, not just reworded. Independently counted: 16 explicit removals + 1 rename-away (`1493034.json`) = 17 gone; 18 new files + 1 rename-in (`1493106.json`) = 19 added.
- Re-read every other `done_when`/contract bullet, not just the named one: the export-recipe bullet now correctly names both the `teams,fixtures` run and the second `--entities landing` run; the "drop the ignored bulk" bullet now correctly describes the scoped `git ls-files --others --ignored --exclude-standard` equivalent instead of the blocked `git clean -fX`.
- `decisions_reserved` disclosure of GitLab #98 checked against scope_paths and the working agreement's §10 naming-decision rule — deferring it is correct, not scope-dodging, since the affected components (`MetricComparison.astro`, `TeamPerformance.astro`) are outside this MR's scope, and fixing it here would itself have been an undisclosed §10 naming call in files this MR does not own.
- File inventory sanity: globbed the actual tree — 19 fixture files, 1 team file (`33.json`), 3 top-level JSON + `README.md` = 24 tracked files, matching README's own "Tracked today, 24 files" claim.
- `.gitignore` diff vs contract narrative: counted the 19 new allowlist entries — matches. `manifest.json`/`slug_map.json` additions declared in `amendments:` rather than slipped in silently.
- Amendments' authority claims checked — none assert CPO authority they don't have; the substantive roll-forward decision correctly cites "the CPO, this conversation," and the two correction amendments correctly claim no authority was needed.
- Secrets sweep run over `site_v2/src/data/**`, `.gitignore`, `contract.md`, `escalations.log` diffs — no credential-shaped strings found.
- Threshold declarations (no new mechanism, no recurring cost) checked against the diff — confirmed no new script, CI job, or schedule introduced anywhere in the changed files.
- `scope_paths` against every file touched — no out-of-scope file edited; no `dbt_project/**` or `scripts/**` touched.
- Numbers cross-check: `183/181/97/25` stale-key counts, `19 fixtures/13 competitions`, `51→57` page count, `16→14→16` row counts, and the `1575140` null-W1 fixture are consistent across `contract.md`, `escalations.log` and `acceptance_evidence.md`.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round-1 finding (English group headings on DE/FI) re-verified directly against the actual built output on disk (`site_v2/dist/de/bundesliga/matches/2026-08-28-bayern-munchen-vs-vfb-stuttgart/index.html`): `mgroup` literals are `Goals, Shooting, Duels, Defending, Passing, Set pieces, Goalkeeping` on the DE page, unlocalized, confirming the disclosed defect is real and unchanged by this MR. Deferral is legitimate: the offending code is outside `scope_paths`, fixing it would require inventing German/Finnish wording — a §10 CPO naming call — and the gap is correctly filed (GitLab #98) and disclosed including the honest 34→38 multiplier, rather than netted off or hidden.
- Row/heading recovery independently re-derived from the built dist HTML rather than trusted from the evidence doc: counted `class="mrow"` (32 = 16×2 windows) and `class="mgroup"` (7×2, Goalkeeping present) on the same DE fixture page — matches `acceptance_evidence.md` criterion 1 exactly.
- Honest-null handling on the roll-forward's deliberate absent-path fixture (`1575140.json`, Bayern home `w1: null`): checked the rendered EN page directly — the first 16 `mval home` cells for the W1 window render `–` (dash), never a fabricated `0`; W2 values populate correctly (e.g. `12/34` clean-sheets count-fraction) — satisfies "nulls as –, never fabricated zeros" and the count-fraction volume-visible rule.
- Set self-consistency: cross-checked `landing.json`'s 19 `fixture_id`s against the `.gitignore` allowlist's 19 entries and the 19 files actually present under `site_v2/src/data/fixtures/` — all three sets are identical (sorted-list comparison), and `teams/33.json` is the sole tracked team file, matching README's "24 tracked files" claim.
- Stale-key removal and new-key binding: grepped the full `site_v2/src/data/` tree for `corner_kicks_per_match|save_ratio|clean_sheets_share|"points_capture":` — zero hits. Confirmed the four new names exist in `teams/33.json` and multiple fixture payloads, and traced them to the export's `select * from mart_team_profile` / `mart_team_momentum` — not fabricated, genuinely export-producible per the binding rule.
- Label fidelity: verified `metricRows.ts`'s `labelKey`s for the two rows that flip in/out (`saves_pct`, `corners_per_match`) resolve in `strings.ts` to `"% Save percentage"/"% Gehaltene Torschüsse"/"% Torjuntaosuus"` and `"Ø Corners"/"Ø Ecken"/"Ø Kulmapotkut"` — matching exactly what the evidence claims was added, so the before/after causal isolation (added exactly these two labels, removed none) is not overclaiming.
- README correction verified against source: `shape_landing_payload` returns literally `{"type": ..., "upcoming": ...}` and nothing else, confirming the rewritten README's "NOT hand-reduced" claim is true and the prior line was indeed false as the amendment states.
- `check_ui_i18n_metrics.py` read directly: it validates `site/` (legacy MVP) metric label/description completeness, not `site_v2/` group headings — confirms the i18n gap found is genuinely ungated by any existing CI check, consistent with the disclosure rather than contradicting it.
- No display wording changed by this diff: `metricRows.ts`, `i18n/strings.ts` and all `.astro` components are untouched, so no new or changed user-visible string requires a catalogue citation here.
