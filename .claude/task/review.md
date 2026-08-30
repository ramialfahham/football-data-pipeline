# Review — refactor/metric-rename-player-defending — 2026-08-30

> **STEP 4 of the metric catalogue naming programme, MR 3 of seven.** The five player `defending`
> metrics: `tackles_total` → `tackles_player`, `tackles_interceptions` → `interceptions_player`,
> `tackles_blocks` → `blocks_player`, `defensive_actions` → `defensive_actions_player` (plus its
> four derived yoy forms), `dribbles_past` → `dribbles_past_player`. PLAYER entity only.
> Branched from main `a3fb952`.

diff_sha256: c9a85ca8b61170ec14585b4a1e5fdef210ea7e290bb9f159dd301e03dc16f9dd

rounds: 3

⛔⛔ **ROUNDS 1 AND 2 BOTH FAILED 4–1, ON DIFFERENT THINGS, AND BOTH FAULTS WERE MINE.** Round 3 is
the cap and all five reviewers PASS with no open findings.

**Round 1 — `bi-analyst-reviewer` FAILed** on `docs/wireframes/03_player_profile.md:127-128`: two
field names renamed inside prose documenting the MATCH LOG expanded row, whose payload comes from
`mart_player_match_log` — a provider surface the "yes" ruling keeps unrenamed. The wireframe was
left naming two fields that exist nowhere in the export. **Cause: a line-scoped test on a construct
that spans lines.** The provider-prose guard keys on the mark "may show the full per-match line" but
tested it against the token's own line; `!125` got the same block right *by luck* because its token
sat on the mark's line, while here the list wraps. The mark now governs its whole paragraph.
⚠ The contract also had **no entry for that section at all**, so the rename shipped with no
judgement recorded — which is why the reviewer could fairly read it as reversing `!127`'s precedent
for the same file. Both surfaces are now recorded.

**Round 2 — `scope-auditor` FAILed** on `impact_map.downstream`: the `dbt ls` lineage was described
but its output not pasted. **The honest correction is larger than the finding:** the field claimed
the command was "run on this branch BEFORE the first edit" and **it had not been run for this MR at
all** — the sentence came across from `!127`'s contract when I reused it as a template. I asserted a
step I had skipped. The real output is 13 models, not the 10 the previous batch held.

⭐⭐ **THE TWO FAILURES SHARE ONE CAUSE: carrying something forward without re-deriving it** — a
guard that worked by luck in `!125`, and a claim that was true in `!127`. **What a template carries
safely is STRUCTURE; every sentence in it that asserts a fact about THIS branch has to be re-earned.**
After round 2 I audited the rest of the contract for the same defect rather than fixing the
instance: `deploy_order`'s "no touched model is incremental" was re-derived and held.

⚠ **ONE FINDING DELIBERATELY NOT FIXED, and both reviewers whose remit it touches ruled on it.**
`football-analytics-expert-reviewer` raised that `03_player_profile.md` now shows the same underlying
stat as `tackles_player` (season bundle) and `tackles_total` (match log). `bi-analyst-reviewer`
judged it at round 3: no built page renders both labels together (the player match-log surface is
not built yet), and the divergence is the direct consequence of the standing "yes" ruling that has
applied identically since `shots_total` vs `shots_player` — architecture, not a defect this MR
introduced. Recorded in `escalations.log`, not folded into the diff.

## scope-auditor
VERDICT: PASS
risks_checked:
- `impact_map.downstream`'s pasted 13-model `dbt ls` list checked against the real `ref()` graph
  across `dbt_project/models/**` — matches exactly, including the three over-count models
  (`int_player_competition_benchmarks`, `mart_player_competition_benchmarks`, `mart_player_career`),
  confirmed by grep to carry none of the five renamed tokens. The paste is real and complete.
- The round-2 correction is recorded as an admitted false claim — "it was not run for MR 3 at
  all… I asserted a step I had skipped" — not softened into a formatting complaint; wording matches
  verbatim between `contract.md` and `escalations.log`.
- Audited `deploy_order`'s re-derived "no touched model is incremental" claim by spot-checking
  `config(materialized=...)` in touched models — consistent with the claim.
- `scope_paths` reconciled against `review_input.patch`: every changed file is on the list, nothing
  extra either way.
- `escalations.log` diff is a pure append — hunk `@@ -6520,3 +6520,160 @@`, no prior line altered.
- Swept the whole diff for credential-shaped strings — none; all edits are metric renames, doc
  blocks and prose.
- Threshold declarations checked against the diff: the resolver is absent from `scope_paths` and the
  patch (stays a scratchpad tool as claimed); no new file, library, hook or cadence change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Confirmed the cumulative diff's file set is unchanged from what was already reviewed (only
  `contract.md` + `escalations.log` differ) — no model/yml/seed/script slipped in between rounds.
- Verified **by direct file read, not grep**, that `int_player_competition_benchmarks`,
  `mart_player_competition_benchmarks` and `mart_player_career` carry none of the five renamed names
  — the contract's over-count claim holds. The benchmark chain touches only the unchanged `_per90`
  columns via the `player_benchmark_metrics()` macro.
