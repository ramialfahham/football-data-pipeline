# Review — metric labels come from the catalogue, per locale (#370 slice)

branch: feat/370-metric-labels-from-catalogue
diff_sha256: 288339a7cf2e810f6a3c73ed62d6f7725ac9395e0655de729f2dea1f9fb3d262
rounds: 3
rounds_cap_override: >
  Not needed for a cap breach — this is round 3. Recorded because the round count restarted:
  this branch ran twelve rounds before PR #878 merged, was rebased onto the new rules, and was
  reviewed fresh. The CPO authorised finishing it ("finish 370", then "ok go ahead").
  What changed between the two histories is the point of #878. Before it, reviewers received
  38,932 lines to review 839 lines of code, and rounds 6-12 found only defects in this branch's
  own paperwork. After it they receive 1,409 lines, and all three reviewers reached a verdict on
  the code in one round. `bi-analyst-reviewer` and `scope-auditor` PASSed first time.
  `platform-reviewer` FAILed on a real defect this branch introduced — an entry header form that
  `report_process_health.py` mis-parses into a phantom branch — and its two follow-ups were
  resolved without moving the hash, because `escalations.log` is hash-excluded but review-visible.
  That split is exactly what #878 built, and it meant two verdicts survived three fix passes.

> **All three required reviewers PASS at this hash.**

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- All 18 `labelKey`s read against the `label_i18n_key` COLUMN of `metric_catalogue.csv`: every one
  declared verbatim, including the two hero-only keys and the deliberate `metric_id
  shots_on_goal_per_match` → `metrics.shots_on_target_per_match.label` mismatch. The round-1
  inverted-key defect has not returned.
- Field bindings behind the changed surfaces are real in `mart_team_profile.sql` and pass through
  `export_site_data.py`; no sample-only key introduced, no `field` value touched.
- The locked 16-row contract checked row by row against `metrics_display.md`: order, groups, tier
  shape (4×t1 / 9×t2 / 3×t3), formats, directions, `denom` and row-10 `sublabel` byte-identical.
  Only `label:` left.
- Built output, all three locales, all 19 render slots: hero tiles, both team `.vs-row`/`.ss-row`
  blocks and the fixture page's 16 `.mlabel` values are localised in the locked order.
  `grep -rE 'metrics\.[a-z_]+\.label' dist` → 0.
- No English regression: every `METRIC_LABELS_EN` value byte-identical to the `label:` it replaces.
- The hero block names the metric consistently on all four strings in all three locales, read from
  the built HTML; no superseded form survives anywhere in `dist/`.
- Rendering read from the evidence artifact, not re-derived: the 560px stack fires (96px → 149px
  measured), 0 overflow above 1px on every container, 0 unmeasured, no sideways scroll, 0 mid-word
  breaks. The remaining `.vs-row` breaks clip nothing and are CPO-ruled filed (#876).
- Wording authority for every changed user-visible string: 10 DE and 10 FI byte-identical to the
  validated corpus, the rest carrying a quoted CPO answer in `escalations.log`.
- No metric added or removed on any surface; the spec additions declare what already renders.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Rebase integrity of `tests/test_governance_hooks.py`: a single pure insertion hunk, 113 added
  lines, zero removed. All thirteen of #878's test functions present by name; #370's four present.
  Nothing lost from either side.
- The three Python floors fail on revert, traced rather than assumed: `MIN_METRIC_KEYS`'s fixture
  keeps the chrome dicts healthy so control reaches the metric block, and setting the floor to 0
  makes `main()` return 0 and the test red.
- Three-parser parity traced as a chain: `check-metric-labels.test.mjs` pins `labels.EN == asked`,
  test 6 pins `check-page-specs.mjs`'s subset to it, and the Python test pins its own to `asked` —
  all three anchored to the same set rather than agreeing by luck.
- The catalogue cross-check is not passing by luck: `label_i18n_key` is column 2 and columns 0-1
  never contain a comma, so the naive split is safe for this column order; the ≥50 floor has real
  headroom at ~80 declared keys.
- Fail direction: the new test file runs under `node --test` from `prebuild`, so it fails CLOSED on
  the build and in both build workflows; `check-page-specs.mjs`'s new early returns exit 1;
  `check_copy_gate.py` returns 1 on both new branches.
- Re-run and interruption safety: every changed script is a read-only checker holding no lock.
- Build health: 10 built pages across 3 locales unchanged; no new dependency, no lockfile change.
- Header parsing re-derived independently after the fix: 53 headers, exactly five with a non-branch
  token, four distinct junk keys, all pre-split; both two-day headers parse to the real branch.
- Both buckets recomputed from the log; the corrected figures reconcile with the instrument.

## scope-auditor
VERDICT: PASS
risks_checked:
- Silent §10 copy: all 54 `METRIC_LABELS_*` values checked against `escalations.log` and against
  `site/i18n/{de,fi}.json` byte-for-byte. Every DE/FI string is CPO-supplied verbatim, on the
  "Approved, record it" list, or identical to his validated corpus; all 18 EN labels identical to
  the values they replaced.
- Invented metric keys (A1): 13 of 18 `labelKey` values checked against the catalogue column,
  including the deliberate id/key mismatch. All declared; the seed is unedited.
- Rebase content loss: `escalations.log` carries both #370's entry and #878's, complete.
- Scope and amendment authority: all 17 diffed files inside `scope_paths`; each of the five
  amendments traced to a quoted ruling or a standing rule.
- Undeclared threshold / new mechanism: no dependency, workflow, permission, cadence or query
  change, and the `validateSpec` rendered-key walker the log reserves to the CTO was not smuggled in.
- `decisions_reserved`: each of the nine items checked against the diff; none is decided here.
- Consumption-layer contract (A5): `metricLabel()` is a keyed lookup with no derivation; zero
  residual `def.label`/`row.label` in `site_v2/src`; four render sites matching the `impact_map`.
- Doc-sync: `metrics_display.md` updated per the ruling, and `north_star.md`'s "16 findings" claim
  still true against the gate's four checks over the 54 new strings.

## escalations
(none)

## owed — recorded, none blocking
- `check-metric-labels.test.mjs:63` carries a half-deleted sentence from the history strip.
- `metrics_display.md` and the `strings.ts` FI block still carry a little review narration, against
  the CPO's standing "a correction replaces" rule. The test file's neighbours already read that way
  on `main`, so that half is a pre-existing house pattern rather than drift from this branch.
- `report_process_health.py`'s header regex is narrower than the forms a human writes: five
  historical headers carry no branch token, so the pre-split baseline it prints (1.24) is understated
  by roughly 10%. Fixing it means widening the regex plus a test pinning header parsing — nothing
  covers `rulings()` today — or reserving an explicit no-branch key. Advisory only; no gate reads it.
  The five historical headers must NOT be edited: they are other branches' durable records.
- `check-page-specs.mjs`'s `MIN_EXPECTED_METRIC_KEYS` floor is not pinned by a test that fails on its
  removal, mirroring the pre-existing `MIN_EXPECTED_KEYS`. Both are fail-closed and neither absence
  opens a hole; pinning them needs a reshape of the checker.
