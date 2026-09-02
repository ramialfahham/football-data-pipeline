# Review — feat/leaderboards-assists-board-and-club — 2026-09-02

diff_sha256: 6d206d9e2e25c4365fb060aee251a2a5afc34d7f3d35dc4d9a10683592279559

rounds: 5

rounds_cap_override: CPO, verbatim — "round 4, fix all three", then "round 5". TWO overrides, both
  appended to `escalations.log` as dated entries. Round 3 FAILed on three stale statements in
  `docs/wireframes/10_home.md` that this MR falsifies and no disclaimer covers; round 4 — the round
  convened to close that class out — FAILed on a FOURTH, *"…need six pieces of warehouse work, none
  of it built"*. I stopped at the cap each time and brought the findings rather than fixing them
  unauthorised. ⭐ The fourth survived because **the phrase straddles a line break** (`none of
  it\nbuilt`), so no line-based grep can see it — a trap `CLAUDE.md` already records. Four sweeps
  failed four different ways (string-not-claim · reviewer-pointed-only · case-sensitive ·
  line-based); the whitespace-collapsed, case-insensitive, claim-based sweep that finally worked
  returned 38 hits, 1 genuine.

## scope-auditor
VERDICT: PASS
risks_checked:
- The GAP-30 status flip ("NOT YET RULED" → "SHIPPED") checked against the escalations.log entry
  that produced it AND against the prior 2026-08-18 entry that had left GAP-30 explicitly open —
  found a real, direct CPO ruling in this session closing it, not a self-granted authority. Called
  out explicitly as "a legitimate closure, not the builder marking its own homework."
- ⭐ `team_logo_url` beyond GAP-27's literal "name and slug" disposition checked against repo
  precedent rather than only the cited issue: **GAP-22 / `mart_player_career` already carries
  `team_logo_url` alongside `team_name`/`team_sk` on a player-grain mart, shipped 2026-07-02** —
  predating the #41 citation used to justify it here, so it applies an established convention
  rather than inventing scope. (Noted it could not read #41's body from its sandbox and sought
  corroboration instead of taking the quote on trust.)
- `protected_override` bans checked line-by-line against the diff — export untouched
  (`scripts/export_site_data.py` absent), the `dense_rank()` partition clause untouched,
  `board_rank <= 10` unreferenced, and `assists_player` an existing catalogue metric with no
  definition authored into the YAML. None violated.
- `decisions_reserved` items (export wiring, GAP-28, GAP-29) checked against the diff — untouched.
- New `shared.yml` descriptions checked against §2's two bans (no downstream consumer, no history —
  no dates, rulings or issue numbers) and the `{{ doc(...) }}` targets resolved to real blocks in
  `shared_columns.md`. The "one docs block, do not restate" quote verified verbatim against §2.
- Swept the diff for credential-shaped strings or widened permissions — none.
- ROUND 5 (PASS, the final verdict): verified BOTH round-cap overrides ("round 4, fix all three"
  and "round 5") are present verbatim in `escalations.log` and match the contract's citations — no
  unverifiable authority this round, unlike round 2's FAIL. Confirmed the round-4 defect is fixed
  and replaced with a two-sided correction naming what shipped against what remains. ⭐ Ran its own
  **whitespace-aware read of the full file rather than a line grep**, given the documented
  line-break trap — no unstruck false claim of non-existence remains outside the two deliberately
  left `LIVE` cells under the disclaimer. Cross-checked those against `99_gaps_register.md`'s
  GAP-27/GAP-30 rows, both correctly SHIPPED. Confirmed `export_site_data.py:45`'s stale comment is
  explicitly OWNED in `decisions_reserved` rather than unowned drift, and that all four
  `protected_override` bans hold.
- ROUND 4 (PASS, superseded): verified all three round-3 findings are fixed with accurate
  content; verified `rounds_cap_override:` is present in `review.md` AND matches the "round 4, fix
  all three" ruling appended verbatim to `escalations.log`, satisfying the commit gate. Ran its OWN
  claim-based (not string-based) sweep across `docs/wireframes/*.md` and `metric_columns.md` for
  absence-phrased staleness — every remaining hit is about a different mart (`mart_player_career`,
  `dim_player`) or an unrelated gap (GAP-16). Checked all four "correctly not counted" exclusions
  individually, including confirming that GAP-14 and GAP-16 use the same present-tense-Gap-cell
  convention claimed for GAP-27/GAP-30. `export_site_data.py` untouched; every changed file in
  `scope_paths`.
- ROUND 3 (FAIL, superseded): found two stale statements in `10_home.md` — "`assists_player` is not
  a ranked board at all" and "it is not selected into `mart_leaderboards`" — in a section no
  disclaimer reaches, correctly distinguishing it from the gap list that IS disclaimed. Verifying
  them surfaced a third (the section heading "None of it is built"). All three fixed under a CPO
  round-cap override.
- ROUND 2 (FAIL, superseded): the contract cited a CPO ruling ("fix it here") that was **not in
  `escalations.log`** — grepped for it and found nothing, ruling that a scope widening on an
  unverifiable authority is unauthorised whatever the prose claims. Also held the `layering.md` edit
  had gone past the stale number into the "Composes" clause. Both accepted: the ruling was appended,
  and the edit reduced to the number alone on the discriminator "fix what THIS CHANGE falsifies,
  leave what was already incomplete."

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Board-count consistency across all three places it is stated (SQL header, model description,
  `metric_key` description) — all agree on 15, no stale "14" survives. `count_boards` (10) +
  `rate_boards` (5) match the 15-entry `accepted_values` list exactly, order included.
