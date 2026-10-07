# Review — feature/173-match-page-readers — 2026-10-07

diff_sha256: fca48853bf4e148bc10032823d44f2fa93e7e9431109b83240c866d678d9f11f

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every code file in the diff is in scope_paths; no amendment.
- Decision rights: the three column names and the acceptance criteria rest on approvals in chat, 2026-10-07; the "not yet started" rule is the export's existing test; no wording, URL or slug format added.
- Thresholds: no new mechanism; the recurring cost (the mart's nightly read) is declared and measured before merge.
- Impact map: evidenced lineage (mart_competition_fixtures, mart_match_days), export readers, deploy order and blast radius.
- Reserved decisions: no other #173 reader touched; Recent matches stay on mart_team_momentum_window; the Next matches drawing stays with #166.
- Consumption layer: shape_next_match passes the mart row through and drops only the page's own match; the flags are derived in dbt.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the next-match flags are computed in the mart from fct_fixture; the export only filters on them.
- Join fan-out: team_next is one row per team (qualify row_number, fixture_sk tiebreak); joins on (fixture_sk, team_sk) keep the grain fixture_sk.
- Tests: not_null and accepted_values on both flags; the singular test unions home and away flags, so a team flagged once as each is caught.
- Header re-source: the same fixture set and the same dim_team values via the mart; dim_league keyed by league_code, one-to-one through the registry.
- Competition-agnostic: no league identifier in the SQL or the export.
- Residual, not a defect: the flags are frozen at build time, which the column descriptions state.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 finding (no test over fetch_fixture_payloads) resolved: a fake-_query test pins the header read from the mart, the league lookup by league_code, the home/away flag wiring and the page's-own-match exclusion.
- Re-run safety: the export is a pure read; the mart is rebuilt whole and deterministic.
- Empty inputs: team_in is built after the empty-fixtures return, so no empty IN list reaches BigQuery.
- Guards and CI: no hook, workflow, CI or dependency change; deploy:export stays manual and web-only, and fails closed if run before the nightly builds the columns.
- Build health: one next_match object per side, about 3 to 4 MB over 4,614 files.

## escalations
(none)
