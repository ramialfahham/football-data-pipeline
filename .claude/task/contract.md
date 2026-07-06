# Task contract — handover refresh (session-boundary batch, post-#653)

> Written on a CLEAN tree (branch chore/handover-refresh-post-653 off main @ c4489aa).
> Bookkeeping only — batched session-boundary refresh ([[feedback-handover-discipline]] cadence:
> refresh ONCE at the boundary, not per-merge). Plan mode skipped per the CPO handover carve-out;
> still runs the contract + review + gate.

objective: >
  Bring `.claude/active_work.md` current from post-#651 (pointer 28d751f) to post-#653 (c4489aa). Net of this
  session: #653 (#484 — player momentum now consumes the shared int_team_momentum_window so the top-players strip
  and team form share ONE window; tournament-cumulative on tournament fixtures; new parity DQ test) MERGED, and
  issue #484 CLOSED (its literal scope — momentum tournament parity — is done). Record the national-team window
  audit that followed: the window SET is closed/decided (§4 matrix + §8.4); the national FORM panel is fully built
  (team + player), and the two buildable leftovers are now filed as issues with CPO rulings — #654 (NT context
  block on the profile, presence-gated) and #655 (season-record "campaign is the season" — a phantom gap; each
  qualifying campaign already carries ONE season_api_year, so it's a stale-note cleanup). #3 career-NT-by-type
  stays parked on NT-history ingest. NEXT returns to an OPEN CPO pick.

refs: #653 (c4489aa, #484 momentum parity); #484 CLOSED; #654 (NT profile context); #655 (campaign=season note cleanup).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  Doc/bookkeeping only. Single substantive file is `.claude/active_work.md`. No dbt_project/** model, no
  scripts/export_*.py, no ingestion/**, no site*/ change — no data/number/metric move, no build impact. The task
  scaffolding (.claude/task/**) is artifact-only; contract.md is artifact_only_never so this commit is NOT
  review-exempt (scope-auditor required).

decisions_taken: >
  Record-only. #653 merged + #484 closed already happened this session. #654/#655 already filed with their CPO
  rulings recorded IN the issues (campaign=season; NT-profile-context presence-gated). No new roadmap invented;
  no §10 decided here — the rulings were the CPO's this session.

decisions_reserved:
  - The actual next task — CPO picks later (candidates: #655 quick doc green; #654 needs a wireframe first;
    the #545–#547 programs; task_f876b853 chip). NT career-by-type (#3) parked on a data/cost call.

done_when:
  - active_work.md header + FIRST STEPS point at c4489aa; #653 recorded as the latest merged PR.
  - main-carries appends #653; a #653 entry is prepended to RECENT PRs.
  - #484 recorded DONE+CLOSED; the national-window audit + #654/#655 (with rulings) captured; #3 noted parked.
  - NEXT is an OPEN CPO pick again (no locked task).
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
