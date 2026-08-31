# Review — refactor/metric-label-on-goal — 2026-08-31

> **STEP 5 of the metric catalogue naming programme.** The English label "on target" → "on goal" on
> nine catalogue `label_en` rows and on the four `METRIC_LABELS_EN` values that render. The mirror
> image of step 4: that programme moved `metric_id` and PROTECTED `label_en`; this moves `label_en`
> and protects `metric_id` everywhere. Branched from main `649b11c`.

diff_sha256: 766b2b2b30338f4cf03082f77445881bd8fbf14b683d6c25037d87042508d836

rounds: 2

⭐⭐ **THE SCOPE IS WIDER THAN THE RECORDED RULING 2, BY A RULING TAKEN THIS SESSION.** RULING 2's
scope was confirmed *"in the catalogue"*. Measured before proposing anything: the catalogue is **not**
what the website renders — `strings.ts`'s `METRIC_LABELS_EN` is — and four of the nine labels render
today, so catalogue-only would have left every page still reading "Shots on target", which is the
mismatch the ruling exists to remove. Shown both options and their consequences, the CPO selected
**"Catalogue + website (recommended)"**. Recorded in `escalations.log` with the question verbatim,
the selected option's exact title and text, the declined alternative, and an explicit note that it
was a SELECTION rather than free text.

⚠ **THE HANDOVER'S STEP-5 LIST WAS STALE AND WAS NOT USED.** It named nine metric_ids; **six were
superseded** by step 3's and step 4's renames. **The COUNT was right and the NAMES were wrong** —
the tell worth keeping, because a stale list can agree with reality on the summary number and
disagree on every element. The nine were re-derived from the seed.

## ⛔⛔ ROUND 1 FAILED 3–1, AND THE MISS IS THE LESSON

`bi-analyst` found a **third live copy** of the id-vs-label claim — `DeservedHero.astro:43` — that
`decisions_taken §2` rewrites in two other places. It was absent from my census entirely.

⭐ **WHY: I matched `"on target"` and `"on-target"` and never matched `"on_target"`.** An enumeration
of spellings, which loses by one variant — the exact failure `feedback_fix_the_class_not_the_instance`
records holing a guard four rounds running. Re-swept with the PATTERN `on[\s_-]?target`:
**136 occurrences, 5 of them CLAIMS about the split.** Two already rewritten; two stale and now
fixed; **one (`check-page-specs.test.mjs:179`) still TRUE and deliberately untouched**, because it
compares the id to the KEY rather than to the user-facing term — named in the evidence so its absence
from the diff reads as a decision, not another miss.

Two smaller round-1 findings, both accepted and fixed: the **ASCII mockups lost their box alignment**
("on goal" is two characters shorter), measured and re-padded to base columns; and **the new ruling
was recorded as narration rather than the CPO's words**, now corrected.

## scope-auditor
VERDICT: PASS

**Round 1 PASS**, having verified RULING 2 and the new session ruling by content in `escalations.log`,
the `label_i18n_key`/`description` protections, and the `99_gaps_register.md` reversion. It raised
the evidentiary weakness in how the new ruling was recorded — "a weaker evidentiary form" than the
file's convention — which is what prompted the correction.
**Round 2 PASS**, including an explicit ruling on the contract amendment.

risks_checked:
- The `amendments:` reasoning judged against the actual diff: *"both are comment-only fixes
  documenting an already-ruled label change, not new user-visible decisions; no new CPO authority
  was needed and none was smuggled in."*
- The corrected `escalations.log` entry checked for overclaiming in the OTHER direction — it labels
  the entry a selection rather than dressing it as a quoted free-text sentence.
- ASCII re-padding verified by character count across three files: closing borders land on the base
  column.
- `scope_paths` reconciled 1:1 against the full `diff --git` file list; no stray file.
- The seed checked column-by-column against `protected_override`: `metric_id`, `label_i18n_key` and
  `description` byte-identical on all nine touched rows.
- `decisions_reserved` items (the `description` column, the `label_i18n_key` rename) confirmed
  untouched in the diff, as declared.
- Credential sweep across the patch; impact-map/A6 trigger check — no new structural surface.

## bi-analyst-reviewer
VERDICT: PASS

**Round 1 FAIL** — the finding that drove round 2, above. **Round 2 PASS**, and it did not take the
fix on trust: it re-ran its own full-repo sweep rather than checking mine.

risks_checked:
- Independent case-insensitive sweep for `on[\s_-]?target` over the whole repo, every non-`.claude`
  match inspected by hand: *"the pattern that escaped round 1's enumeration-based census is now
  genuinely closed."* ⭐ It also identified a false positive in the raw count worth recording —
  `README.md:145` matches on "ingesti**on target**", a substring, not a metric reference.
- Both rewritten comments read directly: each keeps the load-bearing instruction and replaces only
  the dead reason; "legacy key name" is accurate because the key literally still reads `on_target`.
- `check-page-specs.test.mjs:178-181` read directly and confirmed still true, correctly unedited.
- ASCII box widths **re-measured with its own regex** rather than trusting my column numbers —
  every row in each box, borders included, matches the fixed inner width (44 / 51 / 51).
- The four chrome strings confirmed unchanged and honestly disclosed as flagged-not-folded-in.
- Verified against the actual `dist/` build, not the evidence prose: EN 38 "on goal" / 0 "on target",
  DE and FI 0 of either. It also read the built team page directly and confirmed the three unrendered
  labels genuinely reach no page today — a tighter check than my own "coming soon" paraphrase.