- `int_legs__team_from_players.sql` is untouched and still aggregates the old provider names into
  unrenamed TEAM output columns (`tackles` / `blocks` / `interceptions`) — no reference-following
  violation at the junction.
- Traced all four self-aliasing `sum(X) … as X` sites: only `int_player_season__metrics` moves its
  inner read; the other three keep the provider-sourced read and rename only the outer alias.
- `int_player_profile__yoy`'s `defensive_actions_player` composition correctly reads the renamed
  output columns of `int_player_season_record`.
- Seed formulas for the five renames still point at unrenamed provider columns and relations.
- Both protected 18-name PLAYER `accepted_values` lists still contain `defensive_actions_per90`
  untouched; the one leaderboard list that changes did so correctly.
- The round-1 wireframe fix still matches `mart_player_match_log`'s actual unrenamed columns.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Re-read all nine `player`/`defending` seed rows directly: the five renamed and the four unrenamed
  `_per90` rows are exactly as verified in earlier rounds — `base_relation=int_legs__player_match`
  throughout, every `numerator_expr` still reading the provider's own unrenamed columns, and no
  formula, floor or direction changed. No seed or model change slipped in.
- `dribbles_past_player` is correctly the only `lower_is_better=true` row in the group; the other
  four are `higher_better`, correct for ball-winning actions.
- Judged the `tackles_` prefix drop on football grounds rather than by approval alone: an
  interception reads a pass and a block stops a shot, neither is a challenge for the ball, so
  removing the "kind-of-tackle" implication is an accuracy improvement.
- `defensive_actions_per90` staying un-suffixed beside `defensive_actions_player` is RULING 5's
  documented exception, not an inconsistency.
- Manually checked every `sum(old) as new` write site across the five intermediate models for a
  stem-swap defect (e.g. blocks landing on `interceptions_player`) — none found.
- The pasted 13-model lineage does not contradict the catalogue's own `base_relation` view.
- On the two-names-one-stat documentation gap: content to leave it filed rather than fixed —
  a documentation-clarity question, not a metric-validity defect, and forcing it into a mechanical
  rename MR would be scope creep the working agreement warns against.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-derived the 13-model lineage **independently**, walking the `ref()` graph one hop at a time
  from each of the six seeds; the set closes at exactly the 13 named models, none extra, none
  missing.
- Checked the correction's wording in **all three places it appears** (`contract.md`,
  `escalations.log`, `acceptance_evidence.md`) — all state the larger, honest claim rather than the
  smaller "forgot to paste output". The framing is not softened anywhere it recurs.
- Verified `deploy_order`'s "no touched model is incremental" independently against all ten changed
  `.sql` files' own `config()` blocks: eight `table`, two `view`, none incremental.
- Confirmed no regression between rounds 2 and 3 from the patch's own diffstat — the delta touches
  four `.claude/**` files and zero model/script/seed files.
- Vacuous-gate hunt: `check_ui_i18n_metrics.py` is already disclosed as non-discriminating and not
  buried; `tests/` contains none of the ten old/new tokens, consistent with `pytest` being listed as
  a baseline-match regression check rather than claimed rename evidence. No further undisclosed
  vacuous gate found.
- `export_site_data.py`'s literal-tuple renames are mechanical substitution only; the pre-existing
  "pinned by no test" gap is carried forward and disclosed, not newly introduced.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Confirmed from the patch's own diffstat that nothing in `docs/wireframes/**`, `site_v2/src/**` or
  any dbt model changed between rounds 2 and 3 — the round-1 fix and everything else in this
  territory is untouched.
- Re-read `03_player_profile.md` directly: line 97 (season-stats bundle) and line 106 (unbundled
  atomic) correctly renamed, sourced from marts that rename; lines 127-128 (match-log expanded row,
  from `mart_player_match_log`) correctly unrenamed. The round-1 defect is fixed and the fix holds.
- Traced field bindings against `scripts/export_site_data.py`: the four renamed names appear in
  `_LEADERBOARD_METRICS` / `_LB_KEEP` consistent with the renamed mart columns; `dribbles_past_player`
  flows through `shape_top_players`'s pass-through, matching the wireframe's own "carried in payload,
  unrendered" framing. No fabricated field.
- `defensive_actions_per_match` (the protected TEAM token) verified untouched across all five
  frontend files and the committed samples, matching the empty `site_v2/` diff and 12 rows / 7
  headings unchanged in all three locales.
- **Ruled on the deferred documentation call:** grepped for a built surface rendering both labels
  together and found none — the player match-log page is not built yet, so no fan sees two names for
  one number today. The divergence is the direct consequence of the standing "yes" ruling, identical
  in shape to `shots_total` vs `shots_player` in earlier batches — architecture, not an
  inconsistency this MR introduced. Leaving it recorded rather than folded in is an acceptable call,
  not a FAIL.

## escalations
(none)
