# Review — chore/backfill-pd-sa-l1 — 2026-06-20

> Backfill PD/SA/L1 to 2016-2025 finished (BL1/PL parity): docs/competition_registry.yml
> history_seasons PD 2->10, SA 2->11, L1 2->11 (+ provenance notes). Routing for
> competition_registry.yml = data-engineer-reviewer; scope-auditor always. Both PASS, blinded.
> No FAIL, no ESCALATE. The actual ingest is env-var driven (PD measured first); only the three
> registry values are committed here.

diff_sha256: bfd494f15e24f4fa918eab5bb7efdcb5d4a78248b8fd7fce98a2c8ea1740c1e3

## scope-auditor
VERDICT: PASS
risks_checked:
- Depth target is not a unilateral §10 decision: 10 finished seasons is content_architecture §8
  (top-domestic); targeting 2016-2025 for PD/SA/L1 is consistent execution of the CPO's PL parity
  precedent (#520), and the ~34k spend is covered by the CPO's "continue with backfill" + the
  measure-PD-first cadence. Differing hs (PD=10 vs SA/L1=11) is documented (the #521 phantom-season
  offset), not arbitrary. Phase 2 correctly reserved.
- Phantom-current-season coupling + cost groundedness: SA/L1 hs=11 assumes the API resolves their
  current to 2026 (verified via RAW max season this session); the ~12k/league estimate rests on
  measured detail-row counts (760/760/617, details don't pre-exist). Both are mitigated by the
  contract's gates — PD measured FIRST (LOG_QUOTA) before the broader SA+L1 spend, and post-run
  verification (0 NULL fixture_id / 0 stale-id / fanout 100%) before relying on the data.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Band math (post-#520 authoritative): lo = resolved_current - (history_seasons - 1). SA/L1
  (resolved_current=2026, hs=11) -> lo=2016, hi=2026; PD (2025, hs=10) -> lo=2016, hi=2025. All
  reach 2016 as intended; no global clamp intervenes.
- Nightly run + invariants unchanged: the economy/default profile still truncates to the last
  MAX_SEASONS (=3) regardless of hs=11, so no daily cost increase; the wider window only applies on
  full-profile backfill runs. #514 carry-forward unaffected; history_seasons is not a dbt var
  (check_registry_var_sync stays green, sync_dbt_vars not required); no provider_league_id change.
- PD runtime-flip risk: if the API's current flag advances to 2026 before the PD run, hs=10 yields
  lo=2017 (missing 2016) — explicitly RESERVED as an empirical post-run adjust, not an uncovered gap.
- NOTED (non-blocking): SA/L1 `current_season` field reads "2025" while the notes say provider=2026.
  The field is fallback-only (API `current:true` wins, step 1); it cannot cause a wrong live band,
  but if the API ever dropped the current flag the fallback would resolve 2025 -> lo=2015 (one extra
  season). Same pattern as the merged PL entry; root cause tracked by #521.

## escalations
(none)