- Read `site/i18n/en.json` directly to confirm the frozen corpus declares three of the four ids
  nowhere, independently verifying that the byte-identical gate cannot pin their new wording.
- All six edited wireframes traced 1:1 to a real catalogue or `METRIC_LABELS_EN` change.

## analytics-engineer-reviewer
VERDICT: PASS

**Round 1 PASS** after a field-by-field seed verification; **Round 2 PASS** confirming the warehouse
surface is untouched since.

risks_checked:
- Seed diff byte-for-byte: nine `label_en` cells, **0** other cells; `metric_id`, `label_i18n_key`,
  `description` and every formula/format/direction column unchanged. Read the full current seed, not
  only the diff.
- Confirmed the first apply's defect (three `description` cells rewritten) is genuinely closed by the
  field allowlist.
- Full patch scanned for any `.sql`/`.yml`/macro/model file — none in either round.
- `sync_metric_docs_blocks.py` grepped for `label_en`: zero references, so `metric_columns.md` cannot
  regenerate from a label change.
- `fetch_glossary()` read directly and confirmed the sole reader of the metric catalogue's
  `label_en` — a pure select/serialize, no consumption-layer computation. Every other `label_en` hit
  traced to the unrelated `competition_types`/`confederations` seeds.
- ⭐ An extra check it ran unprompted: the seed's own
  `metric_catalogue_label_en_unique_within_entity` test, checked by hand against the nine new values
  within their team/player partitions — no collision introduced.

## football-analytics-expert-reviewer
VERDICT: PASS

**Round 1 PASS** on the domain question; **Round 2 PASS** on the delta.

risks_checked:
- Judged the new wording as football English: "on target" and "on goal" name the identical provider
  event, so no meaning changes. "On target" is more idiomatic in British/international coverage and
  "on goal" is the American convention, so the new wording reads slightly unfamiliar to a European
  fan — but none of the nine is factually wrong or misleading, and the naming call is squarely the
  CPO's under §10. It specifically scrutinised "Shots on goal faced" and "% Goals per shot on goal".
- Field-by-field seed check: only `label_en` moves; no formula, denominator, coverage caveat or
  direction touched. No residual "on target" in any `label_en` cell.
- RULING 2 read verbatim in `escalations.log` and matched against the contract's quote, including the
  scope confirmation and the German/Finnish exclusion — no overstatement.
- Judged the disclosed label-vs-description split acceptable to ship: the two terms name the same
  event, so it is a wording inconsistency rather than a wrong claim, it is disclosed in
  `decisions_reserved` with a recommended follow-up, and folding it in would repeat the scope-creep
  failure this same programme was FAILed on three times.
- Confirmed the corrected ruling record "reads honestly against the file's own convention".

## platform-reviewer
VERDICT: PASS

Not routed in round 1 — no machinery file was touched. Routed in for round 2 because the fix edited
a test file, which the contract's amendment predicted.

risks_checked:
- `check-metric-labels.test.mjs` diff confirmed comment-only: assertion code, regex, `col`,
  `declared` and `bad` logic byte-identical. The rewritten comment's claim verified against the code
  it sits above — the test never reads label VALUES, so "the invariant is unchanged" is correct.
- ⭐ **The §3 gate analysis verified STRUCTURALLY, not just observationally.** It read the
  byte-identical test's loop and `site/i18n/en.json` directly: three of the four changed ids are
  absent from the frozen corpus entirely and the fourth is skipped by a hard-coded name check, so
  none of the four is ever compared.
- ⭐ **The mutation claim verified against code rather than narration**: it walked all seven tests
  against a hypothetical `"Ø Bananas per fortnight"` and confirmed each one passes — the wording of
  the four labels is pinned by nothing, while emptying one fails the non-empty assertion.
- ⭐ **The pytest-not-rerun reasoning checked at the one place it was actually at risk**, which is
  stronger than my own file-extension argument: `tests/test_governance_hooks.py` DOES read
  `DeservedHero.astro` verbatim and regex-matches `"metrics.*.label"` literals against a floor of 18.
  It verified the round-2 comment adds no new such literal and the matched code line is untouched.
- Whole 923-line patch read end to end: no `.claude/hooks/**`, workflow, `.gitlab-ci.yml`,
  dependency manifest, lockfile, `astro.config.mjs`, `firebase.json`, `tsconfig.json` or `.gitignore`.
- `check-page-specs.test.mjs:179` confirmed key-only and correctly unedited.
- No credentials or permission widenings; no new pages, routes, fetches or build steps.

## escalations

**None raised.** The one §10 question — whether the website's rendered labels move with the
catalogue, given RULING 2's scope was "in the catalogue" — was put to the CPO before any file was
touched and is recorded with its question, options and outcome.

⛔ **FLAGGED FOR THE CPO, deliberately NOT folded in** (both disclosed in `decisions_reserved` and
confirmed untouched by two reviewers):
  - **The seed's `description` column.** A row's label now reads "on goal" while its own description
    says "shots on target", and `persist_docs` publishes those to BigQuery.
  - **Four CHROME strings in `strings.ts`'s `Dict`** — `axPlay` ("Shots on target difference /
    match", the hero chart's x-axis) and the three `heroVerdict*`/`heroCaption` strings. When the
    team Performance surface ships, that axis will read "Shots on target difference" beside a metric
    row reading "Ø Shots on goal difference". Neither renders today.

⚠ **AND WHAT THIS MR CANNOT PROVE, carried rather than closed:** the wording of the four changed
rendered labels is pinned by **no test** (mutation-verified by two reviewers independently), and
**three of the four render on zero built pages**. Only `Ø Shots on goal` is proven by the dist read.
