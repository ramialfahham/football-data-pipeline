# Review — docs/391-squad-screen-spec — 2026-07-01

> G3 Lock artifact. #391 track A: a DOC-ONLY wireframe spec for the Team → Squad screen (new file
> 11_team_squad.md) bound to mart_roster's identity-only columns, with the export-wiring gap registered
> (GAP-20) and the stale 02/00 notes reconciled. Required set (routing): scope-auditor (always) +
> bi-analyst-reviewer (docs/wireframes/**). No code path — export wiring is a separate follow-up PR.
>
> Round 1 (hash 599289d7): bi-analyst FAIL — (1) §4/§5 invented a "flag" nationality rendering that
> has no name→flag mapping (screen 03 renders plain text); (2) the inventory "PR" cell used an
> undefined "A". scope-auditor PASS.
> Round 2 (hash ef1b6838): fixed both — nationality → plain text (matching 03) + a disclaimer; "A" →
> "#391 ⁑" with a footnote legend. scope-auditor PASS. bi-analyst FAIL — two residual "flag" refs
> survived (§4 desktop note + §6 "No age" row), and §6 lacked the unresolved-player-entity state
> (mart LEFT-joins dim_player).
> Round 3 (hash ecf12b17): purged the residual flags → "nationality"; added a §6 "Unresolved player"
> row (all-null identity → member omitted, guarded by the player_sk→dim_player relationships DQ test).
> BOTH reviewers PASS.
> Round 4 (hash 4bcc72da, THIS lock): REBASE-REBIND only — sibling PR #616 (handover refresh) merged
> first, so the branch was rebased onto the new main. #616 touched only .claude/active_work.md +
> .claude/task/* (NOT docs/wireframes/**), so the wireframe diff is byte-identical to round 3; the hash
> shifted solely because contract.md's diff-base moved (#615 contract → #616 contract). active_work.md
> is main's #616 version (not clobbered). Both reviewers re-confirmed PASS on the rebased diff.

diff_sha256: 4bcc72da3b7e7af7c673e0a3befe5950f1e08a382557dbb4573b8db650cd4dee

## scope-auditor
VERDICT: PASS
risks_checked:
- DQ guard on unresolved player entities — §6 "Unresolved player" row documents the mart's LEFT-join
  contract (dim_player LEFT-joined, unresolved memberships surface as a relationships test failure, not
  a silent drop; mart_roster.sql header lines 15–16 + the shared.yml relationships test). The render
  correctly omits all-NULL-identity members, guarded upstream — honest error transparency, not silent
  omission. Held.
- Position grouping deferred to a build-time data check — the contract reserves the taxonomy
  (GK/DEF/MID/ATT vs flat); the wireframe shows it as a PROPOSED example with a catch-all "Other" group
  for unmapped positions, and defers the final decision to the build/wiring PR against the real
  player_position domain. No CPO-reserved decision silently taken. Scope is exactly
  docs/wireframes/** + .claude/task/**; no code/model/export/catalogue change; export wiring deferred to
  GAP-20. Held.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding-rule full sweep — all six §5 bindings (player_position, player_name, player_nationality,
  player_birth_date, player_photo_url, player_sk) trace 1:1 to real mart_roster columns (verified against
  the mart SQL). Zero metric_catalogue metric referenced (identity-only; position-group headers are new
  i18n copy, not metric labels); catalogue untouched. Held.
- Round-1/2 fixes complete + export-honesty — grepped "flag": the only remaining occurrence is the §5
  binding note that explicitly documents no name→flag mapping exists; §4 desktop note + §6 "No age" now
  say "nationality"; the new §6 unresolved-player row matches the mart's LEFT-join behavior verbatim.
  Grepped scripts/export_site_data.py for squad/mart_roster → zero hits, confirming the "not yet
  exported, keys proposed-pending GAP-20" framing is factual. GAP-20 mirrors the GAP-15 precedent; the
  02/00 edits (Squad link, inventory row, census) are accurate and don't overclaim wired/live. Held.

## escalations
(none) — doc-only wireframe spec; records the CPO's two rulings (identity-only scope; new dedicated
file) and RESERVES (does not decide) the export payload shape/attachment (GAP-20, follow-up PR) and the
position-grouping taxonomy (build-time data check) — both to the CPO / the wiring PR.