- ⭐ Fan-out traced to source rather than taken on trust: `dim_team.team_sk` back through
  `base_apif__teams_global.sql`, which dedupes with `qualify row_number() over (partition by
  team_api_id) = 1`, and `dim_team` adds no aggregation — independently confirmed by the existing
  `not_null, unique` test on `dim_team.team_sk` in `core.yml`. No fan-out possible; the
  `(player_sk, season_sk, metric_key)` grain test is unaffected.
- ⭐ What `team_sk` MEANS upstream, read from the derivation rather than the description:
  `array_agg(team_sk ignore nulls order by last_kickoff_at desc)[safe_offset(0)]` over
  `int_player_club_season__metrics`, whose `finished` CTE filters `status_short in
  ('FT','AET','PEN')`. The new column description matches exactly, including the null case.
  ⚠ For a mid-season transfer the row's counting stats sum across BOTH clubs while `team_sk` names
  only the last — pre-existing upstream behaviour, not introduced here, and the description does
  not overclaim beyond "the club he belonged to".
- ⭐ The new `relationships` test's null semantics: confirmed no `test_relationships` macro
  override exists in this project, so it runs dbt-core's default, which excludes `from_field is
  null` rows. A null `team_sk` PASSES rather than fails — matching the documented intent that a
  null club is an allowed state.
- Description hygiene §2 on every added description: business meaning, source and null-meaning
  present; no downstream-consumer claim, no date, ruling or issue number. `team_sk`/`team_slug`
  reuse the real `{{ doc(...) }}` blocks in `shared_columns.md`; `team_name`/`team_logo_url` follow
  the same inline pattern already used at 9 other `team_logo_url` sites in `shared.yml`.
- Catalogue governance: `assists_player` is a pre-existing catalogue row, not newly authored; only
  board-key membership changed, no metric definition written into YAML.
- Competition-agnostic: no league or competition literal introduced in the new CTE or join.
- Layer placement: the `dim_team` lookup is a plain identity join, consistent with `layering.md`
  §5_marts denormalisation; no business logic invented, no core definition re-forked.
- Impact-map honesty verified independently: `mart_leaderboards` is only MENTIONED in comments by
  `mart_player_profile.sql` and `int_player_season__metrics.sql` (no `ref()`); `site_v2/src` has
  zero data-consuming references; `export_site_data.py` reads it into an unrendered target, exactly
  as `protected_override` states.
- FINDING (round 1, non-blocking, now FIXED): `layering.md:332`'s mart inventory read "9 count
  boards", stale at 10. Raised with the CPO, who ruled "fix it here"; `layering.md` was added to
  `scope_paths` and corrected, and the class was swept — the second stale statement
  (`export_site_data.py:45`) is deliberately left to the reserved export-wiring step that owns it.
- FINDING (round 2, non-blocking, PARTLY fixed): two further stale claims in `10_home.md` that the
  builder's own sweep had missed. The schema sentence ("`mart_leaderboards` carries no team column,
  verified against the live schema") is falsified by this MR and was fixed; the GAP-27/GAP-30
  `LIVE` lines were left, on this reviewer's own reasoning that the paragraph above them defers to
  the register as authority — and the register is corrected in this MR.
- ROUND 5 (PASS, the final verdict): confirmed BOTH "none of it built" instances are replaced with
  two-sided statements naming GAP-30/GAP-27 shipped and GAP-28/GAP-29 still unbuilt — no
  implication the section is complete. ⭐ Ran its own **whitespace-collapsed, case-insensitive,
  MULTILINE** sweep across `docs/wireframes/` plus every other doc mentioning leaderboards
  (`content_architecture.md`, `site_architecture.md`, `metrics_display.md`, `00_overview.md`,
  `09_chrome.md`, `ui_design_brief.md`, `audits/2026-06_alignment_audit.md`): every remaining hit
  sits inside struck text, a VOID bullet, a superseded paragraph, or the register's present-tense
  Gap cell — **no live unstruck claim that the assists board or club columns do not exist.**
  Confirmed the `layering.md` edit is the number alone, and that the §10 disclaimer sits directly
  above the two left-in-place `LIVE` bullets with no intervening text, unlike the round-3/4
  sentences which sat outside any disclaimer's scope. Re-read the model and yml hunks from the full
  patch rather than from memory.
- ROUND 4 (FAIL, superseded): found the fourth stale statement — "…need six pieces of warehouse
  work, none of it built" — in the round convened to close that class out. It survived three prior
  sweeps because the phrase straddles a line break (`none of it\nbuilt`), which no line-based grep
  can match, including the reviewer's own quoted string.
- ROUND 3 (narrow re-confirmation, PASS): model and yml hunks still unchanged. The REDUCED
  `layering.md` line verified true against the actual `count_boards` list (10 entries) and judged
  "not worse — same incompleteness, number now correct", since the line never claimed the
  "Composes" clause was exhaustive. The `10_home.md` fix verified against
  `int_player_season__metrics.sql`'s `array_agg(team_sk ignore nulls order by last_kickoff_at
  desc)` — the club is resolved UPSTREAM, so the mart does an identity join only and the claim of
  "no export derivation" holds. Re-swept the tree: `export_site_data.py:45` remains the only stale
  statement, out of `scope_paths`, `protected_override`-banned, and recorded in
  `decisions_reserved` rather than silently orphaned.
- ROUND 2 (PASS, superseded): verified the then-fuller `layering.md` line, confirmed
  `_LEADERBOARD_METRICS` is still exactly 9 entries so the export deferral is accurately
  characterised, and swept `content_architecture.md`, `site_architecture.md`,
  `mart_player_profile.sql`, `int_player_season__metrics.sql` and `tests/test_export_site_data.py`
  for stale board-count claims — none found.

## escalations
(none — GAP-30 was put to the CPO as a decision and he returned it as already-decided: *"So what's
the question. The player block has assists in the mockup."* Recorded in `escalations.log`; no
question is open.)
