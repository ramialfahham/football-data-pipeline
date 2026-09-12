# Review — chore/115-step8-sweep-frontend-ingestion — 2026-09-12

diff_sha256: be548b7966194a71398e1220eed648e4be035b1ef896121989b02cb5524344f3

rounds: 3

bi-analyst-reviewer: PASS at round 1 (`c931e1ef…`), PASS at round 3 (every `site_v2/src` blob SHA
  identical to round 1's; the contract's false-why declaration covers the two files it flagged)
platform-reviewer: FAIL at round 1 (`c931e1ef…`), PASS at round 3
data-engineer-reviewer: PASS at round 1 (`c931e1ef…`), PASS at round 3 (all 18 ingestion blob
  SHAs identical to round 1's)
scope-auditor: FAIL at round 1, PASS at round 2 (`a6f9a5d5…`), PASS at round 3 (its first
  round-3 verdict flagged six string literals in `design-mocks` as unswept; re-classified on
  re-read as printed check labels and rendered mock text — program output, outside the
  comment/docstring definition and protected by criterion 2 — and withdrawn)

Round 2 → 3. The platform-reviewer's round-1 finding: eight history lines in `design-mocks` the
guard cannot see — CSS comment CONTINUATION lines inside emitted stylesheet strings
(`gen_top_players.py:343`, `gen_top_teams.py:331`, `gen_matches.py:260`,
`gen_competition_hub.py:334`) and a bare triple-quoted block comment in two generators
(`gen_top_players.py:84-106`, `gen_top_teams.py:79-99`). All eight swept by hand; the rendered
mocks re-diffed (identical, CSS comments stripped); `ast` shows the two bare strings as no-op
statements; criterion 2's exception list is now thirteen lines in six files; an amendment names
the guard's blind spot. Whole-tree count still (0, 0).

Round 1 → 2 (contract only): `decisions_taken` names the false-why correction rule (sweeps 1
and 3 applied and declared it; omitted here) and the two files it applied to (`index.astro`,
`types.ts`); a second amendment bullet.

### platform-reviewer — round 1
Verdict then: FAIL (resolved at round 3)
- `site_v2/scripts/*.mjs`: comment lines only; the parsers read double-quoted entries, none
  depends on a comment. The pin at zero: the `<=` half is the whole guard, the `==` half implied;
  nothing assumes a non-zero pin; the hook still fails open. The five declared string lines each
  traced to its enclosing `MOCK_CSS`/`PAGE_CSS`/`ROW_CSS` string and its `<style>` sink; "rendered
  identical with CSS comments stripped" is the right comparison; the emitted `.html` is gitignored.
  The two non-running generators fail on `main` identically (registry drift: BPL/EKS/TSL,
  `intercontinental_super_cup`); `design-mocks` is referenced by no CI job — not a blocker.
  `check_*.py`: docstrings and `#` only; every checker strips `/* */` before scanning.
- Findings 1–4: eight further history lines in comment position that neither the pin nor the
  hook can see (CSS continuation lines inside strings; a bare triple-quoted string that is not a
  docstring) → all swept, declared, and proven at round 3.

## bi-analyst-reviewer
VERDICT: PASS (round 1)
risks_checked:
- `strings.ts` hunks (patch 1779–2176): every changed line a `//`, `/**` or `*` comment; no
  `key: "value"` entry touched in EN, DE, FI, `METRIC_LABELS_*` or `playerMetrics.*`;
  `metricRows.ts` header comment only, the 16-row array untouched.
- Provenance as rule: "Supplied copy (§10)", "confirmed copy", "APPROVED COPY (#41)", "(LOCKED)" each
  still signal settled wording; none reduced to unmarked prose.
- ≥12 rewrites read end to end (em dash, brand suffix, `kunto`/`muoto`, `Der Top-Spieler`, per-board
  stacking, `overflow-wrap` measurements): rule, number and reasoning survive.
- `index.astro`: both blocks imported (33–34) and rendered (73–74), no hunk in imports or JSX; the
  corrected claim is true of the code as it stood — a content fix, not user-facing, no fabricated
  field, so not a display/binding defect.
- Every `.astro` hunk a `//` frontmatter or `{/* */}` comment; no markup, prop or expression.
- `system.css` boxed headers measured character by character: both lines keep their width (71 and
  74), borders unchanged; no rule/property/value line altered.
findings:
- none

## platform-reviewer
VERDICT: PASS (round 3)
risks_checked:
- Hunt 6 grep re-run over `design-mocks/*.py`: the eight comment-position lines gone (each read
  from disk); the fourteen remaining hits are rendered mock content, printed check labels or a
  fixture URL — string literals outside §1.2, classified in round 1. No ninth line.
- Regenerated patch, design-mocks region: every `+`/`-` line a `#` comment, docstring, CSS
  `/* … */` comment inside an emitted stylesheet string, or a line of the two no-op bare strings;
  no selector, property, value, assertion, regex or expected string changed; the delta versus
  round 1 is exactly the eight lines; only four generators carry new blob SHAs.
- Criterion 2's exception list counted from the patch: nine CSS lines + four bare-string lines =
  thirteen in six files, matching the contract exactly; the bare strings are not `body[0]`, so
  `ast` sees `Expr(Constant)` — the blind spot the amendment names; widening reserved.
- Proof shape valid: the rewritten continuation lines sit inside the same `/* … */` blocks, the
  bare strings are never emitted, the `.html` stays gitignored.
- Round-1 items untouched by the delta stand: scripts comment-only, the pin at zero, the hook
  fails open, the two non-running generators pre-existing with no CI consumer, no dependency,
  credential or hosting change.
findings:
- none

## data-engineer-reviewer
VERDICT: PASS (round 1)
risks_checked:
- Every hunk in the 18 ingestion files (patch lines 851–1451): comment or docstring only; the
  three hotspots (`bigquery.py:270` REMOVED block, `squads.py:40` REMOVED block, `registry.py:34-40`
  field comments) comment-only; `append=False,` beneath the reworded `completeness.py` comment
  untouched.
- Safety reasons still true against the code: the three delete helpers absent from `ingestion/`
  (referenced only in `REMOVED:` comments); `load_json_to_bq`'s `append` still keyword-only with no
  default; `result_is_complete` unchanged and the empty-response rule literally true; the
  `(rows, complete)` docstrings and the rate-limited-HTTP-200 mechanism intact; the 29-events and
  "no players vs we lost the players" sentences survive.
- Dates that were data became number-preserving phrasing ("five nightlies", "sit idle for months");
  `~23 of 1,265` untouched — the same pattern as sweeps 1–3.
- `registry.py`: both cost fields still flagged as governed decisions; `ingest_active` now points at
  §10 explicitly; defaults and types unchanged.
- No fetch/write/delete/gate/skip/table/key/quota change anywhere.
findings:
- none

### scope-auditor — round 1
Verdict then: FAIL (resolved at round 2)
- Scope, the five declared string lines, the two non-running generators, credentials, thresholds,
  `decisions_reserved`: all clean.
- Finding 1–2: `index.astro:9-11` and `types.ts:283-289` replace a false build-status claim ("Top
  teams … not built") with the true one — a content correction, not attribution-stripping, and not
  named in `decisions_taken` or `amendments`. → The contract now names the rule sweeps 1 and 3
  applied and declared ("a why that is false as written is corrected, not preserved") and both
  files; re-audited at round 2.

## scope-auditor
VERDICT: PASS (round 3)
risks_checked:
- Round 3 — contract criteria 1–2 and `decisions_reserved` re-read against the six disputed lines
  (`check_home.py:40`, `check_teams.py:100`, `check_players.py:97,111`,
  `gen_competition_hub.py:232`, `gen_competitions.py:700`, `gen_sitemap.py:62,81`): each is a
  `print`/`check` argument or `<p>` text inside an emitted HTML string — printed or rendered
  output, which criterion 2 forbids changing; the comment/docstring scope excludes them by
  definition, not by oversight. The first round-3 verdict misapplied the guard's blind-spot
  precedent (CSS `/* */` comments and a no-op bare string — discarded before rendering) to a
  materially different class; withdrawn.
- Round 3 — the round-2 PASS stands on re-check: scope unchanged, false-why correction true and
  declared, no credentials, no undeclared threshold or mechanism, `decisions_reserved` untouched.
- Round 2 — delta contract-only: the file list and every non-contract `index` line unchanged
  from round 1.
- Round 2 — the false-why rule now declared and named for both files; the precedent checked on
  disk (`sources.yml`'s "reads them" language; `test_refetch_cadence.py`'s threshold docstring) —
  the same rule already applied and merged in `!178`/`!180`, not a new licence.
- Round 2 — the corrected claim true: `index.astro:33-34,73-74` imports and renders both blocks;
  `TopTeams.astro` exists.
- Round 2 — two amendment bullets account for the contract's changes; `protected_override: none`
  and both thresholds hold; reserved decisions untouched; no credential-shaped content.
findings:
- none
