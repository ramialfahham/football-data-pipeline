# Review — chore/backfill-phase2a — 2026-06-21

> Phase 2a: §8 club/domestic depths in docs/competition_registry.yml — 7 non-top-5 domestic_league
> 2->5 (BL2,ED,LMX,LP,MLS,SPL,VL) + 8 continental_club 5->10 (UCL,UEL,UECL,LIBER,CAFCL,AFCCL,CCCU,CWC).
> Phase 2b (national-team tournaments/qualifiers) DEFERRED (CPO Option A). Routing: data-engineer +
> scope-auditor. Both PASS, blinded. No FAIL, no ESCALATE.

diff_sha256: 7fe5ef6092f8c150d0910390fa90f6e93d42a0513480e046941373973123f877

## scope-auditor
VERDICT: PASS
risks_checked:
- §8 application is mechanical, not a unilateral §10 call: the 5-season rule applies to non-top-5
  domestic_league (tier-1 ED/VL/LMX/LP/MLS/SPL + tier-2 BL2) per §8's "2nd-tier/smaller" bucket
  (its own examples include tier-1 leagues); continental_club = 10 per §8. Diff changes ONLY
  history_seasons on exactly the 15 intended leagues — no other field/league, no status/classification
  change. UESC (not in §8) left at 5; cups + APD/BSA/J1/KL1 (already 5) untouched; CWC/CCCU use their
  existing registry competition_type, not reclassified.
- Phase 2b boundary held: national-team tournaments + qualifiers are RESERVED (Option A), flowing from
  §8's own two-track design (editions/cycle need a per-cadence mapping, not a year-count) — not smuggled
  in, not decided here. No Appendix A anti-pattern.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Registry integrity + nightly behaviour: exactly 15 history_seasons lines changed (7 dom 2->5,
  8 cc 5->10), no provider_league_id/status/other field touched; valid parse; history_seasons is not
  a dbt var (var-sync green, sync_dbt_vars not needed). The economy MAX_SEASONS cap only fires on the
  economy profile; the nightly scheduler sets no INGEST_PROFILE -> runs full -> the new hs values are
  respected nightly with no cost cap interference, and INCLUDE_IN_PROGRESS=1 is already in dbt-scheduled.yml
  for the in_progress continental_club set. #514 carry-forward unaffected.
- Sparse-catalog safety: hs=10 on UECL (founded 2021/22) / CWC (old format) computes a lower bound
  earlier than the competition existed, but _seasons_for_ingestion discovers only the years the API
  returns and filters to [lo,hi] — missing years are silently skipped (no empty-row writes, no
  corruption). done_when already states ">=10 or the API's available depth"; no off-by-one in the
  inclusive band formula.

## escalations
(none)
