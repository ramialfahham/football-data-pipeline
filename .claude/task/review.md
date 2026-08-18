# Review — fix/gaps-register-vs-reduced-home-design — 2026-08-18

diff_sha256: d975aab8d8dff37ee3909fa545ab544d3abc22fc240dc313a023d9c1b0012d70

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Confirmed both delta-touched files (`docs/wireframes/99_gaps_register.md`, `.claude/active_work.md`) are inside contract.md's scope_paths; no other file in the branch changed.
- Verified GAP-28's new claim against the actual seed: `dbt_project/seeds/competition_registry.csv` header is `league_code,competition_type,parent_competition,confederation,slug,sort_order,tier,season_type` and the BL1 row is `BL1,domestic_league,,UEFA,bundesliga,30,1,split_year` — matches the register's quoted text byte-for-byte, so the "half false premise" correction is factually accurate, not an invented finding.
- Checked whether narrowing GAP-28's remaining scope to "one authored pool field" and marking it "partly built" is a §10 decision: it does not cancel or alter the CPO's 2026-08-08 design approval (pool grouping is still required and still unbuilt), it only records that the tier/season_type projection sub-part already exists in the warehouse — a factual build-state correction, not a re-scoping call requiring new CPO authority.
- Round 1: verified voiding GAP-24/25/26 is derivative of the CPO's own 2026-08-10 reduction rather than a fresh design call — each void names the specific metrics that entry asked for and each is absent from the reduced four-board set; `.claude/active_work.md`'s "FOUR boards of ONE metric, top 7" note is pre-existing, not manufactured for this task.
- Round 1: withdrawal convention matches the existing GAP-04 precedent (strikethrough + bold status + reason + "returns if ever designed" caveat); no new mechanism invented. GAP-30/GAP-31 marked "NOT YET RULED" rather than approved, so no CPO approval is smuggled in.
- Checked `decisions_reserved` (issue-filing, pass-accuracy re-file, periodic-reconciliation mechanism) — none referenced or altered; no reconciliation mechanism was added to the register, only a prose note in the handover.
- Secrets sweep: markdown prose only, no credential-shaped strings.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round-1 finding closure: grepped the whole repo for the old false premise ("carries only league_code, competition_type, parent_competition" / "only three columns") — zero hits outside the patch itself; GAP-28's Gap/Disposition/Ruling cells, `.claude/active_work.md` and `docs/wireframes/10_home.md` all now state the corrected 8-column fact consistently, no residue anywhere.
- Verified the new factual claims independently rather than trusting the row: read `competition_registry.csv` header + BL1 row (byte-identical to what GAP-28 quotes) and `scripts/sync_dbt_vars.py`'s `SEED_COLUMNS` tuple (same 8 names, same order). Cross-checked `dbt_project/seeds/schema.yml` tier/season_type column docs and tests, confirming the projection is genuinely shipped in the dbt-declared schema, not present in the raw CSV by coincidence.
- Checked whether "only the authored pool field remains" understates other unbuilt work: grepped `dbt_project/models` and `scripts/export_site_data.py` for "pool" — no league-pool grouping exists downstream, and the register correctly scopes the pooled-rank computation to GAP-31 and the team-side mart to GAP-29, so GAP-28's remaining scope is not understated.
- Round 1 — VOID correctness: read `mart_leaderboards.sql`'s `count_boards`/`rate_boards` against each struck entry; confirmed every metric/column/board GAP-24/25/26 asked for (`duels_total`, `dribbles_attempts`, `tackles_total`, `goals_against`, `passes_accurate`, `shots_on_goal_against`, the goals-conceded board) is absent from the reduced player design and from any surviving four-board need — VOID correct for all three.
- Round 1 — survivors: `grep` on `mart_leaderboards.sql` shows no `team_sk` anywhere in the select list (GAP-27 live); all four Top-teams metrics present in `int_team_season__metrics_cumulative.sql` at lines 94/112/131/157 and no other leaderboard-named mart under `5_marts` (GAP-29 live).
- Round 1 — new entries: `count_boards` contains `goals`/`passes_total`/`passes_key` but not `assists`, while `assists` is a selected column (GAP-30 correct); `dense_rank() over (partition by league_code, season_api_year ...)` confirmed at lines 117-118 and the "Ranked across pooled leagues" string is real page copy in both generators, so the per-league-vs-pooled distinction is genuine and separate from GAP-28's membership question (GAP-31 correct).
- Table integrity: 7 columns on every edited row, 31 unique GAP ids, no duplicates, GAP-28's Type correctly narrowed `mart + seed` → `seed`.

## escalations
(none)
