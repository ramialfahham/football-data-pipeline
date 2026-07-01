# Review — docs/391-gap20-shipped-status — 2026-07-01

> G3 Lock artifact. #391 GAP-20 close-out: doc-status reconciliation of the already-merged #619
> (mart_roster wired into the team payload as per-season squad[]). Marks GAP-20 shipped
> (99_gaps_register.md), flips the Squad/roster block ⚠orphan→✓ + updates §7 + bumps the §3 legend
> queried-mart count 14→15 (content_architecture.md), and refreshes the handover (active_work.md,
> track A fully green; next = CPO pick). Bookkeeping/status → skip plan mode (CPO 2026-06-30 carve-out).
> Required set (routing): scope-auditor (always) + bi-analyst-reviewer (docs/wireframes/**).
>
> Round 1 (hash 240b0b2) — scope-auditor PASS; bi-analyst FAIL: the §3 legend PROSE was left stale
> ("the 3 spec'd screens (fixture/team/player)" + Squad named as the orphan example) — self-contradicting
> the roster row flip in the same PR.
> Round 2 (hash 7f45b42, THIS lock) — legend prose fixed: "the spec'd screens (fixture/team/player/Squad)
> are green"; orphan example → "(Stats-percentile / Career)"; reconciliation date → 2026-07-01, post-#619.
> Both reviewers PASS.

diff_sha256: 7f45b42b20c2f1bf578129bb324d5128ab3c8355e35c4c48ca69d648c3d913e2

## scope-auditor
VERDICT: PASS
risks_checked:
- Prose legend consistency (Appendix A6) — the round-1 stale prose (claimed 3 green screens while listing
  Squad as an orphan example, contradicting the table) is fixed: prose now lists fixture/team/player/Squad
  as green and the orphan example as Stats-percentile/Career, matching the table's Squad ⚠→✓ flip. Factually
  correct (#617 spec'd Squad; #619 wired it). No stale claim pushed forward.
- Queried-mart count accuracy — the 14→15 bump is tied to mart_roster now being queried by fetch_team_payloads
  (#619, merged on main @ ac261da); prior count was understating. All changes within scope_paths
  (99_gaps_register.md, content_architecture.md, active_work.md, .claude/task/**); no code/model change; no
  §10 decision (records merged facts only; next track reserved to the CPO). Held.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Cross-file date/PR consistency — content_architecture.md (post-#619), 99_gaps_register.md (shipped
  2026-07-01, #619), and active_work.md (main @ ac261da, #619 merged) all cite #619 / 2026-07-01
  consistently; no drift. The GAP-20 "shipped" note matches the export code exactly (id+name only/no slug,
  byte-stable player_sk order, null-identity omitted, raw position, no stats). Held.
- No silent third orphan / leftover stale Squad language — grepped all Squad/roster occurrences in
  content_architecture.md (lines 63, 82, 107, 164, 203): only benchmarks (Stats-percentile) + career remain
  ⚠ in §3/§7 (correctly untouched); no "orphan" language still attached to Squad; the 14→15 count is the only
  numeric change and is arithmetically consistent. Held.

## escalations
(none) — doc-status reconciliation of merged work; records GAP-20 shipped + roster wired, and RESERVES the
next track (Stats-percentile / Career / Phase C / Phase D), the fold-generalization question, and the
wireframe §10 doc-status sweep — all to the CPO.
