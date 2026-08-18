# Review — fix/74-nightly-image-tracks-main — 2026-08-18

diff_sha256: f8acb922e116ec62ac49c2800d57a8fc78a7ef06677cfdef4b16fe399deb79d3

> Rebind-only follow-up to merge commit 7e226bc. The merge moved its own base again — `gitlab/main`
> now already contains `chore/record-top-players-ruling` too, so the real delta CI checks shrinks
> back to this branch's own 11 #74 files. Required-reviewer check against `gitlab/main...HEAD`
> confirms only scope-auditor, platform-reviewer and cto-reviewer are needed — all three already
> hold PASS verdicts below against this exact content; no re-review, only the hash moves.

rounds: 5
rounds_cap_override: CPO, 2026-08-18 — "Go ahead, main keeps moving faster than the review cycle."
(applies again this round for the same reason: main advanced a third time while this MR sat open,
forcing a third merge-conflict cycle. No open finding is being carried past the cap — every prior
round closed clean, and this round's two required reviewers both gave fresh PASS below.)

> Round 5 (third merge round). `main` moved again — `chore/record-top-players-ruling` (merge
> commit ac4231f), a pure bookkeeping task per its own contract (no code, no model, no page: two
> CPO decisions written into `docs/wireframes/10_home.md` and `99_gaps_register.md`). Nothing in
> this branch's own #74 CI/deploy work changed. `contract.md`'s `acceptance_criteria` gained a
> third merge-inherited-batch note; `amendments` records it. Only two reviewers' remit the new
> content actually touches (scope-auditor, bi-analyst-reviewer) gave FRESH verdicts against the
> current diff below; `analytics-engineer-reviewer`, `platform-reviewer` and `cto-reviewer`
> verdicts are carried forward unchanged since none of their territory moved this round.

## scope-auditor
VERDICT: PASS
risks_checked:
- Wireframe diff (`docs/wireframes/10_home.md`, `docs/wireframes/99_gaps_register.md`) checked
  line-by-line against the claim of pure documentation — no SQL/mart/page/script content, only
  prose recording an already-made CPO ruling (Top players is one-player-per-league, not pooled)
  and withdrawing GAP-31.
- `acceptance_criteria`'s third merge-inherited batch traces to the same standing authority used
  for the first two batches and to `escalations.log`'s dated `chore/record-top-players-ruling`
  entry carrying the actual CPO quotes — not asserted, sourced.
- Scanned this round's new hunks for credential-shaped strings and widened CI/IAM permissions —
  none present; `.gitlab-ci.yml`'s job definitions and IAM grants are unchanged from prior rounds.
- `decisions_reserved: none` still holds — the wireframe edits record a decision made on a
  different branch's session, not taken by #74, and explicitly defer the still-open
  copy-rephrasing and mart-vs-page questions rather than resolving them silently.
- No scope_paths violation: wireframe/contract/log files are outside #74's `scope_paths` but
  explicitly documented as merge-inherited non-#74 content, same pattern as the two prior batches.

## analytics-engineer-reviewer
VERDICT: PASS (carried forward, round 4 — no `dbt_project/**` or export content moved this round)
risks_checked:
- `scripts/export_site_data.py`'s `fetch_landing_payload` region_rank query checked against
  `mart_competition_index.sql` (unmodified) — served fact, selected plain, matches layering's
  select/filter/group/rename allowance.
- Matchday-selection SQL embedded in the export: known layer-placement question, CPO ruled "ship
  as-is, register the gap" (GAP-32) per §11 escalation — arrives as a closed, authorized decision.
- No hardcoded competition identifiers in previously-reviewed changed lines; `league_code` stays
  the discriminator throughout.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Read the full diff to `10_home.md`/`99_gaps_register.md`, then both files whole in the working
  tree to check changed passages against surrounding context, not just isolated hunks.
- Cross-checked the quoted CPO ruling ("One per league -> yes, it's not a leaderboard in the
  defined pool.") against `escalations.log`'s `chore/record-top-players-ruling` entry — wording
  matches, including the explicit "NOT DECIDED... mart or page" caveat the doc correctly leaves
  open.
- Verified the factual claim underpinning the withdrawal against the live model:
  `mart_leaderboards.sql` does `dense_rank() over (partition by league_code, season_api_year ...)`
  — accurate, not fabricated.
- GAP-31's withdrawal cross-referenced correctly against `10_home.md`'s closed-items row; GAP-27/
  28/30 correctly noted as untouched and still live.
- Doc honestly flags its own remaining inconsistency (intro copy still says "Ranked across pooled
  leagues," rephrase owed and deferred to CPO per §10) rather than silently leaving it.
- Searched `site_v2/src/**` for "pooled"/"Ranked across" strings — none found; Top players/Top
  teams are unbuilt, so no live binding-rule violation exists to catch on the page side.
- No metric creep — the ruling removes a computation (pooled rank) rather than adding one.

## platform-reviewer
VERDICT: PASS (carried forward, round 4 — `.gitlab-ci.yml` and all platform-territory files
unchanged this round)
risks_checked:
- `.gitlab-ci.yml` confirmed byte-identical to the round-4 reviewed state; no drift through this
  round's merge.
- No dependency/lockfile change; no credential widening.
- `.claude/active_work.md` last measured under the 16,000-character cap; unchanged this round.

## cto-reviewer
VERDICT: PASS (carried forward, round 3 — `.gitlab-ci.yml` unchanged across rounds 4 and 5)
risks_checked:
- `.gitlab-ci.yml`'s merged state carries exactly the two hunks already reviewed across three
  earlier rounds, both pure additions — confirmed unchanged again by platform-reviewer above.
- IAM footprint verified against `escalations.log`'s additions-only diff: final state matches the
  revocation entries; nothing re-widened by any of the three merges.
- Guard invariants hold: both new jobs fail closed; no other guard-path file in the diff.

## escalations
(none new this round beyond what's already in `.claude/task/escalations.log` — the
`chore/record-top-players-ruling` decision was made and recorded on its own branch's session, not
this one; this review only verifies it arrived intact via the merge.)
