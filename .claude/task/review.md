# Review — docs/incomplete-data-rule-in-the-metric-doc — 2026-09-08

diff_sha256: 72351c2d8defe7195ee6bae592f98aec703817aa2b47b6b57b4830875c53f0a2

rounds: 2

⚠ **DOCUMENTATION MR, but the documentation makes technical claims about the warehouse**, so
`analytics-engineer-reviewer` was briefed to ignore prose and check every statement against the
code. That is what found both of its failures.

## analytics-engineer-reviewer
VERDICT: PASS (round 2)
risks_checked:
- ⛔ **ROUND 1: it found I had reintroduced the exact defect the rewrite exists to fix, one line
  below the fix.** I corrected the canonical-model table, then wrote *"a player metric is added to
  the atoms model"* — false for most of the player catalogue. The atoms model's own docstring says
  atoms are the SUMMABLE counts only and that ratios, per-90s and composites are *"derived where
  consumed"*. It listed them: every `_pct`, every `_per90`, `scorer_points_player`,
  `defensive_actions_player`, `cards_player` — all in the COMPOSING model.
- **ROUND 2** verified the replacement against the model code rather than the docstring paraphrase:
  the atoms model's final select is plain `sum`/`countif` columns with no ratio present, the
  composing model derives five `_pct` and eleven `_per90`, and `mart_player_career:138` really does
  derive its own `minutes_per_appearance` — so both halves of the sentence hold. It searched
  specifically for a metric fitting NEITHER half and found none.
- ⭐ It also checked the paraphrase for drift against the atoms docstring — the failure mode where a
  restatement is true in isolation but softer than the original. None found.
- ⚠ It named a boundary without calling it a defect: `int_player_season_position__metrics` computes
  the same per-90 formulas independently for the benchmark engine, outside the drift guard's scanned
  set. The doc never claims the three canonical models are the only place a per-90 is ever computed,
  so it is out of scope for this text — recorded rather than folded in.
- Across both rounds it verified: the seed's 15 columns against the CSV header exactly; all five
  guard descriptions against what each test asserts; that steps 3 and 4 of the recipe are real CI
  gates in `validate:governance`; the `points_won` passthrough and its `_sum_season` exemption; the
  player-zero/team-missing asymmetry; that `games_expecting_team_stats` is team-side only; and the
  corrected `metrics_display.md` paragraph against the model and the yml assertion.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- ⛔ **ROUND 1: it FAILed because I edited a CPO-LOCKED document on authority no reviewer could
  check.** `metrics_display.md` is marked LOCKED, `contract.md` cited *"fix it"* as the authority,
  and `escalations.log` had no entry for any instruction on this branch. Fourth instance of that
  class in one day and the second on this branch — hours after I logged an entry saying a quote goes
  in the ledger before the sentence citing it exists.
- **ROUND 2** verified all six quotes resolve, ⭐ and did it the hard way: it re-joined the log's own
  mid-quote line wraps rather than concluding a phrase was absent because a single-line `grep` missed
  it. That is the trap that made me reflow the entry — one clause per line — after my own check
  returned a false zero.
- ⭐ **It then ruled on the substance rather than deferring it.** *"fix it"*, now logged, is adequate
  authority for THIS correction — given in direct response to a specific factual defect I had just
  reported, scope-limited by the entry itself, and touching only rationale prose. It said explicitly
  that a standing instruction to edit locked documents would NOT be adequate.
- Confirmed what the lock actually protects is byte-for-byte unchanged: block order
  Goals→Shooting→Duels→Defending→Passing→Set pieces→Goalkeeping, and row 7's label and `metric_id`.
- Confirmed the log addition is append-only past main, every diffed path is in `scope_paths`, the new
  document carries no dates, quotes or provenance, and `decisions_reserved` is untouched.

## bi-analyst-reviewer
VERDICT: PASS (round 1)
risks_checked:
- ⚠ **It ran because the COMMIT GATE caught a route I had missed** — `docs/wireframes/**` requires
  this reviewer and I had run only the other two. Recorded because the gate found it, not I.
- ⭐ **It checked the question that decides whether this is half a fix**: the old text said the
  glossary carries a >100% caveat, so if any built surface still promised that, correcting the
  rationale alone would leave the site saying something false. It swept `i18n/strings.ts`,
  `lib/format.ts` and the committed team/fixture samples — no component, sample or string asserts
  the removed behaviour, and no `finishing_efficiency_pct` value above 1 appears in the samples.
- ⭐ It found there was never a capping mechanism to describe: `format.ts`'s `percent()` multiplies
  and formats with no clamp anywhere in the file, so *"never capped"* was describing an absence.
  Removing it loses nothing operative.
- Verified the seed's own description matches the new wording essentially verbatim — open-play
  numerator, same-games denominator, `[0, 1]`, NULL on disagreement — so the wireframe and the SSoT
  now agree rather than one restating the other loosely.
- Confirmed "serves NULL" is display-accurate: `percent()` returns the dash for a non-numeric value,
  which is the repo's null-rendering rule, so a reader is told what a visitor actually sees.
- Confirmed row 7's label, `metric_id`, tier and the block order are outside the diff.
- ⚠ Noted without failing: `metrics_display.md:298`'s GAP-11 register still lists the ">100%
  finishing caveat" as a past scope item. Historical bookkeeping, not a live promise, and outside
  what *"fix it"* authorised. Left alone deliberately.

## escalations
- **`2026-09-08 — docs/incomplete-data-rule-in-the-metric-doc — RESTRUCTURE THE DOC; FIX THE LOCKED
  CAVEAT`** — every instruction verbatim, with an explicit paragraph on what *"fix it"* does and does
  not authorise: the factual paragraph inside the locked section, NOT the funnel or row order, and
  not a general licence to edit locked documents.

## ⛔ WHAT THIS BRANCH SHOULD BE REMEMBERED FOR

**1. The document was wrong in eight places and nobody had noticed**, because nobody re-reads a doc
they think they know. It named 2 of 3 canonical models, listed the seed's columns twice with the two
lists disagreeing, denied two features that had shipped, and named 1 of 5 guards.

**2. I wrote the fix from memory and broke it again in the same paragraph.** Round 1's fix corrected
the table; the sentence I then wrote under it sent an engineer to the wrong model for every ratio and
per-90. Correcting a claim and then writing an adjacent claim without opening the file is the same
failure wearing a different hat.

**3. Placement is not importance.** I opened the document with the rule I had just been arguing
about. An independent review — briefed not to treat any section as recent or protected — put the
router table first, because of four questions a reader arrives with, the rule answers one.

**4. Four unlogged-quote failures in one day, two on this branch.** The rule is not the problem; the
habit is. A quote goes in the ledger before the sentence that cites it exists, and a quote that wraps
mid-line is unfindable — one clause per line.
